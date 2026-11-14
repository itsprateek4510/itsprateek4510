# `profile.json`

Data file that drives `scripts/generate_profile.py`. Editing this changes the card text without
touching Python code. It contains no secrets.

## Fields

| Key | Type | Used for |
| --- | --- | --- |
| `username` | string | GitHub login; also shown in the title bar and `user@github` header |
| `name` | string | display name under the portrait and in the `<title>` |
| `role` | string | rendered as `Kernel:` |
| `photo` | path | source image, relative to the repository root |
| `crop` | 4 numbers | `[left, top, right, bottom]` fractions of the EXIF-oriented photo |
| `subject_outline` | list of `[x, y]` | polygon that keeps the person and blanks the background |
| `info` | list of `[label, value]` | extra rows after the fixed header rows |
| `projects` | list of strings | rows under the `— Projects` section |
| `email` | string | `Email:` row |
| `linkedin` | string | `LinkedIn:` row |

## How the portrait coordinates work

All coordinates are fractions (`0.0`–`1.0`) of the image **after EXIF rotation**, not pixels. This
keeps them valid if you replace the photo with a larger version of the same framing.

- `crop` selects the head-and-shoulders region first.
- `subject_outline` is a hand-traced polygon in the same coordinate space. Points inside it are
  drawn; everything outside becomes spaces.

Order matters: the outline mask and the crop are applied before contrast stretching and the ASCII
conversion. If you replace `assets/myphoto.jpg` with a different composition, retrace both.

## Example (abridged outline)

```json
{
  "username": "itsprateek4510",
  "name": "Prateek Kushwaha",
  "role": "Backend Developer",
  "photo": "assets/myphoto.jpg",
  "crop": [0.29, 0.085, 0.63, 0.455],
  "subject_outline": [[0.374, 0.174], [0.378, 0.151]],
  "info": [["Location", "Delhi, India"]],
  "projects": ["UPI Offline Mesh / RSA + AES-GCM"],
  "email": "prateekkushwaha868@gmail.com",
  "linkedin": "linkedin.com/in/itsprateek4510"
}
```

Notes:

- `info` labels are rendered as-is; a dot in a label (e.g. `Languages.Programming`) is part of the
  visible text.
- `projects` are plain text; no links are generated.
- Values are HTML-escaped when rendered, so `&`, `<`, and quotes are safe.
- Keep this file valid JSON; `python -m scripts.generate_profile --preview` is a quick syntax check.
