# Terminal profile setup

Personal details come from the previous README and existing résumé, not the sample prompt. Unknown OS, IDE, birthday, and hobbies are intentionally omitted; the interests describe your existing projects.

## Files

```text
.
├── README.md
├── SETUP.md
├── profile.json                   # Verified profile details and portrait crop
├── requirements.txt               # Pillow + numpy
├── assets/
│   ├── myphoto.jpg                 # Original photo, never modified
│   ├── portrait.txt                # Generated 55-column × 30-row ASCII
│   ├── dark.svg                    # Self-contained dark terminal card
│   └── light.svg                   # Self-contained light terminal card
├── scripts/
│   ├── photo_to_ascii.py
│   └── generate_profile.py
├── tests/
│   └── test_profile.py
└── .github/workflows/update.yml
```

Previous SVG assets are left untouched.

## Publish

1. Create the public profile repository **`itsprateek4510/itsprateek4510`** (this repository already has that remote). The repository name must exactly match your username.
2. Create a **fine-grained personal access token** for your account. Grant access to all repositories whose stats you want included, with **Contents: Read-only** (Metadata read access is automatic). Public repositories are readable; include private repositories only if you want their aggregate counts published. A classic PAT with `repo` scope also works but grants broader access. Organization repositories may require organization approval/SSO authorization.
3. In **Settings → Secrets and variables → Actions**, add the repository secret **`PROFILE_TOKEN`** with that token. Never put it in `profile.json`, the README, or a committed `.env` file.
4. Allow **Read and write permissions** under **Settings → Actions → General → Workflow permissions** if restricted by repository policy. The workflow uses the automatic `GITHUB_TOKEN` to push; the profile token is only for reading statistics. Branch protection must allow the bot's direct updates.
5. Commit and push these files, including `assets/myphoto.jpg`. The workflow runs on pushes to `main`, daily at **03:17 UTC**, and manually from **Actions → Update terminal profile → Run workflow**. If your default branch isn't `main`, update the workflow's branch filter. Scheduled runs use the default branch and may be delayed by GitHub.

The workflow tests the scripts, regenerates both cards, and commits only changed generated assets. Bot pushes don't loop; generated-only pushes are also excluded. Keep the token valid; failed API requests fail the job rather than replacing real stats with zeros. GitHub may disable scheduled workflows on inactive public repositories after 60 days; re-enable them in Actions if needed.

## Run locally

Python **3.12 or later**:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v

# Print the head-and-shoulders ASCII portrait directly.
python -m scripts.photo_to_ascii assets/myphoto.jpg --crop 0.25 0.075 0.68 0.545

# Read a token without putting its value into shell history (bash/zsh).
read -rs GH_TOKEN
export GH_TOKEN
python -m scripts.generate_profile
unset GH_TOKEN
```

Alternatively, when already authenticated with GitHub CLI:

```sh
GH_TOKEN="$(gh auth token)" python -m scripts.generate_profile
```

Without a token, preview into a separate directory so real assets stay intact:

```sh
python -m scripts.generate_profile --preview --output-dir /path/to/preview
```

Preview stats explicitly say **not synced**; no sample numbers are presented as real data. Production generation requires `GH_TOKEN` (or `GITHUB_TOKEN`) from the environment and queries the GitHub GraphQL API.

## Customize

Edit **`profile.json`** for profile text. Crop coordinates are `[left, top, right, bottom]`, each a fraction of the EXIF-oriented image; the current crop isolates your head and shoulders. The converter uses the exact ramp ` .:-=+*#%@`, autocontrast plus a 1.6× contrast boost, and a 0.5 character width/height ratio. SVG text uses matching geometry, preserved spaces, and a local Consolas / Fira Code / Liberation Mono fallback stack, with no remote fonts or embedded photo.

Birthday-based **Uptime** is optional. Set the Actions secret **`PROFILE_BIRTH_DATE`** to `DD-MM-YYYY`, or export that variable locally. Without it, the row is omitted. Years/months/days are computed using UTC dates, with month-end clamping for short months and leap birthdays. The birthday itself isn't written to the card, but the displayed age still reveals approximately when you were born.

## What the stats mean

- **Repos:** owned, non-fork repositories visible to the token, including archived repositories.
- **Stars:** sum of stars on those repositories.
- **Followers:** GitHub's current follower count.
- **Commits:** all-time commits GitHub attributes to your account on those repositories' **default branches**. All repository and commit-history pages are fetched; empty repositories count as repos but have no commits.
- **Lines of Code:** cumulative `+additions / -deletions` reported for those same authored commits. This is **churn**, not current source-code size or unique lines. Changes later reverted, generated files, and merges follow GitHub's commit-diff accounting.

These aren't contribution-calendar totals: forks, other people's repositories, organization-owned repositories, and non-default branches are excluded. Author emails must be associated with your GitHub account for commits to be attributed. Private repository names and source aren't published, but their aggregate stats are included if readable by the token. The update bot's commits are not authored by you and don't inflate your commit/line counts.
