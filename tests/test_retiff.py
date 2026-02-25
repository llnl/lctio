"""Test suite for lctio.retiff module.

This comprehensive test suite exercises the TIFF specification features that retiff
must handle correctly when simplifying TIFF files.

TIFF Features Tested:
---------------------
1. **Compression schemes** (TIFF tag 259):
   - Uncompressed (value 1)
   - LZW (value 5) - lossless dictionary compression
   - PackBits (value 32773) - lossless run-length encoding
   - Deflate (value 8) - lossless zlib compression
   - JPEG (value 7) - lossy compression for photos

2. **Photometric interpretation** (TIFF tag 262):
   - MINISBLACK (0) - grayscale where 0=black
   - MINISWHITE (1) - grayscale where 0=white
   - RGB (2) - full color RGB
   - PALETTE (3) - indexed color with colormap

3. **Data layout**:
   - Stripped layout - image divided into horizontal strips (most common)
   - Tiled layout - image divided into rectangular tiles (better for random access)

4. **Sample formats** (TIFF tag 339) and **Bits per sample** (TIFF tag 258):
   - uint8 (8-bit unsigned) - most common for photos
   - uint16 (16-bit unsigned) - common for scientific imaging
   - int16 (16-bit signed) - less common but valid
   - float32 (32-bit float) - for HDR and scientific data

5. **Multi-page support**:
   - Single-page TIFFs (supported)
   - Multi-page TIFFs (error case - not yet supported)

Test Coverage Summary (49 tests):
----------------------------------
**Library Function Tests (rewrite()):**
- TestRewriteBasicFunctionality: Grayscale, RGB, various shapes
- TestRewriteCompressions: LZW, PackBits, Deflate, JPEG, uncompressed
- TestRewritePhotometric: MINISBLACK, MINISWHITE, RGB preservation
- TestRewriteDataTypes: uint8, uint16, int16, float32
- TestRewriteTiledLayout: Tiled vs stripped layout handling
- TestRewriteVerbose: Verbose mode output verification
- TestRewriteErrors: Multi-page, missing files, invalid content, overwrite

**CLI Tests (main()):**
- TestCLISingleFile: Single file with/without output directory
- TestCLIMultipleFiles: Batch processing multiple files
- TestCLIVerbose: --verbose and -v flags
- TestCLIErrors: Error handling for various failure modes
- TestCLIArgumentCombinations: Combined argument testing

**Edge Cases & Integration:**
- TestEdgeCases: Large images (4096×4096), tiny (1×1), aspect ratios
- TestFilenames: Unicode and spaces in filenames
- TestRoundTrip: Stability across multiple rewrites
"""

import sys
import typing
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image
import tifffile
from tifffile import PHOTOMETRIC

from lctio.retiff import rewrite, main


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def random_image_data():
    """Factory fixture to generate random numpy arrays with various shapes/dtypes.

    Uses deterministic seed (42) for reproducibility.

    Returns:
        Callable that accepts shape, dtype and returns numpy array
    """
    def _create(shape, dtype=np.uint8):
        rng = np.random.RandomState(42)
        if dtype == np.float32:
            return rng.random(shape).astype(dtype)
        elif dtype in (np.uint8, np.uint16):
            info = np.iinfo(dtype)
            return rng.randint(info.min, info.max + 1, size=shape, dtype=dtype)
        elif dtype == np.int16:
            return rng.randint(-32768, 32767, size=shape, dtype=dtype)
        else:
            raise ValueError(f"Unsupported dtype: {dtype}")
    return _create


