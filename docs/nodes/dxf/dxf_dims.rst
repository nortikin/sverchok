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

*Default DXF linetypes*

.. image:: https://github.com/user-attachments/assets/1fe1e785-04fc-441c-b267-514538a53388

*Default DXF thicknesses*

.. image:: https://github.com/user-attachments/assets/aa8cd5af-a423-4a6d-8e01-54f32e7831ad

*Default DXF colors - use whether color in node or DXF index from table*

.. image:: https://github.com/user-attachments/assets/390e21c3-3f23-4766-bde1-5cb555b980c4
.. image:: https://github.com/user-attachments/assets/951d31c1-a2ad-4309-912e-61d230509ee5