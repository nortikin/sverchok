DXF Circles
===========

Functionality
-------------

Creates DXF circles objects from Sverchok geometry. Converts curves-circles into DXF circle entities.

Inputs
------

- Curves: Curves as SvCirvle objects expected
- Color: Line color (RGB or integer DXF color)
- Metadata: Additional metadata for lines

Options
-------

- Line Type: DXF line type (CONTINUOUS, DASHED, etc.)
- Line Weight: Line thickness
- Color: DXF color index (-4 to 255, -4 = ignore)

Outputs
-------

- DXF Objects: Circle objects ready for export

Examples
--------

*Example of creating DXF circles from curves SvCircles node lauout*

.. image:: https://github.com/user-attachments/assets/2ae8a0d1-61ac-4434-834d-68e44a285dd9

*Example of created DXF circles from curves SvCircles in zcad*

.. image:: https://github.com/user-attachments/assets/84c4fcb5-4255-4496-b304-b2709fd47168
