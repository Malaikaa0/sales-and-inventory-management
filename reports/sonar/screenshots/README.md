# SonarQube screenshots

Captured on 2026-11-28 from the local SonarQube server by an automated browser script, signed in as a temporary user that was deactivated afterwards.

| Files | What they show |
| --- | --- |
| `before-*` | Scoped analysis before the fixes and exclusions: gate failed, 6 bugs, 13 vulnerabilities |
| `after-*` | Scoped analysis of commit `f5167a9`: gate passed |
| `project-whole-repository-overview.png` | Analysis of the whole repository, taken earlier the same day |
| `project-function-complexity.png` | Per-function cyclomatic and cognitive complexity of `services.py` |

After the exclusions, the overview still lists one issue under Reliability. It is the `autofocus` code smell on the sign-in page, which is not counted as a bug and does not affect the gate.
