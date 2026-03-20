# TIFF Fixture Notes

## Compression and Readers

- The repository intentionally does not include `imagecodecs`.
- For compressed TIFF inputs such as LZW, PackBits, Deflate, and JPEG, prefer PIL for reading fixture data.
- Do not assume `tifffile.imread()` can read compressed TIFFs in this environment.
- PIL can also write compressed TIFF fixtures without adding extra dependencies.

## Assertions

- When PIL or `tifffile` promotes `int16` data during round trips, assert value preservation instead of exact dtype equality.
- For `retiff`, verify shape, values, and photometric interpretation first.

## Reproducibility

- Use deterministic random generators for synthetic image data.
- Keep fixture sizes just large enough to exercise the target TIFF feature unless a large-image case is the point of the test.
