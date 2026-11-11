 # Lab 08: Knowledge check

**Answer each question below it, in your own words, in one to three sentences.** Replace the `...` below **Your answer:** with your text. Questions 1 and 3 also ask for saved output, which goes into the directory `results/`.

## 1. Slurm: what jobs have I submitted?

**Your task:** print a history of all your Slurm job submissions *since November 4, 2026*. Format the output to include the job ID, job name, node list, partition, account, user, state, start time, and elapsed time. See the job accounting fields in the [sacct documentation](https://slurm.schedmd.com/sacct.html). You may also ask Claude Code or another LLM for the exact command. 

Redirect the command's output to `results/job-history.txt` and include the file in your submission. Do not worry if some earlier jobs failed or were canceled. The complete history should show your process, including trial and error.

*Hint:* See [Part 1, Step 6](README.md#step-6-check-how-the-tasks-ended) in the README.

**Your answer:** Provide the entire command you used, including all CLI options.

sacct -S 2026-11-04 -X --format=JobID,JobName,NodeList,Partition,Account,User,State,Start,Elapsed > results/job-history.txt




## 2. Slurm: did every array task run at the same time?

You submitted your entire job array with one `sbatch` command, but Slurm scheduled each task separately.

**Your task:** in the job history from Question 1, find the tasks from your most recent completed array run. Compare their start times and elapsed times.

*Hint:* See [Part 1, Step 5](README.md#step-5-watch-the-job-array) in the README.

**Your answer:** Did all tasks in the array start at the same time? Was the elapsed time identical for every task? Explain why or why not.

Not all 101 of the tasks started at the same time. For example, the first task started at 18:38:54, while the last task started at 19:02:03. This shows that slurm started/scheduled the tasks in batches. Additionally, this means that some tasks started together while other had to wait for resources to become available. The elapsed times also varied, ranging from 14 to 19 seconds.  


## 3. Slurm: did my job use what it asked for?

Suppose your next job array has 1,000 books instead of 101. Before you submit it, you want to know whether your script asks for too much or too little memory and time.

**Your task:** run `seff` for **one** task of your finished job array, and save its output as `results/seff.txt`.

*Hint:* `seff` takes the ID of one task, such as `4211873_1`. Compare its **Memory Utilized** and **Job Wall-clock time** with `--mem` and `--time` in your `summarize.slurm`.

**Your answer:** How much memory and time did the task use, compared with what your script asked for? What would you change in your script, and why?

The task used less memory and CPU than allocated. It only used about 27.78% of its available CPU time(10/36 available core seconds) and 9.23% of its allocated memory (1.48 GB/16 GB). The runtime was also just 18 seconds, compared to the requested 5 minutes. In the future, I would reduce the maximum amount of memory and time limit to help avoid wasting resources.  

