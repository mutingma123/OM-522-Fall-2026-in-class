"""Why shortest processing time first (SPT) minimizes the sum of completion times, in six parts.

    Part1Setup       the four jobs, completion time, the goal, and arrival order's sum
    Part2Spt         the SPT schedule and its smaller sum, and the question it raises
    Part3OneSwap     one swap of an out-of-order pair, worked with the jobs' numbers
    Part4Proof       the same swap in general: the sum falls by a - b
    Part5AllSwaps    swaps until no pair is out of order, which ends at SPT
    Part6CheckAll    a brute-force check of every order

Every number on screen comes from scheduling.py, the method this video explains, and is
checked against a hand calculation below. Render it from the folder above this one:

    pixi run render spt-example check
    pixi run render spt-example preview
"""

from manim import LEFT, RIGHT, UP, WHITE, Dot, FadeIn, FadeOut, GrowFromEdge, Line, Rectangle, VGroup

from scheduling import (
    JOBS,
    arrival_order,
    completion_times,
    every_order,
    spt_order,
    swaps_to_spt,
    total_completion,
)
from video_helpers import BLUE, FAINT, INK, MUTED, RED, VideoScene, label, make_box

PARTS = ["Part1Setup", "Part2Spt", "Part3OneSwap", "Part4Proof", "Part5AllSwaps", "Part6CheckAll"]

# ---------------------------------------------------------------------------
# Computation layer. Every number the scenes show is computed here from the method code
# and checked against a hand calculation. Nothing here depends on how the scenes draw it.
# ---------------------------------------------------------------------------

ARRIVAL = arrival_order(JOBS)
SPT = spt_order(JOBS)
ARRIVAL_DONE = completion_times(ARRIVAL, JOBS)
SPT_DONE = completion_times(SPT, JOBS)
ARRIVAL_SUM = total_completion(ARRIVAL, JOBS)
SPT_SUM = total_completion(SPT, JOBS)

# By hand: arrival order runs A, B, C, D and completes them at 6, 8, 16, and 19 (sum 49).
# SPT runs B, D, A, C and completes them at 2, 5, 11, and 19 (sum 37).
assert ARRIVAL == ["A", "B", "C", "D"] and list(ARRIVAL_DONE.values()) == [6, 8, 16, 19]
assert SPT == ["B", "D", "A", "C"] and list(SPT_DONE.values()) == [2, 5, 11, 19]
assert (ARRIVAL_SUM, SPT_SUM) == (49, 37)

# Swapping the first out-of-order pair until none is left: A and B, then C and D, then A
# and D. By hand the sums are 49, 45, 40, and 37, and each drop equals the longer job's
# time minus the shorter one's (6 - 2, 8 - 3, and 6 - 3).
CHAIN = swaps_to_spt(ARRIVAL, JOBS)
SUMS = [total_completion(order, JOBS) for order in CHAIN]
PAIRS = []  # the swapped pair, longer job first, for each step
for before, after in zip(CHAIN, CHAIN[1:]):
    moved = [job for job, other in zip(before, after) if job != other]
    PAIRS.append(tuple(moved))
DROPS = [JOBS[first] - JOBS[second] for first, second in PAIRS]
assert CHAIN[-1] == SPT and SUMS == [49, 45, 40, 37]
assert PAIRS == [("A", "B"), ("C", "D"), ("A", "D")] and DROPS == [4, 5, 3]
assert DROPS == [high - low for high, low in zip(SUMS, SUMS[1:])]

# The first swap, which Part 3 works and Part 4 generalizes: t = 0, a = 6, b = 2.
FIRST, SECOND = PAIRS[0]
SWAPPED = CHAIN[1]
SWAPPED_DONE = completion_times(SWAPPED, JOBS)
PAIR_BEFORE = ARRIVAL_DONE[FIRST] + ARRIVAL_DONE[SECOND]
PAIR_AFTER = SWAPPED_DONE[FIRST] + SWAPPED_DONE[SECOND]
PAIR_END = JOBS[FIRST] + JOBS[SECOND]
assert (PAIR_BEFORE, PAIR_AFTER, PAIR_END) == (14, 10, 8)
assert all(ARRIVAL_DONE[job] == SWAPPED_DONE[job] for job in ("C", "D"))

