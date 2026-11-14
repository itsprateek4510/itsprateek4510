# `scripts/generate_profile.py`

Builds the two self-contained GitHub profile cards (`assets/dark.svg`, `assets/light.svg`)
and the plain-text ASCII portrait (`assets/portrait.txt`).

It is the only file that talks to GitHub, and the only file that writes into `assets/`.

## Quick flow

```text
profile.json ──┐
               ├─> photo_to_ascii() ──> portrait lines ─┐
assets/myphoto.jpg ┘                                   │
                                                       ├─> render_svg() ──> dark.svg / light.svg
GitHub GraphQL API ──> fetch_stats() ──> stats dict ───┘
                                                       └─> portrait.txt
```

The optional `PROFILE_BIRTH_DATE` environment variable adds an `Uptime:` row.

## What is in the file

### GraphQL query constants

- `USER_QUERY` — the user's `id` and follower count.
- `REPOS_QUERY` — every owned, non-fork repository with its star count, paginated 100 at a time.
- `HISTORY_QUERY` — commits on a repository's default branch, filtered to the user's author ID,
  paginated 100 at a time. Additions/deletions are read per commit.

### `THEMES`

Two colour dictionaries (`dark`, `light`). `render_svg` looks up every colour here, so adding a
theme means adding one entry and passing its name through.

### `github_request(query, variables, token) -> dict`

Sends a POST to `https://api.github.com/graphql` with a `Bearer` token and a JSON body.

- Returns the `data` object from the response.
- Turns `HTTPError`, `URLError`, and GraphQL `errors` into a `RuntimeError`.
- Deliberately **raises instead of returning zeroes**, so a failed API call cannot overwrite real
  statistics with fake ones.

### `fetch_stats(username, token) -> dict`

Collects six numbers:

| Key | Meaning |
| --- | --- |
| `repos` | owned, non-fork repositories visible to the token |
| `stars` | sum of stargazers on those repositories |
| `followers` | follower count |
| `commits` | all-time authored commits on default branches |
| `additions` | cumulative added lines across those commits |
| `deletions` | cumulative deleted lines across those commits |

Repository pages and commit-history pages are both looped until `hasNextPage` is false.
A repository with no default branch (`defaultBranchRef == null`) contributes its repo count but no
commits. A missing user raises `RuntimeError`.

### `calculate_uptime(birthday, today) -> str`

Takes `birthday` as `DD-MM-YYYY` and returns e.g. `"26 years, 3 months, 19 days"`.

- Counts full calendar months, then days since the last monthly anniversary.
- Clamps to month end, so `29-02` and `31-01` work in short months.
- Raises `ValueError` for invalid formats or a future birth date.

### `render_svg(config, portrait, stats, theme, today, uptime=None) -> str`

Returns one complete SVG string. Nothing is loaded from the network or disk at render time, so the
output is safe to embed in a README.

Layout notes:

- Width and height grow with the longest row, with a minimum of 1120 × 748.
- Left column is the ASCII portrait inside a `<text id="portrait">` element, one `<tspan>` per line.
- Right column is a neofetch-style key/value list built from `config`.
- `stats is None` renders `not synced` instead of numbers (preview mode).
- `Lines of Code` shows `+additions / -deletions` in green/red.
- All user/content text goes through `html.escape`, so names with `<`, `>`, `&`, or quotes stay valid XML.
- The SVG contains no `<image>`, `<script>`, or `<foreignObject>`.

### `main(argv=None)`

Command-line entry point.

| Flag / env | Effect |
| --- | --- |
| `--output-dir` | where the three files are written (default `assets/`) |
| `--preview` | offline layout; stats say `not synced`; GitHub is never contacted |
| `GH_TOKEN` / `GITHUB_TOKEN` | required unless `--preview` |
| `PROFILE_BIRTH_DATE` | optional `DD-MM-YYYY`; adds the `Uptime` row |

Important ordering: all API calls and SVG rendering finish **before** any file is written. If the
API fails, the previously committed assets remain untouched. Output is UTF-8; `portrait.txt` is
written with a trailing newline.

## Run it

```sh
python -m scripts.generate_profile                 # real stats (needs a token)
python -m scripts.generate_profile --preview --output-dir /tmp/preview
```
