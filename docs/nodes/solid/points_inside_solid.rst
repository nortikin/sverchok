Points inside Solid
===================

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

The node returns splits a point list by separating the ones that are inside a solid object from the verts that are outside.

Inputs
------

All inputs are vectorized and the data will be matched to the longest list

- **Solid**: Solid to use as limit
- **Vertices**: Vertices to make the analysis over.

Options
-------

- **Tolerance**: Numerical tolerance determining if they are inside or outside the solid.
- **Accept in Surface**: Determine if the points over the solid surface should be considered as inside (if Enabled) or outside (if disabled).

Outputs
-------

- **Mask**, **Inside Vertices** and **Outside Vertices**


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/points_inside_solid/points_inside_solid_blender_sverchok_example.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/points_inside_solid/points_inside_solid_blender_sverchok_example_01.png
