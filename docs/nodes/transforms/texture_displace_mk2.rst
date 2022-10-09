Texture Displace
================

.. image:: https://user-images.githubusercontent.com/14288520/193805385-06b3f08e-e70f-45b3-ad19-fd1b0cf5c899.png
  :target: https://user-images.githubusercontent.com/14288520/193805385-06b3f08e-e70f-45b3-ad19-fd1b0cf5c899.png

This node displaces a list of Vectors using a texture.

Inputs & Parameters
-------------------

+----------------+-------------------------------------------------------------------------+
| Parameters     | Description                                                             |
+================+=========================================================================+
| Direction      | Displacement direction.                                                 |
|                | Available modes:                                                        |
|                |                                                                         |
|                | * Normal                                                                |
|                | * X, Y, Z                                                               |
|                | * Custom Axis                                                           |
|                | * RGB to XYZ                                                            |
|                | * HSV to XYZ                                                            |
|                | * HLV to XYZ                                                            |
+----------------+-------------------------------------------------------------------------+
| Texture Coord. | Modes to match vertices and texture:                                    |
|                |                                                                         |
|                | - UV: Input a second set of verts to be the UV coordinates of           |
|                |   the mesh.                                                             |
|                | - Mesh Matrix: Matrix to multiply the verts to get their UV coord.      |
|                | - Texture Matrix: Matrix of external object to set where in global      |
|                |                                                                         |
|                |   space is the origin location and rotation of texture.                 |
+----------------+-------------------------------------------------------------------------+
| Channel        | Color channel to use as base of the displacement                        |
|                | Offers:                                                                 |
|                |                                                                         |
|                | * Red                                                                   |
|                | * Green                                                                 |
|                | * Blue                                                                  |
|                | * Hue                                                                   |
|                | * Saturation                                                            |
|                | * Value                                                                 |
|                | * Alpha                                                                 |
|                | * RGB Average                                                           |
|                | * Luminosity                                                            |
|                |                                                                         |
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
|                |                                                                         |
|                | location and rotation of texture                                        |
+----------------+-------------------------------------------------------------------------+
| Middle Level   | Texture Evaluation - Middle Level = displacement                        |
+----------------+-------------------------------------------------------------------------+
| Strength       | Displacement multiplier                                                 |
+----------------+-------------------------------------------------------------------------+

Examples
--------

Basic example

.. image:: https://user-images.githubusercontent.com/14288520/193816365-4fa5d5f3-ec0d-4158-ac79-202c3f08c6e1.png
  :target: https://user-images.githubusercontent.com/14288520/193816365-4fa5d5f3-ec0d-4158-ac79-202c3f08c6e1.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Multiple textures can be used with the help of the Object ID selector:

.. image:: https://user-images.githubusercontent.com/14288520/193823844-5a8de042-ed06-4217-bfdb-2891c5022279.png
  :target: https://user-images.githubusercontent.com/14288520/193823844-5a8de042-ed06-4217-bfdb-2891c5022279.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* BPY Data-> :doc:`Object ID Selector+ </nodes/object_nodes/get_asset_properties_mk2>`

---------

When joining the texture list (to be [[texture, texture,...],[texture,...],...]) multiple textures can be used with a single mesh. (The node will match one texture per vertex)

.. image:: https://user-images.githubusercontent.com/14288520/193836932-9fd9a05c-7810-4f20-bd98-24fb6cb4de2c.png
  :target: https://user-images.githubusercontent.com/14288520/193836932-9fd9a05c-7810-4f20-bd98-24fb6cb4de2c.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzers-> :doc:`KDT Closest Verts </nodes/analyzer/kd_tree_MK2>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* BPY Data-> :doc:`Object ID Selector+ </nodes/object_nodes/get_asset_properties_mk2>`

---------

"Axis Scale out" with multiply the effect multiplying each displace vector component-wise

.. image:: https://user-images.githubusercontent.com/14288520/193890604-03357422-b94e-4679-ab34-95914b470ec6.png
  :target: https://user-images.githubusercontent.com/14288520/193890604-03357422-b94e-4679-ab34-95914b470ec6.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The Texture Matrix mode of "Texture Coordinates" will work as the Displace Modifier with the texture Coordinates set to Object

.. image:: https://user-images.githubusercontent.com/14288520/193892042-a9010802-1f28-46e5-97c9-48a8b6138e98.png
  :target: https://user-images.githubusercontent.com/14288520/193892042-a9010802-1f28-46e5-97c9-48a8b6138e98.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Matrix View </nodes/viz/vd_matrix>`

---------

The Mesh Matrix mode of "Texture Coordinates" will work as the Displace Modifier with the texture Coordinates set to Global in which the Matrix is treated as the mesh matrix

.. image:: https://user-images.githubusercontent.com/14288520/193893063-866e3aac-60b0-4ec4-95f9-fd5e14ddb596.png
  :target: https://user-images.githubusercontent.com/14288520/193893063-866e3aac-60b0-4ec4-95f9-fd5e14ddb596.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Matrix View </nodes/viz/vd_matrix>`

---------

The "UV" mode of "Texture Coordinates" will work as the Displace Modifier with the texture Coordinates set to UV in which the new set of vertices is used as the UV Coordinates of the first mesh

.. image:: https://user-images.githubusercontent.com/14288520/193893888-3b819d8a-2dad-4396-9c05-98d76134f63d.png
  :target: https://user-images.githubusercontent.com/14288520/193893888-3b819d8a-2dad-4396-9c05-98d76134f63d.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Matrix View </nodes/viz/vd_matrix>`

---------

The node can use also "Image or Movie" textures

.. image:: https://user-images.githubusercontent.com/14288520/193895318-2a1abba8-fa27-4cda-8901-8c69297012d1.png
  :target: https://user-images.githubusercontent.com/14288520/193895318-2a1abba8-fa27-4cda-8901-8c69297012d1.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Matrix View </nodes/viz/vd_matrix>`

---------

One matrix per point can be passed if the matrix list is wrapped, note that the "Flat Output" checkbox of the matrix in is un-checked

.. image:: https://user-images.githubusercontent.com/14288520/193901787-26d0aefe-e3c5-45a7-8df7-dee8ec8094da.png
  :target: https://user-images.githubusercontent.com/14288520/193901787-26d0aefe-e3c5-45a7-8df7-dee8ec8094da.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* LEN: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`