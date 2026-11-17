"""A small scheduling method. In your project, the video imports your own method code instead."""

# Minutes of processing for each job, listed in the order the jobs arrived. Every job is
# ready at minute 0.
JOBS = {"A": 6, "B": 2, "C": 8, "D": 3}


def arrival_order(jobs):
    return list(jobs)


def spt_order(jobs):
    """Shortest processing time first (SPT)."""
    return sorted(jobs, key=lambda job: jobs[job])


def finish_times(order, jobs):
    """The minute each job finishes when the machine runs the jobs in this order."""
    finished, clock = {}, 0
    for job in order:
        clock += jobs[job]
        finished[job] = clock
    return finished


def average_flow_time(order, jobs):
    """Every job is ready at minute 0, so a job's flow time is its finish time."""
    finished = finish_times(order, jobs)
    return sum(finished.values()) / len(finished)
