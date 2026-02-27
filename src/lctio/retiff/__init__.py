"""Read the provided TIFF file, and rewrite with minimal complexity.

Replicate the shape, data type, and photometric interpretation of the input and
write a new TIFF with default (simple) data storage and minimal metadata.

This tool is part of the LCTIO project (LLNL-CODE-2015296): https://github.com/llnl/lctio
"""
import argparse
from pathlib import Path

from PIL import Image
import numpy as np
import tifffile
from tifffile import PHOTOMETRIC

parser = argparse.ArgumentParser(description="Simplify a TIFF file and rewrite")
parser.add_argument("infile", nargs="+", help="TIFF file to read")
parser.add_argument("-o", "--outdir", help="Output directory (optional, to avoid overwriting input files)")
parser.add_argument("-v", "--verbose", action="store_true")

def rewrite(infile: Path, outfile: Path, verbose:bool = False):
    # Check the PhotometricInterpretation so we can keep it consistent.
    with tifffile.TiffFile(infile) as tif:
        if len(tif.pages) != 1:
            raise RuntimeError("Only single-page TIFFs are supported at this time.")
        photometric = PHOTOMETRIC(tif.pages[0].photometric)
        if verbose:
            print("Input TIFF:")
            for page in tif.pages:
                for tag in page.tags:
                    tag_name, tag_value = tag.name, tag.value
                    print(f"{tag_name}: {tag_value}")

    # Let PIL take care of converting the image to a bitmap, regardless of layout or compression.
    with Image.open(infile) as pil_img:
        # Explicitly copy the PIL Image object to a NumPy array
        np_img = np.array(pil_img)

    tifffile.imwrite(outfile, np_img, photometric=photometric)
    if verbose:
        print("Output TIFF:")
        with tifffile.TiffFile(outfile) as tif:
            for page in tif.pages:
                for tag in page.tags:
                    tag_name, tag_value = tag.name, tag.value
                    print(f"{tag_name}: {tag_value}")

def main():
    args = parser.parse_args()
    if args.outdir:
        outdir = Path(args.outdir)
    else:
        outdir = None
    if outdir and not outdir.exists():
        raise RuntimeError(f"Output directory {outdir} does not exist.")

    for input in args.infile:
        infile = Path(input)
        if not infile.exists():
            raise RuntimeError(f"Cannot find input file {infile}")
        if outdir is None:
            outfile = infile
        else:
            outfile = outdir.joinpath(infile.name)

        rewrite(infile=infile, outfile=outfile, verbose=args.verbose)
