Chamfer Solid
=============

Functionality
-------------

Chamfer edges of a solid.

Inputs
------

All inputs are vectorized and the data will be matched to the longest list

- Solids: Solids to chamfer.
- Distance A: Distance to chamfer from the edge in one of the faces. (Left side when looking from the origin to the end).
- Distance B: Distance to chamfer from the edge in one of the faces. (Right side when looking from the origin to the end).
- Mask: mask to select the edges to chamfer.


Outputs
-------

- Solid


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/chamfer_solid/chamfer_solid_blender_sverchok_example.png

Notes
-----

- The Distance A and Distance B depends on the orientation of the edge.

- If Distance A or Distance B are to big the node will became in Error state and will not perform the operation.