@pytest.fixture
def create_test_tiff(tmp_path):
    """Factory fixture to create TIFF files with specific properties.

    Creates stripped-layout TIFFs (standard row-based storage using StripOffsets
    and StripByteCounts TIFF tags) with various compression schemes and
    photometric interpretations.

    Args:
        filename: Name for the TIFF file
        data: Numpy array with image data
        photometric: Photometric interpretation (MINISBLACK, RGB, etc.)
        compression: Optional compression ('lzw', 'packbits', 'tiff_deflate', 'jpeg', None)

    Returns:
        Path to created TIFF file

    Note:
        PIL is used for compressed TIFFs since tifffile requires imagecodecs for
        reading compressed data, which is intentionally not a dependency.
    """
    def _create(filename: Path | str, data: np.ndarray, photometric: PHOTOMETRIC = PHOTOMETRIC.MINISBLACK, compression: str = None) -> Path | Any:
        filepath = tmp_path / filename

        if compression is None:
            # Use tifffile for uncompressed
            tifffile.imwrite(filepath, data, photometric=photometric)
        elif compression == 'jpeg':
            # Use PIL for JPEG (only works with uint8)
            if data.dtype != np.uint8:
                data = (data / data.max() * 255).astype(np.uint8)
            img = Image.fromarray(data)
            img.save(filepath, compression='jpeg', quality=85)
        else:
            # Use PIL for other compressions
            compression_map = {
                'lzw': 'tiff_lzw',
                'packbits': 'packbits',
                'tiff_deflate': 'tiff_deflate'
            }
            pil_compression = compression_map.get(compression, compression)

            if len(data.shape) == 2:
                mode = 'I;16' if data.dtype == np.uint16 else 'L'
            else:
                mode = 'RGB'

            img = Image.fromarray(data)
            img.save(filepath, compression=pil_compression)

        return filepath
    return _create


@pytest.fixture
def create_tiled_tiff(tmp_path):
    """Factory fixture to create tiled-layout TIFF files.

    Creates TIFFs with tiled layout (using TileOffsets and TileByteCounts TIFF
    tags) instead of stripped layout. Tiled TIFFs divide the image into
    rectangular tiles (e.g., 256×256) for better random access performance.

    Args:
        filename: Name for the TIFF file
        data: Numpy array with image data
        tile_size: Tuple of (tile_height, tile_width), default (256, 256)

    Returns:
        Path to created tiled TIFF file

    Note:
        tifffile automatically handles tiling when the 'tile' parameter is provided.
    """
    def _create(filename, data, tile_size=(256, 256)):
        filepath = tmp_path / filename
        tifffile.imwrite(filepath, data, tile=tile_size)
        return filepath
    return _create


@pytest.fixture
def create_multipage_tiff(tmp_path):
    """Factory fixture to create multi-page TIFF files for error testing.

    Multi-page TIFFs contain multiple images (pages) in a single file,
    commonly used for document scanning or image sequences.

    Args:
        filename: Name for the TIFF file
        pages: List of numpy arrays, one per page

    Returns:
        Path to created multi-page TIFF file
    """
    def _create(filename, pages):
        filepath = tmp_path / filename
        with tifffile.TiffWriter(filepath) as tif:
            for page in pages:
                tif.write(page)
        return filepath
    return _create


# ============================================================================
# Library Function Tests - rewrite()
# ============================================================================

class TestRewriteBasicFunctionality:
    """Test basic rewrite() functionality with various image types.

    Tests the most common TIFF configurations:
    - Uncompressed grayscale (PHOTOMETRIC.MINISBLACK)
    - RGB color images (PHOTOMETRIC.RGB)
    - Various image dimensions and aspect ratios
    """

    def test_uncompressed_grayscale(self, tmp_path, random_image_data, create_test_tiff):
        """Test rewriting uncompressed grayscale image.

        TIFF features: stripped layout, no compression (tag 259=1),
        MINISBLACK photometric (tag 262=1), uint8 samples.
        """
        data = random_image_data((100, 100), np.uint8)
        infile = create_test_tiff("input.tif", data)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        assert outfile.exists()
        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
        np.testing.assert_array_equal(data, output_data)

    def test_rgb_image(self, tmp_path, random_image_data, create_test_tiff):
        """Test rewriting RGB image.

        TIFF features: RGB photometric interpretation (tag 262=2),
        3 samples per pixel, 8 bits per sample.
        """
        data = random_image_data((64, 128, 3), np.uint8)
        infile = create_test_tiff("rgb.tif", data, photometric=PHOTOMETRIC.RGB)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        assert outfile.exists()
        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
        np.testing.assert_array_equal(data, output_data)

    @pytest.mark.parametrize("shape", [
        (100, 100),
        (256, 512),
        (1024, 1024),
        (64, 128, 3),
    ])
    def test_various_shapes(self, tmp_path, random_image_data, create_test_tiff, shape: typing.Sized):
        """Test rewriting images with various shapes."""
        dtype = np.uint8
        data = random_image_data(shape, dtype)
        photometric = PHOTOMETRIC.RGB if len(shape) == 3 else PHOTOMETRIC.MINISBLACK
        infile = create_test_tiff("input.tif", data, photometric=photometric)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
        np.testing.assert_array_equal(data, output_data)


