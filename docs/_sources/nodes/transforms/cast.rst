Cast
====

.. image:: https://user-images.githubusercontent.com/14288520/194025745-6f3f8e0c-ef8d-41b5-a648-a3002d498ab7.png
  :target: https://user-images.githubusercontent.com/14288520/194025745-6f3f8e0c-ef8d-41b5-a648-a3002d498ab7.png

The Cast modifier shifts the shape of a mesh towards a predefined shape (sphere, cylinder, prism, UV Sphere).

Mimics and expands the Blender Cast Modifier (https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/cast.html).

The node accepts regular Python lists and Numpy Arrays. (Flat Arrays for scalars and two-axis arrays for vectors).

Inputs & Parameters
-------------------

+----------------+----------------------------------------------------------------------------------+
| Parameters     | Description                                                                      |
+================+==================================================================================+
| Shape          | Sphere, Cylinder, Prism, UV Sphere                                               |
+----------------+----------------------------------------------------------------------------------+
| Origin         | Determine where the origin of the shape should be:                               |
|                |                                                                                  |
|                | - Average: The center of the mesh will be in the mean of the inputted vertices   |
|                | - External: The center of the mesh will be taken from the origin input           |
+----------------+----------------------------------------------------------------------------------+
| Size           | Determine where the origin of the shape should be:                               |
|                |                                                                                  |
|                | - Average: The size of the mesh will be in the mean of the inputted vertices     |
|                | - External: The size of the mesh will be taken from the size input               |
+----------------+----------------------------------------------------------------------------------+

+----------------+-------------------------------------------------------------------------+
| Inputs         | Description                                                             |
+================+=========================================================================+
| Vertices       | Vertices of the mesh to cast                                            |
+----------------+-------------------------------------------------------------------------+
| Shape Scale    | Axis scaling of the base mesh                                           |
+----------------+-------------------------------------------------------------------------+
| Effect Scale   | Axis scaling of the displacement vector                                 |
+----------------+-------------------------------------------------------------------------+
| Origin         | Origin of the base mesh                                                 |
+----------------+-------------------------------------------------------------------------+
| Size           | Base size of the base mesh                                              |
+----------------+-------------------------------------------------------------------------+
| Strength       | Scalar scaling of the displacement vector                               |
+----------------+-------------------------------------------------------------------------+
| Meridians      | Horizontal divisions. If less than 2 it will be interpreted as circular |
+----------------+-------------------------------------------------------------------------+
| Parallels      | Vertical divisions. If less than 1 it will be interpreted as circular   |
+----------------+-------------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Output NumPy arrays in stead of regular lists (makes the node faster)

**List Match**: Define how list with different lengths should be matched

Examples
--------

Basic example

.. image:: https://user-images.githubusercontent.com/14288520/194028140-78483ea3-4234-46d6-ab79-a9f4aff06805.png
  :target: https://user-images.githubusercontent.com/14288520/194028140-78483ea3-4234-46d6-ab79-a9f4aff06805.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Cast a box to a octahedron:

.. image:: https://user-images.githubusercontent.com/14288520/194028531-ae35beeb-0f6b-48e0-b9a4-93a7b29d0880.png
  :target: https://user-images.githubusercontent.com/14288520/194028531-ae35beeb-0f6b-48e0-b9a4-93a7b29d0880.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Cast a UV Sphere to a pentagonal prism:

.. image:: https://user-images.githubusercontent.com/14288520/194029392-364622a0-a19f-4c52-9c1b-4fd521068c6a.png
  :target: https://user-images.githubusercontent.com/14288520/194029392-364622a0-a19f-4c52-9c1b-4fd521068c6a.png

* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`

---------

Casting Suzzane to different height prisms

.. image:: https://user-images.githubusercontent.com/14288520/194030634-d5a01d83-d901-461a-9d88-5814b56f1797.png
  :target: https://user-images.githubusercontent.com/14288520/194030634-d5a01d83-d901-461a-9d88-5814b56f1797.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

Casting a plane to a scaled sphere using external origin

.. image:: https://user-images.githubusercontent.com/14288520/194031922-fd4bf6a7-409f-49d8-a3e9-752612953297.png
  :target: https://user-images.githubusercontent.com/14288520/194031922-fd4bf6a7-409f-49d8-a3e9-752612953297.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Matrix View </nodes/viz/vd_matrix>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Multiple concatenation of casts

.. image:: https://user-images.githubusercontent.com/14288520/194033124-372627cb-c8c2-4163-80a2-7948c4003b87.png
  :target: https://user-images.githubusercontent.com/14288520/194033124-372627cb-c8c2-4163-80a2-7948c4003b87.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

All parameters are vectorized. In this example multiple origins are passed to the same shape

.. image:: https://user-images.githubusercontent.com/14288520/194034637-fd59829d-4e9a-4354-abb8-6fdc9e9199cc.png
  :target: https://user-images.githubusercontent.com/14288520/194034637-fd59829d-4e9a-4354-abb8-6fdc9e9199cc.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzers-> :doc:`KDT Closest Verts </nodes/analyzer/kd_tree_MK2>`
* ADD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

To get a tetrahedron Meridians:3 Parallels: 1.5 Shape scale: (1.08888, 1.08888, 0.8889)

.. image:: https://user-images.githubusercontent.com/14288520/194036065-57076049-4f34-4237-a0aa-d165b78bebb6.png
  :target: https://user-images.githubusercontent.com/14288520/194036065-57076049-4f34-4237-a0aa-d165b78bebb6.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`