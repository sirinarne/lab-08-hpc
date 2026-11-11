
#!/usr/bin/env python3
"""Summarize one book with a language model and add the summary to MongoDB.

Usage: summarize.py BOOK_LIST TASK_ID

BOOK_LIST has the header "File path", then the path of one book file per line.
TASK_ID, counted from 1, picks the book. Each task of a Slurm job array
summarizes one book.
"""

import logging
import os
import socket
import sys
import time
from datetime import datetime, timezone

import torch
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from transformers import pipeline

logger = logging.getLogger(__name__)

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

GENRES = [
    "adventure",
    "romance",
    "horror",
    "science fiction",
    "mystery",
    "satire",
    "historical fiction",
    "children's story",
    "poetry",
    "drama"
]

# The model reads at most 32,768 tokens.
MAX_WORDS = 20000

PROMPT = (
    "{excerpt}\n\nThat was the beginning of a book. Summarize the story in three sentences. "
    "Then, on a new line, write 'Genre: ' and the genre that fits best, one of: {genres}. "
    "Write plain text, without Markdown."
)


def read_book(path):
    """Return the text of a book file, without Project Gutenberg's header and license."""

    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()

    # The book is between the START and END markers.
    start = text.find("*** START OF")
    end = text.find("*** END OF")

    begin = text.find("\n", start) + 1 if start != -1 else 0

    return text[begin:end if end != -1 else len(text)]


def summarize_book(text):
    """Return a three-sentence summary of the book and its genre."""

    # Use GPU if available, otherwise CPU.
    device = "cuda" if torch.cuda.is_available() else "cpu"

    logger.info("Running %s on %s", MODEL, device)

    generator = pipeline(
        "text-generation",
        model=MODEL,
        device=device,
        dtype=torch.bfloat16
    )

    # Use the beginning of the book.
    excerpt = " ".join(text.split()[:MAX_WORDS])

    prompt = PROMPT.format(
        excerpt=excerpt,
        genres=", ".join(GENRES)
    )

    # Generate the summary and genre.
    result = generator(
        [{"role": "user", "content": prompt}],
        max_new_tokens=256,
        do_sample=False
    )

    answer = result[0]["generated_text"][-1]["content"]

    # Separate the summary and genre.
    summary, separator, genre = answer.rpartition("Genre:")

    if not separator:
        return answer.strip(), "unknown"

    summary = summary.strip()
    genre = genre.strip().lower()

    return summary, genre if genre in GENRES else "unknown"


def upload_summary(key, summary, genre, job):
    """Add the summary and genre to the document in gutenberg.books."""

    client = MongoClient(
        os.environ["MONGODB_ATLAS_URL"],
        username=os.environ["MONGODB_ATLAS_USER"],
        password=os.environ["MONGODB_ATLAS_PWD"]
    )

    now = datetime.now(timezone.utc)

    try:
        db = client["gutenberg"]
        collection = db["books"]

        result = collection.update_one(
            {"_id": key},
            {
                "$set": {
                    "llm_analysis": {
                        "summary": summary,
                        "genre": genre,
                        "model": MODEL,
                        "at": now
                    }
                },
                "$push": {
                    "runs": {
                        "host": socket.gethostname(),
                        "at": now,
                        "job": job
                    }
                }
            }
        )

        if result.matched_count == 0:
            logger.warning("No document found for %s", key)

    except PyMongoError as e:
        logger.error("MongoDB error for %s: %s", key, e)
        raise

    finally:
        client.close()


def main():
    """Summarize book number TASK_ID of BOOK_LIST and save the result in MongoDB."""

    # Set up logging.
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s"
    )

    # Check command-line arguments.
    if len(sys.argv) != 3:
        logger.error("Usage: summarize.py BOOK_LIST TASK_ID")
        sys.exit(1)

    book_list = sys.argv[1]

    try:
        task_id = int(sys.argv[2])
    except ValueError:
        logger.error("TASK_ID must be an integer")
        sys.exit(1)

    # Read book list, skipping the header.
    with open(book_list, "r") as f:
        books = [
            line.strip()
            for line in f.readlines()[1:]
            if line.strip()
        ]

    # Check that the task number is valid.
    if task_id < 1 or task_id > len(books):
        logger.error(
            "TASK_ID must be between 1 and %d",
            len(books)
        )
        sys.exit(1)

    # Select the book for this task.
    book_path = books[task_id - 1]
    key = os.path.basename(book_path)

    logger.info("Task %d: %s", task_id, book_path)

    # Read and summarize the book.
    start = time.time()

    text = read_book(book_path)
    summary, genre = summarize_book(text)

    elapsed = time.time() - start

    logger.info("%s: %s, %.1f s", key, genre, elapsed)

    # Get Slurm job information.
    job_id = os.environ.get("SLURM_ARRAY_JOB_ID")
    array_id = os.environ.get("SLURM_ARRAY_TASK_ID")

    job = f"{job_id}_{array_id}" if job_id and array_id else None

    # Save summary and genre to MongoDB.
    upload_summary(key, summary, genre, job)

    # Print completion message.
    print(
        f"Summarized {key} in "
        f"{time.time() - start:.1f} s "
        f"on {socket.gethostname()}"
    )


if __name__ == "__main__":
    main()