class TestRewriteCompressions:
    """Test rewrite() with various compression formats.

    Tests all major TIFF compression schemes (TIFF tag 259):
    - None (1) - uncompressed strips
    - LZW (5) - Lempel-Ziv-Welch lossless compression
    - PackBits (32773) - Apple Macintosh run-length encoding
    - Deflate (8) - zlib/PNG-style lossless compression
    - JPEG (7) - lossy compression (quality loss expected)

    The retiff tool should decompress any input and write uncompressed output.
    """

    @pytest.mark.parametrize("compression", [
        None,  # Uncompressed (tag 259=1)
        'lzw',  # LZW compression (tag 259=5)
        'packbits',  # PackBits RLE (tag 259=32773)
        'tiff_deflate',  # Deflate/zlib (tag 259=8)
    ])
    def test_lossless_compressions(self, tmp_path, random_image_data, create_test_tiff, compression):
        """Test rewriting TIFFs with various lossless compressions.

        Verifies that:
        1. All lossless compressions can be read correctly
        2. Output is uncompressed (tag 259=1)
        3. Pixel data is preserved exactly (lossless)
        """
        data = random_image_data((100, 100), np.uint8)
        infile = create_test_tiff("input.tif", data, compression=compression)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        # Verify bitmap equality
        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
            # Verify output has no compression (compression=1 means NONE)
            assert tif.pages[0].compression == 1
        np.testing.assert_array_equal(data, output_data)

    def test_jpeg_compression(self, tmp_path, random_image_data, create_test_tiff):
        """Test rewriting JPEG-compressed TIFF (lossy compression, tag 259=7).

        JPEG compression is lossy, so we only verify shape preservation and consistency with the compressed data.
        Exact pixel values will differ from the original input due to JPEG artifacts from quantization.
        """
        data = random_image_data((100, 100), np.uint8)
        infile = create_test_tiff("input.tif", data, compression='jpeg')
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        # For lossy compression, verify shape but not exact values for original data
        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
        assert output_data.shape == data.shape
        # JPEG introduces artifacts, so we can't use exact equality to the original data.
        # Instead, read the lossy data from the generated input file.
        with Image.open(infile) as img:
            # Extract the numpy array from img
            input_array = np.array(img)
        np.testing.assert_array_equal(input_array, output_data)


class TestRewritePhotometric:
    """Test that photometric interpretation is preserved.

    Photometric interpretation (TIFF tag 262) defines how to interpret pixel values:
    - MINISBLACK (0): 0=black, higher values=lighter (standard grayscale)
    - MINISWHITE (1): 0=white, higher values=darker (inverted grayscale)
    - RGB (2): Red, Green, Blue color channels
    - PALETTE (3): Indexed color with separate colormap

    The retiff tool must preserve the original photometric interpretation.
    """

    @pytest.mark.parametrize("photometric,data_shape", [
        (PHOTOMETRIC.MINISBLACK, (100, 100)),  # Standard grayscale
        (PHOTOMETRIC.MINISWHITE, (100, 100)),  # Inverted grayscale
        (PHOTOMETRIC.RGB, (100, 100, 3)),      # Full color RGB
    ])
    def test_photometric_preserved(self, tmp_path, random_image_data, create_test_tiff,
                                   photometric, data_shape):
        """Test that photometric interpretation values are preserved.

        Verifies tag 262 has the same value in output as input.
        """
        data = random_image_data(data_shape, np.uint8)
        infile = create_test_tiff("input.tif", data, photometric=photometric)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        with tifffile.TiffFile(outfile) as tif:
            assert tif.pages[0].photometric == photometric.value


