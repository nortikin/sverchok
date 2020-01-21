Texture Displace
================

This node displaces a list of Vectors using a texture.

Inputs & Parameters
-------------------

+----------------+-------------------------------------------------------------------------+
| Parameters     | Description                                                             |
+================+=========================================================================+
| Direction      | Displacement direction.                                                 |
|                | Available modes: Normal, X, Y, Z, Custom Axis, RGB to XYZ, HSV to XYZ   |
|                | and HLV to XYZ.                                                         |
+----------------+-------------------------------------------------------------------------+
| Texture Coord. | Modes to match vertices and texture:                                    |
|                | - UV Coords: Input a second set of verts to be the UV coordinates of    |
|                | the mesh                                                                |
|                | - Mesh Matrix: Matrix to mutiply the verts to get their UV coord.       |
|                | - Texture Matrix: Matrix of external object to set where in global      |
|                | space is the origin location and rotation of texture                    |
+----------------+-------------------------------------------------------------------------+
| Channel        | Color channel to use as base of the displacement                        |
|                | Offers: Red, Green, Blue, Hue, Saturation, Value, Alpha, RGB Average    |
|                | and Luminosity.                                   |
|                | Only in Normal, X, Y, Z, Custom Axis.                                   |
+----------------+-------------------------------------------------------------------------+
| Vertices       | Vertices of the mesh to displace                                        |
+----------------+-------------------------------------------------------------------------+
| Polygons       | Polygons of the mesh to displace                                        |
+----------------+-------------------------------------------------------------------------+
| Texture        | Texture(s) to use as base                                               |
+----------------+-------------------------------------------------------------------------+
| Scale Out      | Vector to multiply the added vector                                     |
+----------------+-------------------------------------------------------------------------+
| UV Coordinates | Second set of vertices to be the UV coordinates of the mesh             |
+----------------+-------------------------------------------------------------------------+
| Mesh Matrix    | Matrix to multiply the vertices to get their UV coordinates             |
+----------------+-------------------------------------------------------------------------+
| Texture Matrix | Matrix of external object to set where in global space is the origin    |
|                | location and rotation of texture                                        |
+----------------+-------------------------------------------------------------------------+
| Middle Level   | Texture Evaluation - Middle Level = displacement                        |
+----------------+-------------------------------------------------------------------------+
| Strength       | Displacement multiplier                                                 |
+----------------+-------------------------------------------------------------------------+

Examples
--------



.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_1.png

Basic example

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_2.png

Seed and scale per vertex can be passed, in this example the seed is chosen by determining the closest point of another mesh and the scale is based on the distance to that point

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_3.png

One matrix per point can be passed if the matrix list is wrapped, note that the "Flat Output" checkbox of the matrix in is un-checked

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_4.png

The node offers three ways of matching the list lengths "Repeat Last", "Cycle" and "Match Short" in this example "Cycle" is used to alternate the noise matrix

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_5.png

In this example the scale output is used to blend with another oscillation texture

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_5.png

The "Vector" Mode does not use vertex normals so it can be used just with vertices

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_6.png

The "Scale out" input can be used to mask the affected vertices

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_7.png

The "Scale out" input can be used to mask the affected vertices

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_8.png

The "Scale out" input can be used to mask the affected vertices



.. _Noise: http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html
