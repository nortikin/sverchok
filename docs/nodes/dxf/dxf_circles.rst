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

*Default DXF linetypes*

.. image:: https://github.com/user-attachments/assets/1fe1e785-04fc-441c-b267-514538a53388

*Default DXF thicknesses*

.. image:: https://github.com/user-attachments/assets/aa8cd5af-a423-4a6d-8e01-54f32e7831ad

*Default DXF colors - use whether color in node or DXF index from table*

.. image:: https://github.com/user-attachments/assets/390e21c3-3f23-4766-bde1-5cb555b980c4
.. image:: https://github.com/user-attachments/assets/951d31c1-a2ad-4309-912e-61d230509ee5