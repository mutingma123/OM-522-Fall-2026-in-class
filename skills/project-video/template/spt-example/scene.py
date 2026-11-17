"""Shortest processing time first (SPT) on four jobs, in three parts.

    Part1Jobs       the four jobs and what flow time means
    Part2Arrival    the schedule in arrival order and its average flow time
    Part3Spt        the SPT schedule beside it, with the same last finish and a lower average

Every number on screen comes from scheduling.py, the method this video explains, and is
checked against a hand calculation below. Render it from the folder above this one:

    pixi run render spt-example check
    pixi run render spt-example preview
"""

from manim import LEFT, RIGHT, UP, FadeIn, GrowFromEdge, Rectangle, VGroup

from scheduling import JOBS, arrival_order, average_flow_time, finish_times, spt_order
from video_helpers import BLUE, FAINT, INK, MUTED, VideoScene, label, make_box

PARTS = ["Part1Jobs", "Part2Arrival", "Part3Spt"]

# ---------------------------------------------------------------------------
# Computation layer. Every number the scenes show is computed here from the method code
# and checked against a hand calculation. Nothing here depends on how the scenes draw it.
# ---------------------------------------------------------------------------

ARRIVAL = arrival_order(JOBS)
SPT = spt_order(JOBS)
ARRIVAL_DONE = finish_times(ARRIVAL, JOBS)
SPT_DONE = finish_times(SPT, JOBS)
ARRIVAL_AVG = average_flow_time(ARRIVAL, JOBS)
SPT_AVG = average_flow_time(SPT, JOBS)
LAST = max(ARRIVAL_DONE.values())

# By hand: arrival order runs A, B, C, D and finishes at 6, 8, 16, and 19, so the average
# is 49 / 4 = 12.25. SPT runs B, D, A, C and finishes at 2, 5, 11, and 19, so the average
# is 37 / 4 = 9.25. Both finish the last job at minute 19.
assert ARRIVAL == ["A", "B", "C", "D"] and list(ARRIVAL_DONE.values()) == [6, 8, 16, 19]
assert SPT == ["B", "D", "A", "C"] and list(SPT_DONE.values()) == [2, 5, 11, 19]
assert (ARRIVAL_AVG, SPT_AVG, LAST) == (12.25, 9.25, 19)
assert max(SPT_DONE.values()) == LAST


def minutes(values):
    """1, 2, and 3 as '1, 2, and 3'."""
    words = [f"{value:g}" for value in values]
    return ", ".join(words[:-1]) + ", and " + words[-1]


# ---------------------------------------------------------------------------
# Display layer. Colors, layout, captions, and timing.
# ---------------------------------------------------------------------------

UNIT = 0.55  # frame units per minute, so 19 minutes span about 10.5 units
BAR_HEIGHT = 0.7
LEFT_EDGE = -4.6


def gantt(order, done, y, color):
    """One machine's schedule as bars along a time line, with each finish minute below."""
    bars, ticks = VGroup(), VGroup()
    for job in order:
        start = done[job] - JOBS[job]
        bar = Rectangle(
            width=JOBS[job] * UNIT,
            height=BAR_HEIGHT,
            stroke_color=INK,
            stroke_width=1.5,
            fill_color=color,
            fill_opacity=1,
        )
        bar.move_to([LEFT_EDGE + (start + JOBS[job] / 2) * UNIT, y, 0])
        bar.add(label(job, size=26, color="#FFFFFF" if color == BLUE else INK).move_to(bar))
        bars.add(bar)
        ticks.add(label(f"{done[job]}", size=20, color=MUTED).move_to([LEFT_EDGE + done[job] * UNIT, y - 0.6, 0]))
    # The 0 mark appears with the first job's finish mark, so ticks keeps one entry per bar.
    ticks[0] = VGroup(label("0", size=20, color=MUTED).move_to([LEFT_EDGE, y - 0.6, 0]), ticks[0])
    assert len(ticks) == len(bars)
    return bars, ticks


def row_name(text, y):
    return label(text, size=24, color=MUTED).move_to([LEFT_EDGE - 0.3, y, 0], aligned_edge=RIGHT)


class Part1Jobs(VideoScene):
    def construct(self):
        self.title_card("Setting up the problem")
        self.say("Four jobs wait for one machine. Each box shows its processing time.")
        boxes = VGroup(*(make_box(job, [f"{JOBS[job]} min"], width=2.2) for job in JOBS)).arrange(RIGHT, buff=0.5)
        self.play(FadeIn(boxes, lag_ratio=0.2), run_time=1.2)
        self.pause("jobs")
        self.say("A job's flow time is the minute it finishes, counting from minute 0.")
        self.pause("flow time")


class Part2Arrival(VideoScene):
    def construct(self):
        self.title_card("Scheduling in arrival order")
        self.say(f"In arrival order, the jobs finish at minutes {minutes(ARRIVAL_DONE.values())}.")
        bars, ticks = gantt(ARRIVAL, ARRIVAL_DONE, y=0.6, color=FAINT)
        for bar, tick in zip(bars, ticks):
            self.play(GrowFromEdge(bar, LEFT), FadeIn(tick), run_time=0.6)
        self.pause("arrival schedule")
        self.say(f"The average flow time is {ARRIVAL_AVG:g} minutes.")
        total = " + ".join(f"{value}" for value in ARRIVAL_DONE.values())
        average = label(f"({total}) / {len(JOBS)} = {ARRIVAL_AVG:g} min", size=28).move_to([0, -1.6, 0])
        self.play(FadeIn(average, shift=0.1 * UP), run_time=0.6)
        self.pause("arrival average")


class Part3Spt(VideoScene):
    def construct(self):
        self.title_card("Scheduling the shortest job first")
        self.say("Shortest processing time first (SPT) runs the shortest job next.")
        old_bars, old_ticks = gantt(ARRIVAL, ARRIVAL_DONE, y=1.2, color=FAINT)
        old = VGroup(row_name("Arrival", 1.2), old_bars, old_ticks)
        self.play(FadeIn(old), run_time=0.6)
        self.pause("arrival again")
        self.say(f"SPT runs {', '.join(SPT)} and finishes them at minutes {minutes(SPT_DONE.values())}.")
        self.play(FadeIn(row_name("SPT", -0.8)), run_time=0.4)
        bars, ticks = gantt(SPT, SPT_DONE, y=-0.8, color=BLUE)
        for bar, tick in zip(bars, ticks):
            self.play(GrowFromEdge(bar, LEFT), FadeIn(tick), run_time=0.6)
        self.pause("spt schedule")
        self.say(f"The last job still finishes at minute {LAST}. The average falls from {ARRIVAL_AVG:g} to {SPT_AVG:g} minutes.")
        averages = VGroup(
            label(f"Arrival order: {ARRIVAL_AVG:g} min", size=26, color=MUTED),
            label(f"SPT: {SPT_AVG:g} min", size=26, color=BLUE),
        ).arrange(RIGHT, buff=1.0).move_to([0, -2.6, 0])
        self.play(FadeIn(averages, shift=0.1 * UP), run_time=0.6)
        self.pause("averages", hold=3.5)
