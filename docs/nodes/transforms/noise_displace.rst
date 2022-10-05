Noise Displace
==============

.. image:: https://user-images.githubusercontent.com/14288520/194018662-8f0712a7-c99b-4b89-b153-e52f25f8db1a.png
  :target: https://user-images.githubusercontent.com/14288520/194018662-8f0712a7-c99b-4b89-b153-e52f25f8db1a.png

This noise node displaces a list of Vectors. The seed value permits you to apply a different noise calculation to identical inputs.

Inputs & Parameters
-------------------

+----------------+-------------------------------------------------------------------------+
| Parameters     | Description                                                             |
+================+=========================================================================+
| Mode           | Pick between Scalar along Normal and Vector output                      |
+----------------+-------------------------------------------------------------------------+
| Noise Type     | Pick between several noise types                                        |
|                | Mathutils noise:                                                        |
|                |                                                                         |
|                | - Blender                                                               |
|                | - Cell Noise                                                            |
|                | - New Perlin                                                            |
|                | - Standard Perlin                                                       |
|                | - Voronoi Crackle                                                       |
|                | - Voronoi F1                                                            |
|                | - Voronoi F2                                                            |
|                | - Voronoi F2F1                                                          |
|                | - Voronoi F3                                                            |
|                | - Voronoi F4                                                            |
|                |                                                                         |
|                | See mathutils.noise docs ( Noise_ )                                     |
|                | Custom noises:                                                          |
|                |                                                                         |
|                | - Random Cells                                                          |
|                | - Random Gradients                                                      |
|                | - Ortho Gradients                                                       |
|                | - Numpy Perlin                                                          |
|                |                                                                         |
|                | (see examples)                                                          |
+----------------+-------------------------------------------------------------------------+
| Smooth         | Smooth curvature (Only for custom noises)                               |
+----------------+-------------------------------------------------------------------------+
| Interpolate    | Gradient interpolation (Hard noise when un-checked) (For custom noises) |
+----------------+-------------------------------------------------------------------------+
| Seed           | Accepts float values, they are hashed into *Integers* internally.       |
|                |                                                                         |
|                | Seed values of 0 will internally be replaced with a randomly picked     |
|                |                                                                         |
|                | constant to allow all seed input to generate repeatable output.         |
|                |                                                                         |
|                | (Seed=0 would otherwise generate random values based on system time)    |
+----------------+-------------------------------------------------------------------------+
| Scale Out      | Vector to multiply the added vector                                     |
+----------------+-------------------------------------------------------------------------+
| Noise Matrix   | Matrix input to determinate noise origin, scale and rotation            |
+----------------+-------------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **List Match**: Define how list with different lengths should be matched.
* **Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster with  Custom noises slower with Mathutils noises).

Examples
--------

Basic examples

.. image:: https://user-images.githubusercontent.com/14288520/193932023-e47580f7-32fe-4a6f-9a18-fbb7b1c97d51.png
  :target: https://user-images.githubusercontent.com/14288520/193932023-e47580f7-32fe-4a6f-9a18-fbb7b1c97d51.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The node offers three ways of matching the list lengths "Repeat Last", "Cycle" and "Match Short" in this example "Cycle" is used to alternate the noise matrix.

.. image:: https://user-images.githubusercontent.com/14288520/193934351-3cc2db8a-3ecd-4fe1-bae1-4471636c588a.png
  :target: https://user-images.githubusercontent.com/14288520/193934351-3cc2db8a-3ecd-4fe1-bae1-4471636c588a.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

In this example the scale output is used to blend with another oscillation texture.

.. image:: https://user-images.githubusercontent.com/14288520/193935291-72442116-db6b-4c7b-a377-75f9fc72a78e.png
  :target: https://user-images.githubusercontent.com/14288520/193935291-72442116-db6b-4c7b-a377-75f9fc72a78e.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Sine Oscillator: Number-> :doc:`Oscillator </nodes/number/oscillator>`
