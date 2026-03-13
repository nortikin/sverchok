DXF Hatches
===========

Functionality
-------------

Creates DXF hatch patterns from Sverchok geometry. Generates hatched fill patterns for closed polygons.

Inputs
------

- Vertices: Base vertices for hatch boundaries
- Polygons: Face indices defining hatch boundaries
- Color: Hatch color (RGB or integer DXF color)
- Metadata: Additional metadata for hatches

Options
-------

- Pattern: Hatch pattern type (ANSI31, ANSI32, etc.)
- Hatch Scale: Scale factor for hatch pattern density
- Color: DXF color index (-4 to 255, -4 = ignore)

Outputs
-------

- DXF Objects: Hatch objects ready for export

Examples
--------

*Example of creating DXF hatches with different patterns node lauout*

.. image:: https://github.com/user-attachments/assets/17806ef6-2e3f-4a04-afe2-4aa9b526e045

*Example of created DXF hatches with different patterns in librecad*

.. image:: https://github.com/user-attachments/assets/3757c47b-cd9e-4b96-9cd2-4f37cf9a73a0

*Standart DXF hatches available from sverchok node*

.. image:: https://github.com/user-attachments/assets/c5dbb1f2-986c-44a1-9df8-fa9a679ea835

*Default DXF colors - use whether color in node or DXF index from table*

.. image:: https://github.com/user-attachments/assets/390e21c3-3f23-4766-bde1-5cb555b980c4
.. image:: https://github.com/user-attachments/assets/951d31c1-a2ad-4309-912e-61d230509ee5