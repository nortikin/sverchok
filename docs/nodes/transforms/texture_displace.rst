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
|                |                                                                         |
|                | - UV: Input a second set of verts to be the UV coordinates of           |
|                |   the mesh.                                                             |
|                | - Mesh Matrix: Matrix to mutiply the verts to get their UV coord.       |
|                | - Texture Matrix: Matrix of external object to set where in global      |
|                |   space is the origin location and rotation of texture.                 |
+----------------+-------------------------------------------------------------------------+
| Channel        | Color channel to use as base of the displacement                        |
|                | Offers: Red, Green, Blue, Hue, Saturation, Value, Alpha, RGB Average    |
|                | and Luminosity.                                                         |
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

Basic example

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_1.png

Multiple textures can be used with the hep of the Object ID selector:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_2.png

When joining the texture list (to be [[texture, texture,...],[texture,...],...]) multiple textures can be used with a single mesh. (The node will match one texture per vertex)

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_3.png

"Axis Scale out" with multiply the effect multiplying each displace vector component-wise

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_4.png

The Texture Matrix mode of "Texture Coordinates" will work as the Displace Modifier with the texture Coordinates set to Object

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_5.png

The Mesh Matrix mode of "Texture Coordinates" will work as the Displace Modifier with the texture Coordinates set to Global in which the Matrix is treated as the mesh matrix

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_6.png

The "UV" mode of "Texture Coordinates" will work as the Displace Modifier with the texture Coordinates set to UV in which the new set of vertices is used as the UV Coordinates of the first mesh

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_7.png

The node can use also "Image or Movie" textures

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_displace_sverchok_blender_example_8.png

One matrix per point can be passed if the matrix list is wrapped, note that the "Flat Output" checkbox of the matrix in is un-checked

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/texture_displace/texture_evaluate_sverchok_blender_example_9.png
