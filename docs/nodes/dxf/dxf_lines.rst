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

*Default DXF linetypes*

.. image:: https://github.com/user-attachments/assets/1fe1e785-04fc-441c-b267-514538a53388

*Default DXF thicknesses*

.. image:: https://github.com/user-attachments/assets/aa8cd5af-a423-4a6d-8e01-54f32e7831ad

*Default DXF colors - use whether color in node or DXF index from table*

.. image:: https://github.com/user-attachments/assets/390e21c3-3f23-4766-bde1-5cb555b980c4
.. image:: https://github.com/user-attachments/assets/951d31c1-a2ad-4309-912e-61d230509ee5