"""Convert a photo to a contrast-boosted, aspect-correct ASCII portrait."""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageOps


RAMP = " .:-=+*#%@"
CHARACTER_ASPECT = 0.5


def photo_to_ascii(path, columns=55, rows=30, crop=None):
    """Return fixed-width lines; crop coordinates are fractions of the image."""
    if columns < 1 or rows < 1:
        raise ValueError("Columns and rows must be positive.")
    if crop is not None and not (len(crop) == 4 and
                                0 <= crop[0] < crop[2] <= 1 and
                                0 <= crop[1] < crop[3] <= 1):
        raise ValueError("Crop must be left, top, right, bottom fractions between 0 and 1.")
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source).convert("L")
    if crop is not None:
        image = image.crop((round(crop[0] * image.width), round(crop[1] * image.height),
                            round(crop[2] * image.width), round(crop[3] * image.height)))
    image = ImageEnhance.Contrast(ImageOps.autocontrast(image)).enhance(1.6)
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
    args = parser.parse_args()
    print("\n".join(photo_to_ascii(args.photo, args.columns, args.rows, args.crop)))


if __name__ == "__main__":
    main()
