"""Shared pieces for every video in this folder: colors, text, boxes, and the scene class.

A video's scene.py imports from here and draws its own pieces (a Gantt chart, a route map,
a plot). render.py puts this folder on the import path.

    from video_helpers import INK, MUTED, VideoScene, label, make_box

The rules this module enforces:

- Every caption fits the frame in at most two lines, or the render stops.
- Nothing leaves the screen without a click. say() and clear_stage() add a click first
  when anything has played since the last one.
- Nothing sits outside the frame or under the caption at a click, or the render stops.
"""

import json
import os
import re
from pathlib import Path

from manim import (
    DOWN,
    UP,
    WHITE,
    Create,
    FadeIn,
    FadeOut,
    ManimColor,
    RoundedRectangle,
    Scene,
    Text,
    VGroup,
    config,
)
from manim.animation.animation import Wait, prepare_animation
from manim_slides import Slide
from manim_slides.slide.base import BaseSlide

config.background_color = WHITE

# Pango maps "Sans" to the system's default sans-serif face on Windows, macOS, and Linux.
FONT = "Sans"

# Colors. BLUE and RED stay distinguishable under common color blindness. FAINT is for
# fills and grid lines only, since text in it is hard to read.
INK = ManimColor("#1A1A1A")
MUTED = ManimColor("#5F6A72")
FAINT = ManimColor("#D9DDE0")
BLUE = ManimColor("#005C84")
RED = ManimColor("#9E1B32")
GOLD = ManimColor("#F2D653")

CAPTION_Y = 3.3
CAPTION_SIZE = 30
CAPTION_MAX_WIDTH = 12.0
# The least gap between the caption and the content below it, and between any object and
# the frame edge, in frame units. The frame is about 14.2 wide and 8 tall.
CAPTION_GAP = 0.35
FRAME_MARGIN = 0.25
# Seconds the picture holds still before each click, so the MP4 reads without a presenter.
READ = 2.2
# Every animation runs this many times slower than written, so motion is easy to talk over.
PACE = 1.25

SLIDES_DIR = Path(os.environ.get("SLIDES_DIR", "slides"))
CHECKPOINT_DIR = Path(os.environ.get("CHECKPOINT_DIR", "build/checkpoints"))


def label(text, size=24, color=INK):
    """One line of text."""
    return Text(text, font=FONT, font_size=size, color=color)


def text_block(lines, size=24, color=INK, buff=0.16):
    """Several lines of text, centered under one another."""
    return VGroup(*(label(line, size=size, color=color) for line in lines)).arrange(DOWN, buff=buff)


def make_box(title, lines=(), color=MUTED, fill=None, width=None, height=None, size=24):
    """A rounded box with a title and optional lines under it. The box grows to fit its text
    unless width or height is given."""
    content = VGroup(label(title, size=size + 4))
    if lines:
        content.add(text_block(lines, size=size, color=MUTED))
    content.arrange(DOWN, buff=0.2)
    box = RoundedRectangle(
        corner_radius=0.12,
        width=width or content.width + 0.6,
        height=height or content.height + 0.5,
        stroke_color=color,
        stroke_width=2,
        fill_color=fill or WHITE,
        fill_opacity=1,
    )
    content.move_to(box)
    return VGroup(box, content)


# A caption never breaks next to one of these, so "a = 6" stays on one line.
OPERATORS = {"=", "+", "-", "\u2212", ">", "<", "\u00d7", "/"}


def _words(text):
    """Split a caption into words, keeping a parenthesis like "(2 min)," as one word."""
    return re.findall(r"[^\s(]*\([^)]*\)\S*|\S+", text)


def make_caption(text, size=CAPTION_SIZE, max_width=CAPTION_MAX_WIDTH):
    """The caption at the top of the frame, on one line or two. A two-line caption breaks
    between sentences when both lines fit, and otherwise at the most balanced point that
    is not inside a parenthesis or next to an operator. Raises ValueError when two lines
    are not enough, so the caption must be shortened or split."""
    one = label(text, size=size)
    if one.width <= max_width:
        return one.move_to([0, CAPTION_Y, 0])
    words = _words(text)
    cuts = [k for k in range(1, len(words)) if words[k - 1] not in OPERATORS and words[k] not in OPERATORS]

    def balance(k):
        return abs(len(" ".join(words[:k])) - len(" ".join(words[k:])))

    sentence_cuts = sorted((k for k in cuts if words[k - 1].endswith((".", "?"))), key=balance)
    for cut in sentence_cuts + sorted(cuts, key=balance):
        two = text_block([" ".join(words[:cut]), " ".join(words[cut:])], size=size, buff=0.12)
        if two.width <= max_width:
            return two.move_to([0, CAPTION_Y - 0.2, 0])
    raise ValueError(f"Caption too long for two lines, shorten or split it: {text!r}")


