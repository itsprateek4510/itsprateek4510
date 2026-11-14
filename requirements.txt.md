# `requirements.txt`

Runtime dependencies for the profile generator. Versions are pinned so local runs and CI produce
the same output.

| Package | Used by | Why |
| --- | --- | --- |
| `Pillow==12.3.0` | `scripts/photo_to_ascii.py` | open, rotate, crop, mask, resize, and contrast-adjust the photo |
| `numpy==2.5.4` | `scripts/photo_to_ascii.py` | fast pixel→ramp-index conversion and `RAMP` lookup |

`generate_profile.py` and the tests use only the Python standard library on top of these.

Install:

```sh
python -m pip install -r requirements.txt
```

Both are imported at module import time, so the workflow installs them before running the tests.

Notes:

- The tests also rely on Pillow and numpy to build synthetic images.
- If you upgrade Pillow, re-run the full test suite; resampling and `ImageOps.fit` behaviour affects
  the exact ASCII output.