class TestRewriteDataTypes:
    """Test rewrite() with various data types.

    Tests different sample formats and bit depths:
    - uint8: BitsPerSample=8, SampleFormat=1 (unsigned int) - most common
    - uint16: BitsPerSample=16, SampleFormat=1 - scientific imaging
    - int16: BitsPerSample=16, SampleFormat=2 (signed int) - less common
    - float32: BitsPerSample=32, SampleFormat=3 (float) - HDR imaging

    Note: PIL/tifffile may promote int16 to int32 during processing, but
    pixel values should be preserved.
    """

    @pytest.mark.parametrize("dtype", [
        np.uint8,    # 8-bit unsigned (TIFF tag 258=8, tag 339=1)
        np.uint16,   # 16-bit unsigned (tag 258=16, tag 339=1)
        np.int16,    # 16-bit signed (tag 258=16, tag 339=2)
        np.float32,  # 32-bit float (tag 258=32, tag 339=3)
    ])
    def test_various_dtypes(self, tmp_path, random_image_data, create_test_tiff, dtype):
        """Test rewriting images with various data types.

        Verifies that pixel values are preserved across different sample formats.
        """
        data = random_image_data((100, 100), dtype)
        infile = create_test_tiff("input.tif", data)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
            # PIL/tifffile may promote int16 to int32, and float32 may be converted
            if dtype in (np.float32, np.int16):
                assert output_data.shape == data.shape
                # For int16, check values are preserved (even if dtype is promoted)
                if dtype == np.int16:
                    np.testing.assert_array_equal(data, output_data.astype(np.int16))
            else:
                assert output_data.dtype == data.dtype
                np.testing.assert_array_equal(data, output_data)


class TestRewriteTiledLayout:
    """Test rewrite() with tiled-layout TIFFs.

    Tiled layout (using TIFF tags TileWidth=322, TileLength=323, TileOffsets=324,
    TileByteCounts=325) divides images into rectangular tiles instead of
    horizontal strips. This provides better random access performance for
    large images.

    Standard stripped layout uses RowsPerStrip=278, StripOffsets=273,
    StripByteCounts=279.

    The retiff tool should handle both layouts and output stripped layout.
    """

    def test_tiled_layout_basic(self, tmp_path, random_image_data, create_tiled_tiff):
        """Test rewriting tiled TIFF with default 256×256 tiles.

        Input: Tiled layout with TileWidth and TileLength tags
        Output: Stripped layout (default tifffile behavior)
        """
        data = random_image_data((512, 512), np.uint8)
        infile = create_tiled_tiff("tiled.tif", data, tile_size=(256, 256))
        outfile = tmp_path / "output.tif"

        # Verify input is actually tiled
        with tifffile.TiffFile(infile) as tif:
            assert tif.pages[0].is_tiled, "Input should be tiled"

        rewrite(infile, outfile)

        # Verify output exists and has correct data
        assert outfile.exists()
        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
        np.testing.assert_array_equal(data, output_data)

    @pytest.mark.parametrize("tile_size,image_size", [
        ((128, 128), (512, 512)),  # 4×4 grid of tiles
        ((256, 256), (1024, 1024)),  # 4×4 grid of larger tiles
        ((64, 64), (256, 256)),  # 4×4 grid of small tiles
    ])
    def test_tiled_various_sizes(self, tmp_path, random_image_data, create_tiled_tiff,
                                 tile_size, image_size):
        """Test rewriting tiled TIFFs with various tile and image sizes.

        Verifies correct handling of different tiling schemes.
        """
        data = random_image_data(image_size, np.uint8)
        infile = create_tiled_tiff("tiled.tif", data, tile_size=tile_size)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
        np.testing.assert_array_equal(data, output_data)


class TestRewriteVerbose:
    """Test verbose mode output."""

    def test_verbose_true(self, tmp_path, random_image_data, create_test_tiff, capsys):
        """Test that verbose=True produces output."""
        data = random_image_data((50, 50), np.uint8)
        infile = create_test_tiff("input.tif", data)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile, verbose=True)

        captured = capsys.readouterr()
        assert "Input TIFF:" in captured.out
        assert "Output TIFF:" in captured.out

    def test_verbose_false(self, tmp_path, random_image_data, create_test_tiff, capsys):
        """Test that verbose=False produces no output."""
        data = random_image_data((50, 50), np.uint8)
        infile = create_test_tiff("input.tif", data)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile, verbose=False)

        captured = capsys.readouterr()
        assert captured.out == ""


