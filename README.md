# OM 522: Production Scheduling

This repository contains in-class materials for **OM 522** at The University of Alabama during Fall
2026. Materials are added throughout the semester. Blackboard is the authoritative source for the
syllabus, required materials, assignments, announcements, grades, and deadlines.

## Course information

- **Instructor:** Nick Freeman
- **Email:** freem028@ua.edu
- **Meeting time:** Tuesdays and Thursdays, 9:30–10:45 a.m.
- **Location:** Bidgood Hall 121
- **Office hours:** Tuesdays and Thursdays, 11 a.m.–noon

The course studies scheduling decisions in production, logistics, and service settings. We will
connect production planning, detailed scheduling, operational uncertainty, and control while
learning to formulate, implement, and evaluate exact and heuristic solution methods.

Topics include production planning, single-machine scheduling, routing, parallel-machine
scheduling, project scheduling, job-shop scheduling, factory dynamics, and decision-making under
uncertainty. Lecture notes are distributed through Blackboard.

## Set up the course environment

1. Download and extract the repository.
2. Open a terminal.
3. Change into the repository root, i.e., the folder that contains `pixi.toml`. If the path
   contains spaces, put the complete path in quotation marks.
4. Run `pixi install`.

Pixi reads `pixi.toml` and the committed `pixi.lock` file. It then creates a local environment for
your operating system in `.pixi/`. The manifest (`pixi.toml`) lists the tools the project needs.
The lock file records the resolved package versions.

## Class sessions

Each session from September 29 on has its own folder under `in-class-notebooks/` and its own
environment. Run a session from its folder. For example, run these commands from the repository
root for the November 17 session:

```bash
cd in-class-notebooks/20261117
pixi install
pixi run class
```

The table lists each folder and the tasks it defines. The topic links to that session's guide.

