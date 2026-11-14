# `tests/test_profile.py`

Unit and integration tests for `scripts/photo_to_ascii.py` and `scripts/generate_profile.py`.

Run with:

```sh
python -m unittest discover -s tests -v
```

No network access is needed: `urlopen` and `fetch_stats` are mocked, and `profile.json` plus the
real photo are read only.

## Helpers

- `connection(nodes, cursor)` — builds a fake GraphQL pagination object; `cursor is not None` means
  "there is another page".
- `history(nodes, total, cursor)` — wraps commit nodes in the nested
  `repository → defaultBranchRef → target → history` shape.
- `ROOT` — repository root, used to read `profile.json` and `README.md`.
- `NS` — the SVG XML namespace, used by `ElementTree` queries.

## `AsciiTests`

Exercises `photo_to_ascii` with small generated images.

| Test | Checks |
| --- | --- |
| `test_dimensions_ramp_and_brightness` | output is 30×55, only uses `RAMP`, dark→`@`, light→space |
| `test_crop_selects_head_region` | crop keeps the requested half only |
| `test_aspect_correction_crops_instead_of_stretching` | wide image is cropped, not distorted |
| `test_subject_is_drawn_with_characters_and_background_is_blank` | polygon mask leaves background blank and fills the subject |
| `test_real_portrait_has_no_background_characters` | committed photo + `profile.json` produce a clean background |
| `test_invalid_dimensions_and_crop` | bad columns/rows/crop raise `ValueError` |
| `test_missing_image` | missing file raises `FileNotFoundError` |
| `test_command_prints_exact_grid` | `python -m scripts.photo_to_ascii` prints exactly 30×55 characters |

## `UptimeTests`

Covers `calculate_uptime`:

- ordinary calendar years/months/days,
- birthday and birth-day boundaries,
- leap day and short-month clamping (`29-02`, `31-01`),
- invalid formats and future dates raising `ValueError`.

## `GitHubTests`

Covers `github_request` and `fetch_stats` with mocked HTTP/GraphQL responses:

- the request hits the GraphQL URL with a `Bearer` token and a timeout,
- HTTP, URL, and GraphQL errors raise `RuntimeError` instead of returning zero stats,
- repositories and commit pages are paginated, stars/followers/commits/lines are summed,
- the query asks for `isFork: false`, `author:`, and `defaultBranchRef`,
- a user with no repositories returns all-zero counts,
- an unknown user raises `RuntimeError`.

## `RenderingTests`

Covers `render_svg` and `main` end to end:

- both themes are valid, self-contained SVG (no `image`, `script`, or `foreignObject`),
- theme colours, names, email, numbers, and formatted `+/-` lines appear,
- XML special characters are escaped and `Uptime` is optional,
- portrait whitespace and `<tspan>` count are preserved,
- preview mode says `not synced` and never calls GitHub,
- `main` writes `dark.svg`, `light.svg`, and `portrait.txt` from the real photo,
- a missing token exits before writing anything,
- a mocked authenticated API response flows into the SVGs without leaking the token,
- an API failure leaves existing assets byte-for-byte unchanged,
- `README.md` still references both theme SVGs (this is the one test that reads the README; it does
  not modify it).

## Notes when adding tests

- Keep tests offline: patch `profile.urlopen` or `profile.fetch_stats`.
- Use `tempfile.TemporaryDirectory()` for any file output.
- If you change the portrait geometry, update the `30`/`55` expectations and the crop/outline tests
  together.
