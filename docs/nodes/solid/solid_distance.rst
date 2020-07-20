Solid Distance
==============

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

The node returns the closest point to a vector that is over a solid surface. It will also accept "Solid Faces" and "Solid Edges"

Options
-------

**Mode**: Solid, Face or Edge

Inputs
------

All inputs are vectorized and the data will be matched to the longest list

- **Solid / Solid Face / Solid Edge**: Element to project points to.
- **Vertices**: Vertices to make the analysis over.

Outputs
-------

- **Distance**: Minimum distance between point and Element.
- **Closest Point**: Point in element where the distance is minimal
- **Info**: returns a triple per vector with:
  - Nearest topology item type (Face, Edge or Vertex)
  - Nearest topology item index
  - Nearest topology item parameter (UV coords for faces, U for edges and None for vertex)


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/points_inside_solid/points_inside_solid_blender_sverchok_example.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/points_inside_solid/points_inside_solid_blender_sverchok_example_01.png