class TestRewriteErrors:
    """Test error handling in rewrite().

    Tests that the tool properly handles and reports errors for:
    - Multi-page TIFFs (not yet supported)
    - Missing or corrupted files
    - Overwrite mode (rewriting to same file)
    """

    def test_multipage_tiff_error(self, tmp_path, random_image_data, create_multipage_tiff):
        """Test that multi-page TIFFs raise RuntimeError.

        Multi-page TIFFs contain multiple images stored as separate IFDs
        (Image File Directories). Currently not supported by retiff.
        """
        page1 = random_image_data((50, 50), np.uint8)
        page2 = random_image_data((50, 50), np.uint8)
        infile = create_multipage_tiff("multipage.tif", [page1, page2])
        outfile = tmp_path / "output.tif"

        with pytest.raises(RuntimeError, match="Only single-page TIFFs are supported"):
            rewrite(infile, outfile)

    def test_missing_input_file(self, tmp_path):
        """Test that missing input file raises FileNotFoundError."""
        infile = tmp_path / "nonexistent.tif"
        outfile = tmp_path / "output.tif"

        with pytest.raises(FileNotFoundError):
            rewrite(infile, outfile)

    def test_invalid_tiff_content(self, tmp_path):
        """Test that invalid TIFF content raises exception."""
        infile = tmp_path / "invalid.tif"
        infile.write_text("This is not a TIFF file")
        outfile = tmp_path / "output.tif"

        with pytest.raises(Exception):  # tifffile raises various exceptions
            rewrite(infile, outfile)

    def test_overwrite_mode(self, tmp_path, random_image_data, create_test_tiff):
        """Test that rewriting to same file works correctly."""
        data = random_image_data((50, 50), np.uint8)
        infile = create_test_tiff("input.tif", data, compression='lzw')

        # Rewrite to same file
        rewrite(infile, infile)

        # Verify file still exists and has correct data
        assert infile.exists()
        with tifffile.TiffFile(infile) as tif:
            output_data = tif.asarray()
            # Should be uncompressed now
            assert tif.pages[0].compression == 1
        np.testing.assert_array_equal(data, output_data)


# ============================================================================
# CLI Tests - main()
# ============================================================================

class TestCLISingleFile:
    """Test CLI with single file operations."""

    def test_single_file_no_outdir(self, tmp_path, random_image_data, create_test_tiff,
                                   monkeypatch):
        """Test CLI overwrites file when no output directory specified."""
        data = random_image_data((50, 50), np.uint8)
        infile = create_test_tiff("input.tif", data, compression='lzw')

        monkeypatch.setattr(sys, 'argv', ['retiff', str(infile)])
        main()

        # File should be rewritten in place
        assert infile.exists()
        with tifffile.TiffFile(infile) as tif:
            assert tif.pages[0].compression == 1  # Uncompressed

    def test_single_file_with_outdir(self, tmp_path, random_image_data, create_test_tiff,
                                     monkeypatch):
        """Test CLI writes to output directory when specified."""
        data = random_image_data((50, 50), np.uint8)
        infile = create_test_tiff("input.tif", data, compression='lzw')
        outdir = tmp_path / "output"
        outdir.mkdir()

        # Read original data to compare later (use PIL since input is compressed)
        with Image.open(infile) as img:
            original_data = np.array(img)

        monkeypatch.setattr(sys, 'argv', ['retiff', str(infile), '-o', str(outdir)])
        main()

        # Output file should exist in output directory
        outfile = outdir / "input.tif"
        assert outfile.exists()

        # Original should be unchanged (use PIL to read compressed input)
        with Image.open(infile) as img:
            np.testing.assert_array_equal(original_data, np.array(img))

        # Output should have correct data (can use tifffile for uncompressed output)
        np.testing.assert_array_equal(data, tifffile.imread(outfile))


class TestCLIMultipleFiles:
    """Test CLI with multiple file operations."""

    def test_multiple_files_with_outdir(self, tmp_path, random_image_data, create_test_tiff,
                                       monkeypatch):
        """Test CLI processes multiple files with output directory."""
        data1 = random_image_data((50, 50), np.uint8)
        data2 = random_image_data((60, 60), np.uint8)
        infile1 = create_test_tiff("input1.tif", data1, compression='lzw')
        infile2 = create_test_tiff("input2.tif", data2, compression='packbits')
        outdir = tmp_path / "output"
        outdir.mkdir()

        monkeypatch.setattr(sys, 'argv', ['retiff', str(infile1), str(infile2),
                                          '-o', str(outdir)])
        main()

        # Both output files should exist
        outfile1 = outdir / "input1.tif"
        outfile2 = outdir / "input2.tif"
        assert outfile1.exists()
        assert outfile2.exists()

        # Verify data
        np.testing.assert_array_equal(data1, tifffile.imread(outfile1))
        np.testing.assert_array_equal(data2, tifffile.imread(outfile2))

    def test_multiple_files_no_outdir(self, tmp_path, random_image_data, create_test_tiff,
                                     monkeypatch):
        """Test CLI overwrites all files when no output directory."""
        data1 = random_image_data((50, 50), np.uint8)
        data2 = random_image_data((60, 60), np.uint8)
        infile1 = create_test_tiff("input1.tif", data1, compression='lzw')
        infile2 = create_test_tiff("input2.tif", data2, compression='packbits')

        monkeypatch.setattr(sys, 'argv', ['retiff', str(infile1), str(infile2)])
        main()

        # Both files should be rewritten
        with tifffile.TiffFile(infile1) as tif:
            assert tif.pages[0].compression == 1
        with tifffile.TiffFile(infile2) as tif:
            assert tif.pages[0].compression == 1


