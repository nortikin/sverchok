Solid Distance
==============

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

The node returns a slice of the solid object.

Options
-------

**Flat Output**: If the input has two solids the output will have two groups of curves. If Flat Output is enabled the two groups will be merged in a single group [[curve, curve,..], [curve, curve,...]] to [curve, curve, curve...]

Inputs
------

All inputs are vectorized and the data will be matched to the longest list

- **Solid**: Object to slice
- **Matrix**: Cutting plane

Outputs
-------

- **Edges**: Edges (Curves) that define the slice.
- **Faces**: The slice as a Solid Face Surface.


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/slice_solid/slice_solid_blender_sverchok_example_00.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/slice_solid/slice_solid_blender_sverchok_example_01.png
