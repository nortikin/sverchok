Solid Faces (Curves)
====================

Functionality
-------------

Gives the faces that define the solid as surfaces

Options
-------

**Flat Output**:  If the input has two solids the output will have two groups of surfaces. If Flat Output is enabled the two groups will be merged in a single group [[surface, surface,..], [surface, surface,...]] to [surface, surface, surface...]


Outputs
-------

**Solid Faces**: Surfaces that define a solid.

**Outer Wire**: The curves that limit that surfaces. One set of curves for each surface.

**TrimCurves**. Curves in face's U/V parameter space, that limit each face. One set of curves for each surface.


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/solid_faces/solid_faces_blender_sverchok_example.png
