DXF Lines
=========

Functionality
-------------

Creates DXF line objects from Sverchok geometry. Converts edges and vertices into DXF line entities.

Inputs
------

- Vertices: Base vertices for lines
- Edges: Edge indices defining line segments
- Color: Line color (RGB or integer DXF color)
- Metadata: Additional metadata for lines

Options
-------

- Line Type: DXF line type (CONTINUOUS, DASHED, etc.)
- Line Weight: Line thickness
- Color: DXF color index (-4 to 255, -4 = ignore)

Outputs
-------

- DXF Objects: Line objects ready for export

Examples
--------

*Example of creating DXF lines from mesh edges node lauout*

.. image:: https://github.com/user-attachments/assets/31b39074-2884-4504-be84-3e963a0bd4bb

*Example of created DXF lines from mesh edges in librecad*

.. image:: https://github.com/user-attachments/assets/ff02681a-2dbf-41ac-90d0-245a5585f48b