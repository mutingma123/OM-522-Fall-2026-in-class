---
name: project-video
description: Builds a short silent Manim video that explains a project's method, as two outputs from one scene file, i.e., a continuous MP4 and an HTML deck that stops at each click until the presenter advances it. Plans the video with the student first, takes every number on screen from the project's own code, renders, and reviews still frames. Use when a student asks for an animated explainer, a video walkthrough, or a click-through deck of their method or results.
---

# Project video

You build a short video that explains one method or result from the student's project. The
video is silent, so captions carry the words and the animation carries the idea. One file,
`scene.py`, renders two outputs:

- a continuous MP4 that plays on its own, and
- an HTML deck that stops at every `pause()` until the presenter presses the right arrow.
  Pressing S opens a speaker view with the current slide, the next slide, and a clock.

This skill's `template/` folder has everything the video needs. It holds its own environment
(`pixi.toml`), the render script (`render.py`), the drawing helpers (`video_helpers.py`), and a
finished example (`spt-example/`). Read `template/spt-example/scene.py` before you write a
scene. It shows every rule below, and its last four parts explain why the method works and
check it on every possible order.

## Rules

1. **Plan before you draw.** Propose the plan in step 2 and stop until the student approves it.
   The student decides what the video covers.
2. **Every number on screen comes from the project's code.** Compute each number in the scene's
   computation layer, from the project's method or from a results file it wrote. Put numbers in
   captions with f-strings, never as typed digits. Check each one with an `assert` against a
   hand calculation or a second computation, and say where the expected value came from in a
   comment.
3. **Keep two layers.** The computation layer (data, results, asserts) comes first in
   `scene.py`. The display layer (colors, positions, captions, timing) comes after it and never
   changes a result.
