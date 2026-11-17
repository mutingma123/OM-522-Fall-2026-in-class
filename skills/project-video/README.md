# Project video skill

This folder is a skill, i.e., a set of instructions an AI coding agent follows to do one job.
This one makes a short animated video that explains a method from your project. The video
comes in two forms from the same code:

- an MP4 that plays on its own, and
- an HTML deck that stops at each step until you press the right arrow, which you can
  present from.

It works with any agent that can read files and run commands, e.g., Claude Code, Codex, or
Antigravity. [`SKILL.md`](SKILL.md) holds the agent's instructions. This page is for you.

## Try the example first

The example shows why shortest processing time first (SPT) gives the smallest sum of
completion times on one machine. It works through a swap argument with four jobs, proves it
in general, and then checks all 24 orders. It takes about a minute to render.

1. Pull the in-class repository.
2. Run these commands from the repository root.

   ```bash
   cd skills/project-video/template
   pixi install
   pixi run render spt-example preview
   ```

3. Open `spt-example/output/preview/deck/spt-example.html` in a browser. Press the right
   arrow to step through it. Press S to open the speaker view, which shows the current
   slide, the next slide, and a clock. Allow pop-ups if the browser blocks the window.
4. Open `spt-example/output/preview/spt-example.mp4` to watch the continuous version.
5. Read `spt-example/scene.py`. The top half computes and checks every number. The bottom
   half draws the video.

## Use it on your project

Give your agent this prompt. Replace the parts in brackets.

```text
Read skills/project-video/SKILL.md in the OM 522 in-class repository at [path to the
repository] and follow it. Make a short video that explains [your method, e.g., our
savings-based route builder] in my project at [path to your project]. Propose the plan
and wait for my approval before you write any code.
```

The agent will also offer two parts that help you check its work. One explains why the
method works. The other compares the method with brute force or a known answer on a small
case. Keep these parts when an agent wrote code you could not have written yourself. They show
whether the code does what the method claims.

Some agents also load skills from a folder in your project. For example, Claude Code reads
`.claude/skills/project-video/SKILL.md`. Check your agent's documentation if you want to
install it that way. The prompt above works either way.

## Work with the agent to improve it

The first version is a draft. The useful skill is steering the agent toward a better one.

1. **Read the plan before you approve it.** Check that the parts tell your method's story in
   order. Check that each number comes from your code. Cut any part that does not help a
   classmate follow the method.
2. **Watch the deck as your audience would.** Click through it once without reading your
   code. Note each place where you get lost or a slide says too little or too much.
3. **Give specific feedback.** Name the slide and say what to change. Each bullet below is a
   prompt you can adapt. Each one works better than "make it better".

    - On slide 4, the caption mentions the savings list before it appears. Show the list first.
    - Part 2 shows too many routes at once. Build them one at a time with a click between each.
    - Define "savings" in a caption the first time it appears.
    - Use a smaller instance with 6 customers so every route fits on screen.
    - Check the stills for Part 3 and fix any text that overlaps.
4. **Check the numbers yourself.** Pick two numbers on screen. Find the `assert` that checks
   each one in `scene.py`, and confirm that it matches what your method produces.

## If something goes wrong

- **`pixi install` fails.** Run it again from `skills/project-video/template`, or from your
  project's `video/` folder, where `pixi.toml` is.
- **The render stops with "Problems to fix".** Paste the message to your agent. Each line
  names the problem and the slide.
- **The deck opens to a blank page.** Keep the `deck/` folder together. The HTML file loads
  its videos from the `_assets` folder beside it.
