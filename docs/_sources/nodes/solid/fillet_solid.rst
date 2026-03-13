Fillet Solid
============

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

Fillets (Rounds) edges of a solid.

Inputs
------

All inputs are vectorized and the data will be matched to the longest list

- Solids: Solids to perform the operation on.
- Radius Start: Fillet Radius at the beginning of the edge.
- Radius End: Fillet Radius at the beginning of the edge.
- Mask: mask to select the edges to fillet.


Outputs
-------

- Solid


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/fillet_solid/fillet_solid_blender_sverchok_example.png

Notes
-----

- The Fillet depends on the orientation of the edge.

- If Radius Start or Radius End are too big the node will became in Error state and will not perform the operation.
