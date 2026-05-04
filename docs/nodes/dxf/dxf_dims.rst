DXF Linear Dimensions
=====================

Functionality
-------------

Creates DXF linear dimension objects. Generates dimension lines with measurement text between two points.

Inputs
------

- Vertices A: Start points for dimensions
- Vertices B: End points for dimensions
- Color: Dimension color (RGB or integer DXF color)
- Metadata: Additional metadata for dimensions

Options
-------

- Line Type: DXF line type for dimension lines
- Line Weight: Line thickness for dimension lines
- Text Scale: Scale factor for dimension text
- Color: DXF color index (-4 to 255, -4 = ignore)

Outputs
-------

- DXF Objects: Dimension objects ready for export

Examples
--------

*Example of creating DXF linear dimensions node lauout*

.. image:: https://github.com/user-attachments/assets/ce68e990-2db5-4dab-8c58-310b02c394ee

*Example of created DXF linear dimensions in librecad*

.. image:: https://github.com/user-attachments/assets/6583e574-80ff-411c-a386-04b829fc72b9