* LEN: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The "Vector" Mode does not use vertex normals so it can be used just with vertices.

.. image:: https://user-images.githubusercontent.com/14288520/193936218-3df28752-faea-49af-81e5-98f6bafdad2a.png
  :target: https://user-images.githubusercontent.com/14288520/193936218-3df28752-faea-49af-81e5-98f6bafdad2a.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The "Scale out" input can be used to mask the affected vertices.

.. image:: https://user-images.githubusercontent.com/14288520/193938564-1529f630-edec-403b-abb3-652c3598f082.png
  :target: https://user-images.githubusercontent.com/14288520/193938564-1529f630-edec-403b-abb3-652c3598f082.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Analyzers-> :doc:`Select Mesh Elements </nodes/analyzer/mesh_select_mk2>`
* Analyzers-> :doc:`Proportional Edit Falloff </nodes/analyzer/proportional>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* A*SCALAR: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/193938997-6f4fe0e8-8b09-48c4-8404-da4e80f73778.gif
  :target: https://user-images.githubusercontent.com/14288520/193938997-6f4fe0e8-8b09-48c4-8404-da4e80f73778.gif

---------

You can create many different outputs from one set of vertices if you input multiple seeds.

.. image:: https://user-images.githubusercontent.com/14288520/193941010-19f17070-a69a-4988-8492-fcde1d182bf4.png
  :target: https://user-images.githubusercontent.com/14288520/193941010-19f17070-a69a-4988-8492-fcde1d182bf4.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

For the Mathutils Noises:

Seed and scale per vertex can be passed, in this example the seed is chosen by determining the closest point of another mesh and the scale is based on the distance to that point.

.. image:: https://user-images.githubusercontent.com/14288520/193999641-adb31774-0c64-4189-86b6-cb9ff14f6db1.png
  :target: https://user-images.githubusercontent.com/14288520/193999641-adb31774-0c64-4189-86b6-cb9ff14f6db1.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzers-> :doc:`KDT Closest Verts </nodes/analyzer/kd_tree_MK2>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

One matrix per point can be passed if the matrix list is wrapped, note that the "Flat Output" checkbox of the matrix in is un-checked.

.. image:: https://user-images.githubusercontent.com/14288520/194005731-202c3977-8336-4b06-bf87-3af125198fe8.png
  :target: https://user-images.githubusercontent.com/14288520/194005731-202c3977-8336-4b06-bf87-3af125198fe8.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* MUL X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* LEN: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Vector-> :doc:`Vector Lerp </nodes/vector/lerp>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Normalize: List-> :doc:`List Modifier </nodes/list_mutators/modifier>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

For the custom noises:

The custom noises will only allow one seed and matrix per object but they offer two different interpolations per noise to change the noise look.

.. image:: https://user-images.githubusercontent.com/14288520/194007831-a0f7a92c-a8f4-4e78-a9a3-3d17768e1a83.png
  :target: https://user-images.githubusercontent.com/14288520/194007831-a0f7a92c-a8f4-4e78-a9a3-3d17768e1a83.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Scale will be passed per vertex allowing different effects.

.. image:: https://user-images.githubusercontent.com/14288520/194008809-3e2eb485-8b8f-4913-9c0d-8c5d401218c9.png
  :target: https://user-images.githubusercontent.com/14288520/194008809-3e2eb485-8b8f-4913-9c0d-8c5d401218c9.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Square Oscillator: Number-> :doc:`Oscillator </nodes/number/oscillator>`
* LEN: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

When interpolate is off there will be seams in the texture. As the seems are placed every unit with the use of the matrix can be used to produce hard edges.

.. image:: https://user-images.githubusercontent.com/14288520/194010027-e1b019ba-0450-41dd-b86d-af2c83d3086d.png
  :target: https://user-images.githubusercontent.com/14288520/194010027-e1b019ba-0450-41dd-b86d-af2c83d3086d.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`

.. _Noise: http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html