4. **One caption states one fact.** A caption is a plain sentence of at most two lines. Do not
   repeat what the picture or the previous caption already shows. Do not open with "So" or
   "Here we see". Define each term in the caption where it first appears (e.g., "Shortest
   processing time first (SPT) runs the shortest job next").
5. **Nothing leaves the screen without a click.** `say()` and `clear_stage()` add the click for
   you. Any other `FadeOut` needs a `self.pause(...)` before it. `check` lists each one you miss.
6. **Part titles say what the part does**, starting with a verb ("Scheduling in arrival
   order"), not a label ("Results").
7. **Use only the helpers and plain Manim shapes.** Do not use `MathTex` or `Tex`, since they
   need LaTeX, which the environment does not have. Write formulas as plain text with
   `label()`, as the example does for its average.
8. **A clean exit is not a review.** Look at the still frames after every render (step 6).

## Steps

1. **Read the project.** Find the method the student wants to explain, the code that runs it,
   and one small instance the video can show in full. A small instance (4 to 8 jobs, a handful
   of stops) is easier to follow than the full data set. Note the numbers the video will show.
2. **Propose the plan and wait.** Show the student one table with a row per part (2 to 5
   parts). Each row gives the scene class name (`Part1Setup`), the title, what the part shows,
   every number it displays and the code that produces it, and where the clicks fall. Then
   list every term a classmate may not know, with its one-clause definition and the part
   where it first appears.

   Also propose two parts that help the student check the method, not only present it. The
   student can decline either one.
   - **Why it works.** If the method has a known argument (an exchange argument, a bound, an
     invariant), walk through it with the instance's own numbers, then state it in general.
     If no argument is known, show the step that makes the method's choice and why it is
     reasonable.
   - **Checking it.** Compare the method's result on the small instance with brute force, a
     solver, or a known answer, and show where the method lands.

   The example does both (Parts 3 to 6). Ask the student to approve or change the plan. Write
   no scene code until they approve.
3. **Set up the folder.** If the project has no `video/` folder, copy this skill's
   `template/` folder into the project root as `video/`. Then run `pixi install` in `video/`.
   Create `video/<video name>/scene.py` for the new video (e.g., `video/route-builder/`).
   Leave `spt-example/` in place as a reference.
4. **Write the computation layer.** Choose one of two ways to get the numbers.
   - **Import the method** when its packages are already in the video environment (Python,
     NumPy, Polars). Put the project's code folder on the path at the top of `scene.py`, e.g.,
     `sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))`.
   - **Read a results file** when the method needs other packages (a solver, a large data
     set). Write a short script that runs in the project's own environment and saves the
     numbers the video shows to `video/<video name>/results.json`. The scene reads that file.
     Tell the student to rerun the script whenever the method changes.

   Add an `assert` for every displayed number. Run `pixi run render <video name> check` from
   `video/`. A failed assert is a finding about the method or the computation, so report it to
   the student before you continue.
5. **Write the display layer.** Subclass `VideoScene` for each part, list the parts in order
   in `PARTS = [...]` at the top of `scene.py`, and use `title_card()`, `say()`, `pause()`,
   and `clear_stage()` as the example does. Draw the project's own pieces (a route map, a
   Gantt chart, a bar chart) as functions in `scene.py`. Run `check` after every round of
   edits and fix every problem it lists.
6. **Render a preview and review the stills.** Run `pixi run render <video name> preview`.
   It writes one still per click and a contact sheet per part to
   `video/<video name>/output/preview/stills/`. Open every contact sheet as an image if you
   can view images. Look for text that is cut off, overlaps, or runs past the frame. Look for
   a term used before it is defined, a caption that describes something not yet on screen,
   and leftover objects from an earlier step. If you cannot view images, tell the student
   which sheets to open and what to look for. Fix what you find and render again.
7. **Render the final version.** Run `pixi run render <video name> final`. Report the MP4
   path, the deck path, and the number of slides it printed. Tell the student to open the
   deck in a browser and click through it once.

## Helpers in `video_helpers.py`

| Helper | What it does |
|---|---|
| `VideoScene` | The scene class for each part. It slows every animation slightly so it is easy to narrate. |
| `self.title_card(title)` | Opens a part with its title, which fades before the first caption. |
| `self.say(text)` | Shows a caption at the top. It waits for a click first if anything has played since the last click. |
| `self.pause(name)` | Holds the picture briefly for the MP4, then ends the slide (one click). The name labels the still. |
| `self.clear_stage()` | Fades out everything but the caption, after a click if needed. |
| `self.emphasize(mob)` | Draws an outline around shapes to point at them. It fades with the next caption. Outline shapes, not the labels under them. |
| `label(text, size, color)` | One line of text. |
| `text_block(lines, size, color)` | Several centered lines. |
| `make_box(title, lines, color, fill, width)` | A rounded box with a title and lines under it. |
| `INK`, `MUTED`, `FAINT`, `BLUE`, `RED`, `GOLD` | The colors. `BLUE` and `RED` stay distinct under common color blindness. Use `FAINT` for fills only. |

## Render modes

Run these commands from `video/`. Add `--parts Part2Name` to render only some parts, which
skips the joined MP4 and the deck.

| Command | What it does | Time for the example |
|---|---|---|
| `pixi run render <video name> check` | Runs every scene without rendering and lists layout and click problems | about 35 seconds |
| `pixi run render <video name> preview` | Renders 720p video, stills, the MP4, and the deck | about 35 seconds |
| `pixi run render <video name> final` | Renders 1080p video, stills, the MP4, and the deck | about 70 seconds |

## Common problems

- **"Caption too long for two lines."** Split it into two captions, each one fact.
- **"runs past the frame edge" or "reaches into the caption."** Move or shrink the object
  named in the message. The frame is about 14.2 units wide and 8 tall, centered on (0, 0).
- **"FadeOut without a click before it."** Add `self.pause("name")` before that animation.
- **manim stops with a Python error.** The error names the line in `scene.py`. An
  `AssertionError` from the computation layer means a displayed number disagrees with its
  check.
