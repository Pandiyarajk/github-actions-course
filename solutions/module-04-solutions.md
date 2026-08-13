# Module 4 — Solutions

![Module](https://img.shields.io/badge/Module-4-1f6feb?style=flat-square) ![Type](https://img.shields.io/badge/Type-Solutions-2da44e?style=flat-square)

> Navigation: [Course Home](../README.md) | [Solutions Index](./README.md) | [Module 4](../modules/module-04-scheduled-workflows.md)

Work each lab yourself before opening the answer. The point of the lab is the
error you hit on the way, not the finished YAML.

## Quiz Answers

**1 — B.** Every cron expression in GitHub Actions is evaluated in UTC, and
there is no `timezone:` key to change that (D). At UTC+5:30, `0 9 * * *` fires at
09:00 UTC, which is 14:30 local — you add your offset to the UTC time to get
local, or subtract it from your desired local time to get the cron. So 9:00 AM
local is `30 3 * * *`. Options A and C encode the two directions people guess
when they assume some conversion is happening for them: none is. The corollary
that catches teams twice a year is that UTC has no daylight saving, so a cron
tuned to local time drifts by an hour when your own zone shifts.

**2 — B.** GitHub only runs `schedule` events from the repository's **default
branch**. A cron on a feature branch is inert, which makes scheduled workflows
uniquely awkward to test: unlike `push` or `pull_request`, you cannot validate
the trigger from the branch you are developing on. That is exactly why the module
insists on adding `workflow_dispatch` alongside `schedule` — the dispatch trigger
*does* work from any branch, so you can prove the job body is correct before
merging, and then only the cron string itself remains unverified.

A related surprise worth knowing: GitHub disables scheduled workflows in public
repositories that have seen no activity for 60 days, and emails the repository
owner. A suite that "silently stopped running months ago" is often this rather
than a broken cron.

**3 — B.** `*/30 * * * *` means "every 30th minute" in the minute field —
minutes 0 and 30 of every hour. Option A puts the step in the **hour** field
(`0 */30 * * *`), so it means minute 0 of every 30th hour; since hours only run
0–23, that collapses to 00:00 daily. This is the single most common cron mistake
in the module's list: the step value has to go in the field whose unit you mean.
Option C (`30 * * * *`) is hourly at half past. Option D fires every minute of
hour 0.

**4.** Each `cron:` entry is an independent trigger, so four entries produce four
separate runs at their own times — they do not combine, and if two entries
coincide (say `0 * * * *` and `0 */6 * * *` at midnight) you get two runs of the
same workflow at once.

To tell which one fired, read `github.event.schedule`. It holds the **exact cron
string** from the `on:` block, so a step can branch with
`if: github.event.schedule == '30 1 * * *'`. Two practical constraints: the
comparison is a plain string match, so the literal in the `if:` must be
character-identical to the one in `on:` — a different amount of whitespace
between fields is a different string and the condition silently never matches.
And `github.event.schedule` is empty for any non-schedule trigger, so every such
step is skipped on a manual dispatch.

`github.event_name` is not enough because it is the same value — `schedule` — for
all four entries. It distinguishes cron from `push` or `workflow_dispatch`, not
one cadence from another.

**5.** Cron in GitHub Actions is a best-effort trigger, not a guarantee. Runs are
queued rather than started at the instant the minute arrives, and delays of
minutes to tens of minutes are normal — the platform schedules them alongside
everyone else's, and load peaks on the hour because the overwhelming majority of
crons are written at minute 0. Under sufficient load an occurrence can be dropped
entirely rather than run late. GitHub's own guidance is explicit that scheduled
workflows may be delayed during periods of high load.

Design changes that make the suite reliable in spite of that:

- **Move off the hour.** `30 1 * * *` is already better than `0 1 * * *`; an
  offset like `17 1 * * *` avoids the crowd further. This costs nothing and
  measurably reduces queue time.
- **Add `workflow_dispatch`.** A dropped occurrence becomes a one-click re-run
  instead of a lost night, and it is how you test the job at all before merging
  to the default branch.
- **Make the job idempotent and self-dating.** Derive report names, Allure
  directories, and Zephyr Scale cycle names from the actual run time rather than
  assuming "the 01:30 run", so a run that lands at 02:10 still files its results
  correctly and a doubled run does not overwrite the first.
- **Alert on absence, not just on failure.** A missing run produces no failed
  workflow and therefore no failure notification. Something outside the workflow
  — a check that the newest run is less than 26 hours old — is what catches a
  silently disabled schedule.
- **Set `timeout-minutes`** so a run that starts late and overlaps the next
  occurrence cannot pile up, and consider `concurrency:` with
  `cancel-in-progress: false` to serialise overlapping runs (see
  [Module 11](../modules/module-11-misc-features.md)).

## Lab 1 — Beginner

**Task:** Add a daily schedule at your local 9:00 AM converted to UTC.

<details>
<summary>Show solution</summary>

Working the conversion for IST (UTC+5:30): 09:00 local − 5:30 = 03:30 UTC, so
the cron is `30 3 * * *`. For EST (UTC−5) it would be `0 14 * * *`; for PST
(UTC−8), `0 17 * * *`.

```yaml
name: Daily Smoke

on:
  schedule:
    # 09:00 IST (UTC+5:30) == 03:30 UTC. Cron is ALWAYS UTC.
    - cron: "30 3 * * *"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  smoke:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      - name: Install dependencies
        working-directory: your-solution-root-folder-name
        run: pip install -r requirements.txt

      - name: Run smoke suite
        working-directory: your-solution-root-folder-name
        run: behave --tags=smoke
```

**Why this works.** `schedule` takes a list of maps, each with a single `cron:`
key — the list form is what allows several cadences later. The cron string is
quoted, `workflow_dispatch` sits alongside it so the job body is testable
immediately, and `timeout-minutes` bounds a run that starts late.

**Verify the failure mode the lab asks for.** Commit the workflow on a feature
branch and wait for the time to pass. Nothing runs, and there is nothing to read
— no error, no queued run, no entry in the Actions tab. Merge the same file to
the default branch and the schedule becomes live. This is the failure the lab
exists to produce: with `schedule`, "it works on my branch" is not a state that
exists.

While the file is still on the branch, press **Run workflow** to dispatch it.
That proves the job is correct, and isolates the remaining risk to the cron
string alone.

A second, quicker failure: drop the quotes from a cron that begins with `*`.

```text
    - cron: */30 * * * *
```

This is a YAML error, not a cron error — a plain scalar cannot start with `*`,
because `*` introduces an alias. The workflow fails to load. Quote every cron
string and the question never arises.

**Common wrong answer.** Writing the local time directly (`0 9 * * *` for 9 AM
IST) and finding the suite runs mid-afternoon. The near-miss version is
converting correctly but writing `9 30 * * *` — fields are minute-first, so that
is minute 9 of hour 30, an hour that does not exist.

</details>

## Lab 2 — Intermediate

**Task:** Add weekday and weekend schedules that print different messages.

<details>
<summary>Show solution</summary>

```yaml
name: Weekday and Weekend Suites

on:
  schedule:
    - cron: "0 3 * * 1-5"    # Mon-Fri at 03:00 UTC
    - cron: "0 4 * * 0,6"    # Sat & Sun at 04:00 UTC
  workflow_dispatch:

permissions:
  contents: read

jobs:
  cadence:
    runs-on: ubuntu-latest
    steps:
      - name: Weekday run
        if: github.event.schedule == '0 3 * * 1-5'
        # Note the value is quoted in full -- a plain scalar cannot contain ": ".
        run: 'echo "Weekday: behave --tags=smoke"'

      - name: Weekend run
        if: github.event.schedule == '0 4 * * 0,6'
        run: 'echo "Weekend: behave --tags=regression"'

      - name: Manual run
        if: github.event_name == 'workflow_dispatch'
        run: echo "Manual dispatch - running the default smoke suite"
```

**Why this works.** Both crons live under one `schedule` list and each fires its
own run of the same workflow; the `if:` conditions then route to different work.
`1-5` is an inclusive range over the day-of-week field, and `0,6` is a list.
Because day-of-week accepts both `0` and `7` for Sunday, `0,6` and `6,7` describe
the same two days — but they are different *strings*, which matters for the next
paragraph. The third step covers the manual case, which matches neither cron
comparison.

**Verify the failure mode the lab asks for.** Change only the `if:` on the
weekday step so its spacing differs from the `on:` block — for example
`if: github.event.schedule == '0 3 * * 1-5 '` (trailing space), or write the
range as `1,2,3,4,5` in the `if:` while `on:` still says `1-5`. Wait for the
weekday run. The job succeeds with **every step skipped**: the run happened, it
was green, and it did no work. `github.event.schedule` is compared as an opaque
string, so a semantically equivalent cron is not an equal cron.

This is the characteristic scheduled-workflow failure: green runs that do
nothing. Guard against it by adding a final step that fails when no cadence
matched:

```yaml
      - name: Fail if no cadence matched
        if: github.event_name == 'schedule' && github.event.schedule != '0 3 * * 1-5' && github.event.schedule != '0 4 * * 0,6'
        run: |
          echo "Unrecognised schedule: ${SCHEDULE}"
          exit 1
        env:
          SCHEDULE: ${{ github.event.schedule }}
```

**Common wrong answer.** Trying to distinguish the cadences with
`github.event_name`, which is `schedule` for both, so whichever step is listed
first runs on every scheduled run. The other frequent slip is `* * * * 1-5`,
which is every minute of every weekday rather than once a day — five days of
minute-by-minute runs is a memorable way to learn what an unfilled minute field
means.

</details>

## Lab 3 — Challenge

**Task:** Add an every-6-hours schedule and branch logic using
`github.event.schedule`.

<details>
<summary>Show solution</summary>

The full multi-cadence version is in
[`module-04-scheduled-workflows.yml`](../examples/module-04-scheduled-workflows.yml).
A focused answer:

```yaml
name: Multi-Cadence Suite

on:
  schedule:
    - cron: "0 */6 * * *"    # 00:00, 06:00, 12:00, 18:00 UTC
    - cron: "30 1 * * *"     # Daily at 01:30 UTC - nightly regression
  workflow_dispatch:
    inputs:
      cadence:
        description: "Cadence to simulate when running manually"
        type: choice
        options:
          - six-hourly
          - nightly
        default: six-hourly
        required: true

permissions:
  contents: read

jobs:
  dispatch-by-cadence:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - name: Checkout repository
        uses: actions/checkout@v7

      - name: Set up Python
        uses: actions/setup-python@v7
        with:
          python-version: "3.13"

      # Resolve the cadence ONCE, from either trigger, into a step output.
      # Every later step keys off this instead of repeating the cron literals.
      - name: Resolve cadence
        id: cadence
        env:
          SCHEDULE: ${{ github.event.schedule }}
          MANUAL: ${{ inputs.cadence }}
        run: |
          case "${SCHEDULE}" in
            "0 */6 * * *") resolved="six-hourly" ;;
            "30 1 * * *")  resolved="nightly" ;;
            "")            resolved="${MANUAL:-six-hourly}" ;;
            *)             echo "Unrecognised schedule: ${SCHEDULE}"; exit 1 ;;
          esac
          echo "resolved=${resolved}" >> "$GITHUB_OUTPUT"
          echo "Cadence: ${resolved}"

      - name: Install dependencies
        working-directory: your-solution-root-folder-name
        run: pip install -r requirements.txt

      - name: Six-hourly health check
        if: steps.cadence.outputs.resolved == 'six-hourly'
        working-directory: your-solution-root-folder-name
        run: behave --tags=healthcheck

      - name: Nightly regression
        if: steps.cadence.outputs.resolved == 'nightly'
        working-directory: your-solution-root-folder-name
        run: |
          behave --tags=regression \
            -f allure_behave.formatter:AllureFormatter \
            -o reports/allure-results

      - name: Upload Allure results
        if: always() && steps.cadence.outputs.resolved == 'nightly'
        uses: actions/upload-artifact@v7
        with:
          name: allure-nightly-${{ github.run_id }}
          path: your-solution-root-folder-name/reports/allure-results/
          retention-days: 30
```

**Why this works.** `0 */6 * * *` steps the **hour** field by six from 0, giving
00:00, 06:00, 12:00 and 18:00 UTC — four runs a day, each a separate workflow
run carrying its own `github.event.schedule`.

The design point is the `Resolve cadence` step. Comparing cron literals directly
in each `if:` works, but it scatters the same fragile string across the file and
leaves manual dispatches matching nothing. Resolving once into a step output
gives a single place where a cron string appears, makes the manual path a
first-class cadence via `${MANUAL:-six-hourly}`, and — because the `case` has a
`*)` arm that exits non-zero — turns an unrecognised cron into a red run instead
of a green no-op. The cron strings are read from `env:` inside the script rather
than interpolated into it, so no `${{ }}` sits at column 0 in the `run:` block.

The artifact name includes `github.run_id` because artifacts are immutable from
v4 onward: two runs uploading the same name would conflict rather than merge
(see [Module 10](../modules/module-10-artifacts.md)).

**Verify the failure mode the lab asks for.** Remove the `""` arm from the
`case` and dispatch the workflow manually. `github.event.schedule` is empty for
`workflow_dispatch`, so `SCHEDULE` is an empty string, the `*)` arm catches it,
and the run fails with `Unrecognised schedule:` and nothing after the colon —
which is the point: the empty value *is* the diagnosis.

Now do the version without the resolve step, comparing cron literals directly in
each `if:`, and dispatch manually. Every conditional step is skipped and the job
finishes green having installed dependencies and run no tests. Compare the two
outcomes: both are wrong, but only one of them tells you so. Reproducing this
pair is the lab.

**Common wrong answer.** `*/6 * * * *` — stepping the minute field instead of the
hour, giving 240 runs a day rather than four. The other is assuming
`github.event.schedule` reports a friendly label ("six-hourly") or a timestamp;
it is verbatim the cron string from the `on:` block, whitespace included, which
is why it should be matched in exactly one place.

</details>

---

[Solutions Index](./README.md) | [Module 4](../modules/module-04-scheduled-workflows.md) | [Course Home](../README.md)
