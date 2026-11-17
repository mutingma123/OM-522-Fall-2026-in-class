"""Shortest processing time first (SPT) for the sum of completion times on one machine.

In your project, the video imports your own method code instead of this file.
"""

from itertools import permutations

# Minutes of processing for each job, listed in the order the jobs arrived. Every job is
# ready at minute 0.
JOBS = {"A": 6, "B": 2, "C": 8, "D": 3}


def arrival_order(jobs):
    return list(jobs)


def spt_order(jobs):
    """Shortest processing time first (SPT)."""
    return sorted(jobs, key=lambda job: jobs[job])


def completion_times(order, jobs):
    """The minute each job finishes when the machine runs the jobs in this order."""
    completed, clock = {}, 0
    for job in order:
        clock += jobs[job]
        completed[job] = clock
    return completed


def total_completion(order, jobs):
    """The objective: the sum of the jobs' completion times."""
    return sum(completion_times(order, jobs).values())


def first_out_of_order(order, jobs):
    """The position of the first longer job that sits right before a shorter one, or None."""
    for position in range(len(order) - 1):
        if jobs[order[position]] > jobs[order[position + 1]]:
            return position
    return None


def swap(order, position):
    """The order with the jobs at position and position + 1 traded."""
    swapped = list(order)
    swapped[position], swapped[position + 1] = swapped[position + 1], swapped[position]
    return swapped


def swaps_to_spt(order, jobs):
    """Swap the first out-of-order pair until none is left. Returns every order along the way."""
    orders = [list(order)]
    while (position := first_out_of_order(orders[-1], jobs)) is not None:
        orders.append(swap(orders[-1], position))
    return orders


def every_order(jobs):
    """Each possible order of the jobs with its sum of completion times (brute force)."""
    return {tuple(order): total_completion(order, jobs) for order in permutations(jobs)}