# Brute force: all 24 orders. The smallest sum is 37, and only SPT reaches it. The largest
# is 58, from longest first (C, A, D, B completes at 8, 14, 17, and 19).
ALL = every_order(JOBS)
LOWEST, HIGHEST = min(ALL.values()), max(ALL.values())
assert len(ALL) == 24 and (LOWEST, HIGHEST) == (37, 58)
assert [order for order, total in ALL.items() if total == LOWEST] == [tuple(SPT)]


def minutes(values):
    """1, 2, and 3 as '1, 2, and 3'."""
    words = [f"{value}" for value in values]
    return ", ".join(words[:-1]) + ", and " + words[-1]


# ---------------------------------------------------------------------------
# Display layer. Colors, layout, captions, and timing.
# ---------------------------------------------------------------------------

UNIT = 0.5  # frame units per minute, so 19 minutes span 9.5 units
LEFT_EDGE = -4.75  # where minute 0 sits


def x_at(minute):
    return LEFT_EDGE + minute * UNIT


def job_bar(job, start, y, color, height=0.6):
    """One job's bar on the time line, with its letter inside."""
    bar = Rectangle(
        width=JOBS[job] * UNIT,
        height=height,
        stroke_color=INK,
        stroke_width=1.5,
        fill_color=color,
        fill_opacity=1,
    )
    bar.move_to([x_at(start + JOBS[job] / 2), y, 0])
    bar.add(label(job, size=24, color=WHITE if color == BLUE else INK).move_to(bar))
    return bar


def tick(minute, y, size=18, below=0.58):
    return label(f"{minute}", size=size, color=MUTED).move_to([x_at(minute), y - below, 0])


def schedule(order, y, color, height=0.6, size=18, below=0.58):
    """One machine's schedule: a bar per job, its completion minute under the bar's end, and
    a 0 under the start. Returns the bars and ticks keyed by job, and the 0."""
    done = completion_times(order, JOBS)
    bars = {job: job_bar(job, done[job] - JOBS[job], y, color, height) for job in order}
    ticks = {job: tick(done[job], y, size, below) for job in order}
    return bars, ticks, tick(0, y, size, below)


def row_name(text, y, size=22):
    return label(text, size=size, color=MUTED).move_to([LEFT_EDGE - 0.25, y, 0], aligned_edge=RIGHT)


def row_sum(text, y, size=22, color=INK):
    return label(text, size=size, color=color).move_to([x_at(19) + 0.45, y, 0], aligned_edge=LEFT)


def draw_schedule(scene, bars, ticks, zero, order):
    """Grow the bars one job at a time, each with its completion minute."""
    scene.play(FadeIn(zero), run_time=0.3)
    for job in order:
        scene.play(GrowFromEdge(bars[job], LEFT), FadeIn(ticks[job]), run_time=0.5)


class Part1Setup(VideoScene):
    def construct(self):
        self.title_card("Setting up the problem")
        self.say("Four jobs wait for one machine. Each box shows its processing time.")
        boxes = VGroup(*(make_box(job, [f"{JOBS[job]} min"], width=2.2) for job in JOBS)).arrange(RIGHT, buff=0.5)
        self.play(FadeIn(boxes, lag_ratio=0.2), run_time=1.2)
        self.pause("jobs")
        self.say(f"A job's completion time is the minute it finishes. In arrival order, they are {minutes(ARRIVAL_DONE.values())}.")
        self.clear_stage()
        bars, ticks, zero = schedule(ARRIVAL, y=0.6, color=FAINT)
        draw_schedule(self, bars, ticks, zero, ARRIVAL)
        self.pause("arrival schedule")
        self.say(f"The goal is the smallest sum of completion times. In arrival order, it is {ARRIVAL_SUM}.")
        total = " + ".join(f"{value}" for value in ARRIVAL_DONE.values())
        self.play(FadeIn(label(f"{total} = {ARRIVAL_SUM}", size=30).move_to([0, -1.4, 0]), shift=0.1 * UP), run_time=0.6)
        self.pause("arrival sum")


