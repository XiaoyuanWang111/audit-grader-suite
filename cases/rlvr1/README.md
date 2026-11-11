# The RLVR1 case

Each RLVR1 run worked in a folder that held this case (178 files, 115 MB) beside a Python environment. This folder
keeps five of the case's files:

- `TASK.md`: the run's task description, with the workspace's absolute path written as `<W>` (six times). Nothing
  else is changed.
- `SOURCES.md`: where every file of the case comes from, byte-identical to the run's copy.
- `MANIFEST.sha256`: the sha256 of every other file of the case. Its line for `TASK.md` is the hash of the copy the
  case was built with; each run's copy names that run's own folder, so its hash differs.
- `panel/CONFIGS.md`: the generation settings of the stored responses, without the name of the hardware in its first
  sentence; `MANIFEST.sha256` has the hash of the run's copy.
- `deps/requirements.lock.txt`: the Python packages of the run's environment, byte-identical.

The graders, the reference, the rows and the NLTK data come from the public sources that `SOURCES.md` lists. The
stored responses (74 MB) are not published.
