# Livermore Computed Tomography Input Output software (LCTIO)

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

## License

SPDX-License-Identifier: BSD-3-Clause

See [LICENSE](LICENSE) for details.

LLNL-CODE-2015296
