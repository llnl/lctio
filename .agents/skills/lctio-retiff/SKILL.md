---
name: lctio-retiff
description: Use when modifying or debugging lctio.retiff, TIFF rewrite behavior, or the retiff CLI.
---

# LCTIO Retiff

Use this skill when a task touches `src/lctio/retiff/` or the `retiff` command.

## Current Behavior

- `retiff` reads a TIFF file and rewrites it with simpler storage and minimal metadata.
- The tool preserves image shape, sample values, and photometric interpretation.
- The library entry point is `lctio.retiff.rewrite()`.
- The CLI entry point is `retiff`, defined in `pyproject.toml`.

## Important Constraints

- Only single-page TIFF files are supported. Multi-page input should raise an error.
- The project intentionally relies on PIL for broad TIFF read compatibility and `tifffile` for writing.
- The repository does not depend on `imagecodecs`.

## CLI Examples

- `retiff input.tif`
- `retiff input.tif -o output_dir/`
- `retiff *.tif -o simplified/`
- `retiff input.tif -v`
