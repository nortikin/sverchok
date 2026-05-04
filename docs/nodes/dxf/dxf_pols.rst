DXF Polygons
============

Functionality
-------------

Creates DXF polygon objects from Sverchok mesh data. Converts faces into DXF polygon entities.

Inputs
------

- Vertices: Base vertices for polygons
- Polygons: Face indices defining polygons
- Color: Polygon color (RGB or integer DXF color)
- Metadata: Additional metadata for polygons

Options
-------

- Line Type: DXF line type for polygon edges
- Line Weight: Line thickness for polygon edges
- Color: DXF color index (-4 to 255, -4 = ignore)

Outputs
-------

- DXF Objects: Polygon objects ready for export

Examples
--------

*Example of creating DXF polygons from mesh faces node lauout*

.. image:: https://github.com/user-attachments/assets/cc5565a1-8a9d-4124-9a80-b6ab0d88ef31

*Example of created DXF polygons from mesh faces in librecad*

.. image:: https://github.com/user-attachments/assets/229312b9-43cd-4ca9-a3f6-df80f0285743
