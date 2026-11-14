# `scripts/photo_to_ascii.py`

Turns one photo into a fixed-size ASCII portrait. The original photo is only ever read, never
modified or embedded.

## What is in the file

### Constants

- `RAMP = " .:-=+*#%@"` — 10 brightness levels, darkest to brightest. A dark pixel becomes a dense
  character like `@`; a light pixel becomes a space.
- `CHARACTER_ASPECT = 0.5` — terminal characters are about twice as tall as they are wide, so the
  image is pre-stretched vertically to avoid a squashed face.

### `photo_to_ascii(path, columns=55, rows=30, crop=None, subject_outline=None) -> list[str]`

Returns `rows` strings, each exactly `columns` characters long.

Pipeline, in order:

1. **Validate** — `columns`/`rows` must be positive. `crop` must be four fractions
   `[left, top, right, bottom]` with `0 <= left < right <= 1` and `0 <= top < bottom <= 1`.
   Anything else raises `ValueError`; a missing file raises `FileNotFoundError`.
2. **Load** — applies EXIF rotation (`ImageOps.exif_transpose`) and converts to grayscale.
3. **Mask** — starts fully white (keep everything) when `subject_outline` is absent. When an
   outline is given, a black image is created and the polygon is filled white, so everything
   outside the outline is discarded.
4. **Crop** — `crop` fractions are converted to pixel coordinates and applied to both image and mask.
5. **Boost contrast** — `autocontrast` followed by a 1.6× contrast enhance.
6. **Invert inside the mask** — `Image.composite(ImageOps.invert(image), black, mask)`. This makes
   dark hair/clothing dense while masked-out background stays empty.
7. **Correct aspect** — `ImageOps.fit` to `(columns, rows / 0.5)` crops rather than stretches, then
   resize to exactly `(columns, rows)`.
8. **Map to characters** — pixel values 0–255 become indices 0–9 with integer arithmetic, then are
   looked up in `RAMP` via numpy.

`crop` and `subject_outline` are coordinates as **fractions of the EXIF-oriented image**, which
makes the settings independent of the original photo's pixel size.

### `main()`

Thin CLI wrapper that prints the grid:

```sh
python -m scripts.photo_to_ascii assets/myphoto.jpg --profile profile.json
python -m scripts.photo_to_ascii photo.jpg --columns 40 --rows 20 --crop 0.3 0.1 0.7 0.5
```

Options: `photo`, `--columns`, `--rows`, `--crop` (four floats), `--profile` (a JSON file whose
`crop` and `subject_outline` are used as defaults). Explicit `--crop` wins over the profile file.