| Date | Topic | Folder | Tasks |
|---|---|---|---|
| Aug. 25 | Dispatching rules | repository root | `lecture-20260825-edit`, `-check`, `-export` |
| Sept. 8 | Dynamic critical-ratio dispatching | repository root | `lecture-20260908-edit`, `-check`, `-export` |
| Sept. 22 | [Agentic AI](in-class-notebooks/20260922/README.md) | `20260922` | none |
| Undated | [Traveling salesman problem (TSP)](in-class-notebooks/TSP/README.md) | `TSP` | `demo`, `check`, `test` |
| Sept. 29 | [Clarke–Wright savings](in-class-notebooks/20260929/README.md) | `20260929` | `demo`, `test` |
| Oct. 6 | [Parallel machines](in-class-notebooks/20261006/README.md) | `20261006` | `demo`, `test` |
| Oct. 13 | [Eligible machines](in-class-notebooks/20261013/README.md) | `20261013` | `demo`, `test` |
| Oct. 15 | [Critical path](in-class-notebooks/20261015/README.md) | `20261015` | `demo` |
| Oct. 22 | [Distribution fitting](in-class-notebooks/20261022/README.md) | `20261022` | `demo` |
| Nov. 3 | [FlowSim production line](in-class-notebooks/20261103/README.md) | `20261103` | `demo` |
| Nov. 10 | [Stress test](in-class-notebooks/20261110/README.md) | `20261110` | `stress-test` |
| Nov. 12 | [Capacity, Little's Law, and Quiz 3](in-class-notebooks/20261112/README.md) | `20261112` | `class`, `quiz3` |
| Nov. 17 | [Variability and Quiz 4](in-class-notebooks/20261117/README.md) | `20261117` | `class`, `quiz4` |
| Nov. 19 | [Push and limits](in-class-notebooks/20261119/README.md) | `20261119` | `class` |
| Dec. 1 | [Where to spend the next dollar](in-class-notebooks/20261201/README.md) | `20261201` | `class` |

### Notes on the sessions

- The August 25 and September 8 tasks run from the repository root with the root environment. Use
  `pixi run` followed by the task name.
- Folders from November 3 on include a copy of FlowSim, so the root environment cannot run them.
- Quiz 3 runs in the November 12 folder with `pixi run quiz3`. Quiz 4 runs in the November 17
  folder with `pixi run quiz4`. Each quiz's handout on Blackboard walks through it.
- Each `.py` file is the editable Marimo notebook. Each `.html` file is a static export that opens
  in a browser without Python or Marimo.
- The underlying programs also run directly (e.g., `pixi run marimo edit ...` or `pixi run jupyter
  lab`). The named tasks preserve the correct dated paths.

## Single-machine instance generation

The reusable generator creates reproducible Parquet instances with processing times, release times,
due dates, weights, and optional setup times. Its settings appear in one configuration block inside
the script. The [instance-generation guide](sm-instance-generation/README.md) describes the
settings, output schemas, setup modes, and reproducibility behavior.

```bash
pixi run sm-instance-generate
```

## Folder layout

The data folder is a separate sibling of `in-class-notebooks/`, not a folder inside it. The August
25 notebook was created directly inside `in-class-notebooks/` during class. Its published location
adds the dated `20260825/` subfolder.

<details>
<summary>Show the full folder tree</summary>

```text
OM-522-Fall-2026-in-class/
├── data/
│   └── 20260825-demo/
│       └── production_jobs_30.csv
├── in-class-notebooks/
│   ├── 20260825/
│   │   ├── marimo-test.py
│   │   └── scheduling-dispatch-rules-summary.html
│   ├── 20260908/
│   │   ├── critical-ratio.py
│   │   ├── critical-ratio.html
│   │   └── pseudocode.png
│   ├── 20260922/
│   │   ├── README.md
│   │   ├── agentic-ai.html
│   │   ├── transcript.txt
│   │   ├── ai-update-prompt.md
│   │   └── TSP-demo/
│   ├── 20260929/
│   │   ├── README.md
│   │   ├── clarke_wright.py
│   │   └── routing_utils.py
│   ├── 20261006/
│   │   ├── README.md
│   │   ├── parallel_machines.py
│   │   └── parallel_utils.py
│   ├── 20261013/
│   │   ├── README.md
│   │   ├── eligible_machines.py
│   │   └── eligibility_utils.py
│   ├── 20261015/
│   │   ├── README.md
│   │   └── critical_path.py
│   ├── 20261022/
│   │   ├── README.md
│   │   ├── distribution_fitting.py
│   │   └── data-samples/
│   ├── 20261103/
│   │   ├── README.md
│   │   ├── production_line.py
│   │   ├── data/
│   │   ├── flowsim/
│   │   ├── pixi.toml
│   │   └── pixi.lock
│   ├── 20261110/
│   │   ├── README.md
│   │   ├── stress_test.py
│   │   ├── flowsim/
│   │   ├── pixi.toml
│   │   └── pixi.lock
│   ├── 20261112/
│   │   ├── README.md
│   │   ├── capacity_littles_law.py
│   │   ├── bottleneck_investigation.py
│   │   ├── flowsim/
│   │   └── pixi.toml
│   ├── 20261117/
│   │   ├── README.md
│   │   ├── variability.py
│   │   ├── variability_investigation.py
│   │   ├── make_seed_data.py
│   │   ├── data/
│   │   ├── flowsim/
│   │   └── pixi.toml
│   ├── 20261119/
│   │   ├── README.md
│   │   ├── push_and_limits.py
│   │   ├── flowsim/
│   │   ├── pixi.toml
│   │   └── pixi.lock
│   ├── 20261201/
│   │   ├── README.md
│   │   ├── next_dollar.py
│   │   ├── data/
│   │   ├── flowsim/
│   │   ├── pixi.toml
│   │   └── pixi.lock
│   └── TSP/
│       ├── data/
│       ├── tests/
│       ├── tsp_demo.py
│       ├── tsp_utils.py
│       ├── README.md
│       ├── pixi.toml
│       └── pixi.lock
├── sm-instance-generation/
│   ├── generate_instances.py
│   └── README.md
├── pixi.toml
└── pixi.lock
```

</details>