class Part2Spt(VideoScene):
    def construct(self):
        self.title_card("Scheduling the shortest job first")
        self.say("Shortest processing time first (SPT) runs the shortest waiting job next.")
        bars, ticks, zero = schedule(ARRIVAL, y=1.0, color=FAINT)
        arrival = VGroup(row_name("Arrival", 1.0), *bars.values(), *ticks.values(), zero, row_sum(f"Sum {ARRIVAL_SUM}", 1.0))
        self.play(FadeIn(arrival), run_time=0.6)
        self.pause("arrival again")
        self.say(f"SPT runs {', '.join(SPT)}. They complete at {minutes(SPT_DONE.values())}, a sum of {SPT_SUM}.")
        self.play(FadeIn(row_name("SPT", -0.8)), run_time=0.3)
        bars, ticks, zero = schedule(SPT, y=-0.8, color=BLUE)
        draw_schedule(self, bars, ticks, zero, SPT)
        self.play(FadeIn(row_sum(f"Sum {SPT_SUM}", -0.8, color=BLUE)), run_time=0.4)
        self.pause("spt schedule")
        self.say(f"Is {SPT_SUM} the smallest sum that any order of these jobs can reach?")
        self.pause("question", hold=3.5)


class Part3OneSwap(VideoScene):
    def construct(self):
        self.title_card("Swapping one out-of-order pair")
        self.say("Two neighbors are out of order when the longer job runs first.")
        bars, ticks, zero = schedule(ARRIVAL, y=0.4, color=FAINT)
        total = row_sum(f"Sum {ARRIVAL_SUM}", 0.4)
        self.play(FadeIn(VGroup(*bars.values(), *ticks.values(), zero, total)), run_time=0.6)
        self.pause("arrival")
        self.say(f"{FIRST} ({JOBS[FIRST]} min) runs right before {SECOND} ({JOBS[SECOND]} min), so this pair is out of order.")
        self.emphasize(VGroup(bars[FIRST], bars[SECOND]))
        self.pause("pair")
        self.say(f"Swap {FIRST} and {SECOND}.")
        new_ticks = {job: tick(SWAPPED_DONE[job], 0.4) for job in (FIRST, SECOND)}
        self.play(FadeOut(ticks[FIRST]), FadeOut(ticks[SECOND]), run_time=0.3)
        self.play(
            bars[SECOND].animate.move_to([x_at(JOBS[SECOND] / 2), 0.4, 0]),
            bars[FIRST].animate.move_to([x_at(JOBS[SECOND] + JOBS[FIRST] / 2), 0.4, 0]),
            run_time=1.2,
        )
        self.play(FadeIn(new_ticks[FIRST]), FadeIn(new_ticks[SECOND]), run_time=0.4)
        self.pause("swapped")
        self.say(f"The pair still fills minutes 0 to {PAIR_END}, so C and D complete at {ARRIVAL_DONE['C']} and {ARRIVAL_DONE['D']} as before.")
        self.emphasize(VGroup(bars["C"], bars["D"]))
        self.pause("later jobs")
        self.say(
            f"{FIRST} and {SECOND} completed at {ARRIVAL_DONE[FIRST]} and {ARRIVAL_DONE[SECOND]}, a total of {PAIR_BEFORE}. "
            f"Now {SECOND} and {FIRST} complete at {SWAPPED_DONE[SECOND]} and {SWAPPED_DONE[FIRST]}, a total of {PAIR_AFTER}."
        )
        self.pause("pair totals")
        self.say(f"The sum falls by {DROPS[0]}, from {SUMS[0]} to {SUMS[1]}. That is {JOBS[FIRST]} − {JOBS[SECOND]}, the difference of their times.")
        self.play(FadeOut(total), FadeIn(row_sum(f"Sum {SUMS[1]}", 0.4, color=BLUE)), run_time=0.6)
        self.pause("new sum", hold=3.5)