class VideoScene(Slide):
    """One part of a video. The same code renders a continuous MP4 clip and a deck slide at
    every pause().

    Use say() for captions, pause() for clicks, clear_stage() to clear the picture, and
    title_card() to open the part. Each pause() also records a checkpoint, and render.py
    cuts a still frame at every checkpoint for review.
    """

    # The HTML deck plays every slide forward, so the reversed clips are not needed.
    skip_reversing = True

    def __init__(self, *args, **kwargs):
        # manim-slides 5.7.0 predates manim 0.22, which removed two settings that
        # manim-slides writes. This __init__ and render() below skip those lines. They can go
        # once manim-slides supports manim 0.22. -1 keeps every partial clip for manim-slides.
        config["max_files_cached"] = -1
        BaseSlide.__init__(self, *args, output_folder=SLIDES_DIR, **kwargs)

    def render(self, *args, **kwargs):
        config["max_files_cached"] = -1
        Scene.render(self, *args, **kwargs)
        if config["dry_run"]:
            return
        self._save_slides(
            use_cache=not (config["disable_caching"] or self.disable_caching),
            flush_cache=self.flush_cache,
            skip_reversing=self.skip_reversing,
        )

    def setup(self):
        self.caption = None
        self.checkpoints = []
        self.problems = []
        # What has played since the last click: a caption, and anything else.
        self.caption_since_click = False
        self.content_since_click = False
        self.helper_playing = False
        # Outlines from emphasize() that fade with the current caption.
        self.outlines = []

    def play(self, *animations, **kwargs):
        """Slow every animation by PACE, and in a check run, note a FadeOut that plays
        without a click before it."""
        prepared = [prepare_animation(animation) for animation in animations]
        if "run_time" in kwargs:
            kwargs["run_time"] = kwargs["run_time"] * PACE
        else:
            for animation in prepared:
                animation.run_time = animation.run_time * PACE
        if config["dry_run"] and not self.helper_playing and self.content_since_click:
            if any(isinstance(animation, FadeOut) for animation in prepared):
                self.problems.append(f"FadeOut without a click before it, under caption {self._caption_text()!r}")
        super().play(*prepared, **kwargs)
        if not self.helper_playing and not all(isinstance(a, Wait) for a in prepared):
            self.content_since_click = True

    def _caption_text(self):
        return getattr(self.caption, "source_text", "(no caption)")

    def _check_layout(self, name):
        """At a click, everything must sit inside the frame and below the caption."""
        half_w = config.frame_width / 2 - FRAME_MARGIN
        half_h = config.frame_height / 2 - FRAME_MARGIN
        floor = None
        if self.caption is not None and self.caption in self.mobjects:
            floor = self.caption.get_bottom()[1] - CAPTION_GAP
        for mob in self.mobjects:
            if len(mob.get_all_points()) == 0:
                continue
            if mob.get_left()[0] < -half_w or mob.get_right()[0] > half_w or mob.get_bottom()[1] < -half_h or mob.get_top()[1] > half_h:
                self.problems.append(f"{type(mob).__name__} runs past the frame edge at click {name!r}")
            if floor is not None and mob is not self.caption and mob.get_top()[1] > floor:
                self.problems.append(f"{type(mob).__name__} reaches into the caption at click {name!r}")
        if self.problems and not config["dry_run"]:
            raise AssertionError("\n".join(self.problems))

    def pause(self, name, hold=READ):
        """Hold the picture for viewers of the MP4, then end the slide (one click)."""
        self._check_layout(name)
        if hold:
            self.wait(hold)
        self.checkpoints.append({"name": name, "time": round(float(self.time) - 0.1, 3)})
        self.next_slide()
        self.caption_since_click = False
        self.content_since_click = False

    def say(self, text):
        """Show a caption. Replacing a caption waits for a click when anything has played
        since the last one."""
        new = make_caption(text)
        new.source_text = text
        if self.caption is not None and (self.caption_since_click or self.content_since_click):
            self.pause(f"before caption: {text[:30]}")
        stale = [FadeOut(outline) for outline in self.outlines if outline in self.mobjects]
        self.outlines = []
        self.helper_playing = True
        if self.caption is None:
            self.play(FadeIn(new, shift=0.15 * DOWN), *stale, run_time=0.6)
        else:
            self.play(FadeOut(self.caption, shift=0.15 * UP), FadeIn(new, shift=0.15 * UP), *stale, run_time=0.6)
        self.helper_playing = False
        self.caption = new
        self.caption_since_click = True

    def clear_stage(self):
        """Fade out everything except the caption. When only a caption has played since the
        last click, that caption's click also clears the picture."""
        others = [mob for mob in self.mobjects if mob is not self.caption]
        if not others:
            return
        if self.content_since_click:
            self.pause("before clearing the picture")
        self.helper_playing = True
        self.play(*(FadeOut(mob) for mob in others), run_time=0.6)
        self.helper_playing = False

    def emphasize(self, mob, color=INK, buff=0.08, keep=False):
        """Draw an outline around an object to point at it. The outline fades with the next
        caption, unless keep is True. Outline the shapes only, not the labels under them, or
        the outline's edge crosses the labels."""
        outline = RoundedRectangle(
            corner_radius=0.12,
            width=mob.width + 2 * buff,
            height=mob.height + 2 * buff,
            stroke_color=color,
            stroke_width=4,
            fill_opacity=0,
        ).move_to(mob)
        self.play(Create(outline), run_time=0.6)
        if not keep:
            self.outlines.append(outline)
        return outline

    def title_card(self, title):
        """Open the part with its title, which fades on its own before the first caption."""
        card = label(title, size=48)
        if card.width > config.frame_width - 1.0:
            raise ValueError(f"Title too wide for the frame, shorten it: {title!r}")
        self.helper_playing = True
        self.play(FadeIn(card, shift=0.2 * UP), run_time=0.8)
        self.checkpoints.append({"name": "title", "time": round(float(self.time), 3)})
        self.wait(1.2)
        self.play(FadeOut(card), run_time=0.5)
        self.helper_playing = False

    def tear_down(self):
        """Write the checkpoints for the stills, and any layout or click problems for check."""
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        name = type(self).__name__
        (CHECKPOINT_DIR / f"{name}.json").write_text(json.dumps(self.checkpoints, indent=2))
        problems = CHECKPOINT_DIR / f"{name}.problems.txt"
        problems.unlink(missing_ok=True)
        if self.problems:
            problems.write_text("".join(f"{name}: {line}\n" for line in self.problems))
