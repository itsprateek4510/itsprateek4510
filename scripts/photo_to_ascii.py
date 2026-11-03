"""Convert a photo to a contrast-boosted, aspect-correct ASCII portrait."""

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageOps


RAMP = " .:-=+*#%@"
CHARACTER_ASPECT = 0.5


def photo_to_ascii(path, columns=55, rows=30, crop=None, subject_outline=None):
    """Draw the subject, not the background; coordinates are image fractions."""
    if columns < 1 or rows < 1:
        raise ValueError("Columns and rows must be positive.")
    if crop is not None and not (len(crop) == 4 and
                                0 <= crop[0] < crop[2] <= 1 and
                                0 <= crop[1] < crop[3] <= 1):
        raise ValueError("Crop must be left, top, right, bottom fractions between 0 and 1.")
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("L")
    mask = Image.new("L", image.size, 255 if subject_outline is None else 0)
    if subject_outline is not None:
        ImageDraw.Draw(mask).polygon(
            [(round(x * image.width), round(y * image.height)) for x, y in subject_outline],
            fill=255,
        )
    if crop is not None:
        box = (round(crop[0] * image.width), round(crop[1] * image.height),
               round(crop[2] * image.width), round(crop[3] * image.height))
        image, mask = image.crop(box), mask.crop(box)
    image = ImageEnhance.Contrast(ImageOps.autocontrast(image)).enhance(1.6)
    # Dense characters describe dark hair/clothing; excluded background stays empty.
    image = Image.composite(ImageOps.invert(image), Image.new("L", image.size, 0), mask)
    # Fit to physical character proportions before compressing into text cells.
    image = ImageOps.fit(image, (columns, round(rows / CHARACTER_ASPECT)),
                         method=Image.Resampling.LANCZOS)
    image = image.resize((columns, rows), Image.Resampling.LANCZOS)
    indices = np.asarray(image, dtype=np.uint16) * (len(RAMP) - 1) // 255
    characters = np.array(list(RAMP))[indices]
    return ["".join(line) for line in characters]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photo", type=Path)
    parser.add_argument("--columns", type=int, default=55)
    parser.add_argument("--rows", type=int, default=30)
    parser.add_argument("--crop", type=float, nargs=4, metavar=("LEFT", "TOP", "RIGHT", "BOTTOM"))
    parser.add_argument("--profile", type=Path, help="Read crop and subject outline from profile JSON.")
    args = parser.parse_args()
    config = json.loads(args.profile.read_text()) if args.profile else {}
    print("\n".join(photo_to_ascii(args.photo, args.columns, args.rows,
                                  args.crop or config.get("crop"), config.get("subject_outline"))))


if __name__ == "__main__":
    main()
