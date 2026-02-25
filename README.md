# Livermore Computed Tomography Input Output software (LCTIO)

## Tools included

### Command line tools

* `retiff`

### Python package

* `lctio`

## Getting Started

Install the `lctio` Python package for command line tools and importable library modules.
You could download this repository, but if you are installing into a Python environment
with internet access, you can use the `pip` command to automatically download
the package from https://pypi.org/project/lctio/

Example:

    # Create and activate a Python virtual environment named "myvenv" (optional)
    python3 -m venv myvenv
    . myvenv/bin/activate
    python -m pip install --upgrade pip

    # Use `pip` to install the package from pypi.org
    pip install lctio

Command line help for the provided tools is available with the `--help` option.

    retiff --help

## Scope

The software includes code for Python, C/C++, and Java (and other languages, as needed) to support interoperability between tools and data formats commonly used for radiography and computed tomography at LLNL and elsewhere.

The software repository is a collection of file readers and writers, converters, visualization software plugins, and data validation tools, aimed at supporting users of LLNL NDE software and CT data.

In addition to industry-standard data formats, LLNL traditionally uses several less common formats that have been described in public documentation, but without supporting public software.

This is the first public release of reference software for the file formats and data structures described in LLNL-TM-684438, the LLNL CT Standard, version 2. Supported data formats from this standard include
* SDT/SPR
* SCT
* phantom description language
* bad pixel map
* spectrum data file

Software tools also help to apply specific metadata, schema, and workflow conventions for more general file formats such as TIFF, RAW, and HDF5.

Additional formats and protocols may be implemented, as needed, to support interoperability with common software such as ImageJ and Fiji, or conversion to and from file types, or other open data standards.

LLNL-specific data structures and file formats may be refined or updated in conjunction with updates to the LLNL CT Standard.

The object modeling language may be expanded as necessary to support conversion to and from other open 3D modeling standards, such as the STL format used in Computer Aided Design.

## Contributing

Getting Involved - Information about mailing lists or other ways users can connect with you and each other.
Instructions for how you’d like people to contribute to your code.

## License

SPDX-License-Identifier: BSD-3-Clause

See [LICENSE](LICENSE) for details.

LLNL-CODE-2015296