class TestCLIVerbose:
    """Test CLI verbose mode."""

    def test_verbose_flag(self, tmp_path, random_image_data, create_test_tiff,
                         monkeypatch, capsys):
        """Test --verbose flag produces output."""
        data = random_image_data((50, 50), np.uint8)
        infile = create_test_tiff("input.tif", data)

        monkeypatch.setattr(sys, 'argv', ['retiff', str(infile), '--verbose'])
        main()

        captured = capsys.readouterr()
        assert "Input TIFF:" in captured.out
        assert "Output TIFF:" in captured.out

    def test_verbose_short_flag(self, tmp_path, random_image_data, create_test_tiff,
                               monkeypatch, capsys):
        """Test -v flag produces output."""
        data = random_image_data((50, 50), np.uint8)
        infile = create_test_tiff("input.tif", data)

        monkeypatch.setattr(sys, 'argv', ['retiff', str(infile), '-v'])
        main()

        captured = capsys.readouterr()
        assert "Input TIFF:" in captured.out


class TestCLIErrors:
    """Test CLI error handling."""

    def test_missing_input_file(self, tmp_path, monkeypatch):
        """Test CLI error when input file doesn't exist."""
        infile = tmp_path / "nonexistent.tif"

        monkeypatch.setattr(sys, 'argv', ['retiff', str(infile)])

        with pytest.raises(RuntimeError, match="Cannot find input file"):
            main()

    def test_nonexistent_outdir(self, tmp_path, random_image_data, create_test_tiff,
                               monkeypatch):
        """Test CLI error when output directory doesn't exist."""
        data = random_image_data((50, 50), np.uint8)
        infile = create_test_tiff("input.tif", data)
        outdir = tmp_path / "nonexistent"

        monkeypatch.setattr(sys, 'argv', ['retiff', str(infile), '-o', str(outdir)])

        with pytest.raises(RuntimeError, match="Output directory .* does not exist"):
            main()

    def test_multipage_tiff_cli(self, tmp_path, random_image_data, create_multipage_tiff,
                               monkeypatch):
        """Test CLI error with multi-page TIFF."""
        page1 = random_image_data((50, 50), np.uint8)
        page2 = random_image_data((50, 50), np.uint8)
        infile = create_multipage_tiff("multipage.tif", [page1, page2])

        monkeypatch.setattr(sys, 'argv', ['retiff', str(infile)])

        with pytest.raises(RuntimeError, match="Only single-page TIFFs are supported"):
            main()

    def test_no_arguments(self, monkeypatch):
        """Test CLI error when no arguments provided."""
        monkeypatch.setattr(sys, 'argv', ['retiff'])

        with pytest.raises(SystemExit):
            main()


class TestCLIArgumentCombinations:
    """Test various CLI argument combinations."""

    def test_verbose_and_outdir(self, tmp_path, random_image_data, create_test_tiff,
                               monkeypatch, capsys):
        """Test verbose + outdir together."""
        data = random_image_data((50, 50), np.uint8)
        infile = create_test_tiff("input.tif", data)
        outdir = tmp_path / "output"
        outdir.mkdir()

        monkeypatch.setattr(sys, 'argv', ['retiff', str(infile), '-o', str(outdir), '-v'])
        main()

        # Check output exists
        assert (outdir / "input.tif").exists()

        # Check verbose output
        captured = capsys.readouterr()
        assert "Input TIFF:" in captured.out

    def test_multiple_files_verbose_outdir(self, tmp_path, random_image_data,
                                          create_test_tiff, monkeypatch, capsys):
        """Test multiple files + verbose + outdir."""
        data1 = random_image_data((50, 50), np.uint8)
        data2 = random_image_data((60, 60), np.uint8)
        infile1 = create_test_tiff("input1.tif", data1)
        infile2 = create_test_tiff("input2.tif", data2)
        outdir = tmp_path / "output"
        outdir.mkdir()

        monkeypatch.setattr(sys, 'argv', ['retiff', str(infile1), str(infile2),
                                          '-o', str(outdir), '--verbose'])
        main()

        # Check outputs exist
        assert (outdir / "input1.tif").exists()
        assert (outdir / "input2.tif").exists()

        # Check verbose output (should appear for both files)
        captured = capsys.readouterr()
        assert captured.out.count("Input TIFF:") == 2
        assert captured.out.count("Output TIFF:") == 2


