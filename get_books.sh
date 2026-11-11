#!/bin/bash
set -euo pipefail

# Get arguments
bucket=$1
book_dir=$2

# Create directory for books
mkdir -p "$book_dir"

# Copy text files from S3
aws s3 cp "s3://$bucket" "$book_dir" \
    --recursive --exclude "*" --include "*.txt"

# Create book list with header
echo "File path" > book_list.txt

# Add sorted absolute paths
find "$(realpath "$book_dir")" -type f -name "*.txt" | sort >> book_list.txt

# Print number of books
count=$(($(wc -l < book_list.txt) - 1))
echo "Wrote $count book files to book_list.txt"