class Part4Proof(VideoScene):
    def construct(self):
        self.title_card("Proving the swap always helps")
        y = 1.1

        def block(text, width, left, color):
            box = Rectangle(width=width, height=0.7, stroke_color=INK, stroke_width=1.5, fill_color=color, fill_opacity=1)
            box.move_to([left + width / 2, y, 0])
            box.add(label(text, size=24, color=WHITE if color == BLUE else INK).move_to(box))
            return box

        earlier = block("Earlier jobs", 3.4, -5.4, FAINT)
        first = block("a", 2.4, -2.0, BLUE)
        second = block("b", 1.2, 0.4, BLUE)
        later = block("Later jobs", 3.4, 1.6, FAINT)
        t_mark = label("t", size=24, color=MUTED).move_to([-2.0, y - 0.65, 0])
        end_mark = label("t + a + b", size=24, color=MUTED).move_to([1.6, y - 0.65, 0])

        self.say("Take any order with an out-of-order pair. The jobs before the pair end at minute t.")
        self.play(FadeIn(earlier), FadeIn(later), FadeIn(t_mark), run_time=0.6)
        self.pause("strip")
        self.say("The pair's first job takes a minutes and its second takes b, with a > b.")
        self.play(FadeIn(first), FadeIn(second), FadeIn(end_mark), run_time=0.6)
        self.pause("pair")
        self.say("Before the swap, the pair completes at t + a and t + a + b.")
        before = label("Before:  (t + a) + (t + a + b)  =  2t + 2a + b", size=28).move_to([0, -0.6, 0])
        self.play(FadeIn(before, shift=0.1 * UP), run_time=0.6)
        self.pause("before")
        self.say("After the swap, it completes at t + b and t + b + a.")
        self.play(
            second.animate.move_to([-2.0 + 0.6, y, 0]),
            first.animate.move_to([-2.0 + 1.2 + 1.2, y, 0]),
            run_time=1.0,
        )
        after = label("After:  (t + b) + (t + b + a)  =  2t + 2b + a", size=28).move_to([0, -1.4, 0])
        self.play(FadeIn(after, shift=0.1 * UP), run_time=0.6)
        self.pause("after")
        self.say("The later jobs start at t + a + b either way. Their completion times do not change.")
        self.emphasize(later)
        self.pause("later")
        self.say("The sum falls by a − b, which is more than 0 whenever a > b.")
        self.play(FadeIn(label("Before − After  =  a − b  >  0", size=28, color=BLUE).move_to([0, -2.2, 0]), shift=0.1 * UP), run_time=0.6)
        self.pause("drop")
        self.say(f"In the swap of {FIRST} and {SECOND}, t = 0, a = {JOBS[FIRST]}, and b = {JOBS[SECOND]}. The sum fell by {JOBS[FIRST]} − {JOBS[SECOND]} = {DROPS[0]}.")
        self.pause("example", hold=3.5)