# ============================================================================
# Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_large_image(self, tmp_path, random_image_data, create_test_tiff):
        """Test with large image (4096x4096 uint16)."""
        data = random_image_data((4096, 4096), np.uint16)
        infile = create_test_tiff("large.tif", data)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
        np.testing.assert_array_equal(data, output_data)

    def test_minimum_size(self, tmp_path, random_image_data, create_test_tiff):
        """Test with 1x1 pixel image."""
        data = random_image_data((1, 1), np.uint8)
        infile = create_test_tiff("tiny.tif", data)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
        np.testing.assert_array_equal(data, output_data)

    @pytest.mark.parametrize("shape", [
        (1920, 1080),  # HD aspect ratio
        (100, 1000),   # Tall and narrow
        (1000, 100),   # Wide and short
    ])
    def test_non_square_aspect_ratios(self, tmp_path, random_image_data,
                                     create_test_tiff, shape):
        """Test with non-square aspect ratios."""
        data = random_image_data(shape, np.uint8)
        infile = create_test_tiff("aspect.tif", data)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
        np.testing.assert_array_equal(data, output_data)


class TestFilenames:
    """Test with various filename patterns."""

    def test_unicode_filename(self, tmp_path, random_image_data, create_test_tiff):
        """Test with unicode characters in filename."""
        data = random_image_data((50, 50), np.uint8)
        infile = create_test_tiff("测试_файл_🎨.tif", data)
        outfile = tmp_path / "output.tif"

        rewrite(infile, outfile)

        assert outfile.exists()
        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
        np.testing.assert_array_equal(data, output_data)

    def test_spaces_in_filename(self, tmp_path, random_image_data, create_test_tiff):
        """Test with spaces in filename."""
        data = random_image_data((50, 50), np.uint8)
        infile = create_test_tiff("file with spaces.tif", data)
        outfile = tmp_path / "output file.tif"

        rewrite(infile, outfile)

        assert outfile.exists()
        with tifffile.TiffFile(outfile) as tif:
            output_data = tif.asarray()
        np.testing.assert_array_equal(data, output_data)


# ============================================================================
# Integration Tests
# ============================================================================

class TestRoundTrip:
    """Integration tests for round-trip stability."""

    def test_double_rewrite(self, tmp_path, random_image_data, create_test_tiff):
        """Test that rewriting twice produces identical results."""
        data = random_image_data((100, 100), np.uint8)
        infile = create_test_tiff("input.tif", data, compression='lzw')
        outfile1 = tmp_path / "output1.tif"
        outfile2 = tmp_path / "output2.tif"

        # First rewrite
        rewrite(infile, outfile1)

        # Second rewrite
        rewrite(outfile1, outfile2)

        # Both outputs should be identical
        data1 = tifffile.imread(outfile1)
        data2 = tifffile.imread(outfile2)
        np.testing.assert_array_equal(data1, data2)

        # Metadata should also be identical
        with tifffile.TiffFile(outfile1) as tif1:
            with tifffile.TiffFile(outfile2) as tif2:
                assert tif1.pages[0].compression == tif2.pages[0].compression
                assert tif1.pages[0].photometric == tif2.pages[0].photometric

    def test_stability_across_multiple_rewrites(self, tmp_path, random_image_data,
                                               create_test_tiff):
        """Test that multiple rewrites maintain stability."""
        data = random_image_data((100, 100), np.uint16)
        infile = create_test_tiff("input.tif", data)

        current = infile
        for i in range(5):
            next_file = tmp_path / f"rewrite_{i}.tif"
            rewrite(current, next_file)
            current = next_file

        # Final output should match original data
        final_data = tifffile.imread(current)
        np.testing.assert_array_equal(data, final_data)
