Inset Special
=============

.. image:: https://user-images.githubusercontent.com/14288520/198552761-a6e9f488-d584-444c-935d-ea15c7ded82f.png
  :target: https://user-images.githubusercontent.com/14288520/198552761-a6e9f488-d584-444c-935d-ea15c7ded82f.png

Functionality
-------------

Make inset in polygons. Output inner and outer polygons separately.

Inputs
------

This node has the following inputs:

Base Meshes:

- **Vertices** - Vertices of objects

- **Polygons** - polygons of objects

Transformation definition. Vectorized for every polygon:

- **Inset** - Proportional offset values meaning 0 in the center and 1 in the edges.

- **Distance** - Offset distance along normal.

- **ignore** - mask of affected polygons

- **Make Inner** - Determine if inner face should be created

- **Custom Normals** - custom normals for inset displacement

- **Offset Matrix** - Matrix transformation for inset displacement (only if 'Offset Mode' is set to 'Matrix')

Options
-------

- **Offset Mode** - How to interpret inset distance:
  Center: Inset is measured as a proportion between the corners and the center of the polygon
  Sides: Inset is measured as a constant distance to the sides of the polygon
  Matrix: Inset is computed based on a offset Matrix

- **Proportional** - Multiply distance by polygon perimeter (only if 'Offset Mode' is set to 'Sides')

- **Concave Support** - Try to fix distances in concave polygons.
  Disclaimer: This node is will fail in polygons with the center of the polygon outside
  of itself. For a better concave support use 'Inset Faces' node, which is over
  10 times slower than this node but more robust.

- **Zero Mode** - How to handle faces with zero inset (only if 'Offset Mode' is set to 'Center'):
  Skip: Ignore this faces
  Fan: Merge the inset vertices into a single vertex

- **Implementation** - How inset is calculated.
  Numpy: Faster
  Mathutils: Slower (Legacy. Face order may differ with new implementation) 'Custom normals' and the last 4 outputs wont work


Outputs
-------

This node has the following outputs:

- **vertices**
- **polygons**
- **Ignored** - get polygons that have not been affected.
- **Inset** - get inner polygons.
- **Original Vert Idx** - the index of the original vertex. Can be used to pass
  Vertex Data to new vertices. In case of Zero inset in Fan mode the index of the
  new vertex will be the first index of the polygon
- **Original Face Idx** - the index of the original face. Can be used to pass Face Data to new faces
- **Pols Group** - Outputs a list to mask polygons from the modified mesh,
  0 = Original Polygon
  1 = Side polygon
  2 = Inset Polygon.
- **New Verts Mask** - Mask of the new vertices


Examples of usage
-----------------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/CAD/Inset_special/inset_special_example.png
  :alt: procedural_Inset_example_blender_sverchok_1.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/CAD/Inset_special/inset_special_example2.png
  :alt: procedural_Inset_example_blender_sverchok_2.png

Original Face idx and Original Vert Idx

.. image:: https://user-images.githubusercontent.com/10011941/115357139-9b846200-a1bc-11eb-9c32-529c820a1a36.png

Custom Normal Example

.. image:: https://user-images.githubusercontent.com/10011941/115118493-af08b080-9fa3-11eb-88a2-3252eea02a33.png

New verts mask used to bevel only inset vertices

.. image:: https://user-images.githubusercontent.com/10011941/115415530-46b20d00-a1f7-11eb-8d6f-48bcc941bcfd.png

Pol groups output to filter the output polygons

.. image:: https://user-images.githubusercontent.com/10011941/115419634-c7263d00-a1fa-11eb-8730-d6ca1dc5511b.png
