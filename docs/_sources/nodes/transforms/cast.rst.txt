Cast
====

The Cast modifier shifts the shape of a mesh towards a predefined shape (sphere, cylinder, prism, UV Sphere).

Mimics and expands the Blender Cast Modifier (https://docs.blender.org/manual/en/latest/modeling/modifiers/deform/cast.html).

The node accepts regular Python lists and Numpy Arrays. (Flat Arrays for scalars and two-axis arrays for vectors).

Inputs & Parameters
-------------------

+----------------+-------------------------------------------------------------------------+
| Parameters     | Description                                                             |
+================+=========================================================================+
| Shape          | Sphere, Cylinder, Prism, UV Sphere                                      |
+----------------+-------------------------------------------------------------------------+
| Origin         | Determine where the origin of the shape should be:                      |
|                |                                                                         |
|                | - Average: The center of the mesh will be in the mean of the inputted   |
|                |   vertices.                                                             |
|                | - External: The center of the mesh will be taken from the origin input. |
+----------------+-------------------------------------------------------------------------+
| Size           | Determine where the origin of the shape should be:                      |
|                | - Average: The size of the mesh will be in the mean of the inputted     |
|                | vertices.                                                               |
|                | - External: The size of the mesh will be taken from the size input.     |
+----------------+-------------------------------------------------------------------------+

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

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/cast/cast_to_sphere_sverchok_blender_example_1.png

Cast a box to a octahedron:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/cast/cast_to_octahedron_sverchok_blender_example_1.png

Cast a UV Sphere to a pentagonal prism:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/cast/cast_to_prism_sverchok_blender_example_1.png

Casting Suzzane to different height prisms

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/cast/cast_to_prism_sverchok_blender_example_shape_scale.png

Casting a plane to a scaled sphere using external origin

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/cast/cast_to_sphere_sverchok_blender_example_external_origin_shape_scale.png

Multiple concatenation of casts

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/cast/cast_to_sphere_sverchok_blender_example_external_origin_shape_scale_2.png

All parameters are vectorized. In this example multiple origins are passed to the same shape

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/cast/cast_to_sphere_sverchok_blender_example_multiple_origin_shape_scale.png

To get a tetrahedron Meridians:3 Parallels: 1.5 Shape scale: (1.08888, 1.08888, 0.8889)

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/cast/cast_to_tetrahedron_sverchok_blender_example_1.png