class Part5AllSwaps(VideoScene):
    def construct(self):
        self.title_card("Swapping until no pair is out of order")
        rows_y = [1.7, 0.55, -0.6, -1.75]
        names = ["Arrival"] + [f"Swap {first}, {second}" for first, second in PAIRS]
        sums = [f"{SUMS[0]}"] + [f"{total} (−{drop})" for total, drop in zip(SUMS[1:], DROPS)]

        def row(k):
            color = BLUE if k == len(CHAIN) - 1 else FAINT
            bars, ticks, zero = schedule(CHAIN[k], rows_y[k], color, height=0.5, size=16, below=0.46)
            return VGroup(*bars.values()), VGroup(*ticks.values(), zero, row_name(names[k], rows_y[k]), row_sum(sums[k], rows_y[k]))

        self.say("Swap the first out-of-order pair, and repeat until none is left.")
        bars, side = row(0)
        self.play(FadeIn(bars), FadeIn(side), run_time=0.6)
        self.pause("start")
        for k, ((first, second), drop) in enumerate(zip(PAIRS, DROPS), start=1):
            self.say(f"Swapping {first} ({JOBS[first]} min) and {second} ({JOBS[second]} min) lowers the sum by {drop}, to {SUMS[k]}.")
            bars, side = row(k)
            self.play(FadeIn(bars, shift=0.1 * UP), FadeIn(side), run_time=0.8)
            self.pause(f"swap {k}")
        self.say("No pair is out of order now. This order is SPT.")
        self.emphasize(bars, buff=0.05)
        self.pause("spt")
        self.say("From any order, these swaps reach SPT and only lower the sum. No order has a smaller sum than SPT.")
        self.pause("conclusion", hold=3.5)


class Part6CheckAll(VideoScene):
    def construct(self):
        self.title_card("Checking every order")
        axis_y = -0.8
        low, high = 35, 60

        def x_of(total):
            return -5.5 + (total - low) * 11.0 / (high - low)

        axis = VGroup(Line([x_of(low), axis_y, 0], [x_of(high), axis_y, 0], color=INK, stroke_width=2))
        for value in range(low, high + 1, 5):
            axis.add(Line([x_of(value), axis_y - 0.1, 0], [x_of(value), axis_y + 0.1, 0], color=INK, stroke_width=2))
            axis.add(label(f"{value}", size=20, color=MUTED).move_to([x_of(value), axis_y - 0.4, 0]))
        axis.add(label("Sum of completion times (minutes)", size=22, color=MUTED).move_to([0, axis_y - 1.0, 0]))

        self.say(f"every_order() in scheduling.py tries all {len(ALL)} orders of these four jobs.")
        self.play(FadeIn(axis), run_time=0.6)
        self.pause("axis")

        # SPT and arrival order go on top of their stacks, so their labels clear the other dots.
        marked = (tuple(SPT), tuple(ARRIVAL))
        dots, stacked = {}, {}
        for order, total in sorted(ALL.items(), key=lambda item: (item[1], item[0] in marked)):
            level = stacked.get(total, 0)
            stacked[total] = level + 1
            dots[order] = Dot([x_of(total), axis_y + 0.3 + 0.28 * level, 0], radius=0.11, color=MUTED)
        self.say(f"Each dot is one order's sum of completion times. The sums run from {LOWEST} to {HIGHEST}.")
        self.play(FadeIn(VGroup(*dots.values()), lag_ratio=0.05), run_time=1.5)
        self.pause("dots")

        self.say(f"Only SPT reaches the smallest sum, {LOWEST}. Arrival order sits at {ARRIVAL_SUM}.")
        spt_dot, arrival_dot = dots[tuple(SPT)], dots[tuple(ARRIVAL)]
        label_y = axis_y + 0.3 + 0.28 * max(stacked.values()) + 0.25
        self.play(
            spt_dot.animate.set_color(BLUE).scale(1.3),
            arrival_dot.animate.set_color(RED).scale(1.3),
            FadeIn(label("SPT", size=22, color=BLUE).move_to([spt_dot.get_x(), label_y, 0])),
            FadeIn(label("Arrival", size=22, color=RED).move_to([arrival_dot.get_x(), label_y, 0])),
            run_time=0.8,
        )
        self.pause("spt dot")
        self.say("The proof covers every instance. This check confirms that the code agrees with it here.")
        self.pause("closing", hold=3.5)
