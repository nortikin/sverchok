Solid Distance
==============

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

The node returns the distance between a Solid, a solid Face or a solid Edge to another Solid (or solid face, solid edge or vertex).

It will also return which is the closest point between the selected objects and information about where this closest point is.


Options
-------

**From**: Solid, Solid Face or Solid Edge

**To**: Solid, Solid Face, Solid Edge or Vertex

Inputs
------

All inputs are vectorized and the data will be matched to the longest list

- **Solid / Solid Face / Solid Edge**: First element
- **Solid / Solid Face / Solid Edge / Vertices**: Second element

Outputs
-------

- **Distance**: Minimum distance.
- **Closest Point A and B**: Points in element where the distance is minimal
- **Info A and B**: Returns a triple per element with:
  - Nearest topology item type (Face, Edge or Vertex)
  - Nearest topology item index
  - Nearest topology item parameter (UV coordinates for faces, T for edges and None for vertex)


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/solid_distance/solid_distance_blender_sverchok_example_00.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/solid_distance/solid_distance_blender_sverchok_example_01.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/solid_distance/solid_distance_blender_sverchok_example_03.png
