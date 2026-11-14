# `.github/workflows/update.yml`

GitHub Actions workflow that refreshes the generated profile cards on a schedule and commits them
back to the repository.

## Triggers

| Trigger | When |
| --- | --- |
| `schedule` | daily at `03:17 UTC` (`cron: "17 3 * * *"`) |
| `push` | pushes to `main`, except commits that only touch generated assets |
| `workflow_dispatch` | manual run from the Actions tab |

The `paths-ignore` list (`assets/dark.svg`, `assets/light.svg`, `assets/portrait.txt`) prevents the
bot's own commit from starting another run.

## Permissions and concurrency

- `permissions.contents: write` — needed to push the regenerated assets.
- `concurrency.group: terminal-profile-${{ github.ref }}` with `cancel-in-progress: false` — runs for
  the same branch queue up instead of cancelling, so an in-progress commit is not interrupted.

## Job steps (`update` on `ubuntu-latest`)

1. **`actions/checkout@v4`** — gets the repository with the token that allows pushing.
2. **`actions/setup-python@v5`** — Python 3.12 with pip caching.
3. **Install dependencies** — `pip install -r requirements.txt`.
4. **Test** — `python -m unittest discover -s tests -v`. A failing test stops the workflow before
   any asset is touched.
5. **Generate profile** — `python -m scripts.generate_profile` with environment:
   - `GH_TOKEN` ← secret `PROFILE_TOKEN` (read-only token used for stats),
   - `PROFILE_BIRTH_DATE` ← optional secret `PROFILE_BIRTH_DATE` (`DD-MM-YYYY`).
6. **Commit updated assets** — configures the `github-actions[bot]` identity, stages only the three
   generated files, and commits/pushes only if `git diff --cached` is non-empty.

## Things to know

- If the API call fails, the script raises and the job fails; previously committed assets stay as
  they are.
- `GITHUB_TOKEN` is used for the push; `PROFILE_TOKEN` is only for reading statistics.
- The workflow assumes the default branch is `main`. Change the push filter if yours differs.
- Scheduled workflows can be disabled by GitHub after 60 days of repository inactivity.
