Vector Noise
============

.. image:: https://user-images.githubusercontent.com/14288520/189527778-9ece116a-6991-475e-b015-91aa5bbc6995.png
  :target: https://user-images.githubusercontent.com/14288520/189527778-9ece116a-6991-475e-b015-91aa5bbc6995.png

This noise node takes a list of Vectors and outputs a list of equal length containing either Vectors or Floats in the range 0.0 to 1.0.
The seed value permits you to apply a different noise calculation to identical inputs.

Inputs & Parameters
-------------------

+----------------+-------------------------------------------------------------------------+
| Parameters     | Description                                                             |
+================+=========================================================================+
| Noise Function | Pick between Scalar and Vector output                                   |
+----------------+-------------------------------------------------------------------------+
| Noise Type     | Pick between several noise types                                        |
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
|                |                                                                         |
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
| Noise Matrix   | Matrix input to determinate noise origin, scale and rotation.           |
|                |                                                                         |
|                | One matrix per point can be passed if the matrix list is wrapped        |
+----------------+-------------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster in Scalar mode and in Vector Mode with  Custom noises).

Examples
--------

Different noises
----------------

.. image:: https://user-images.githubusercontent.com/14288520/189527784-551b3af9-1143-4c19-9e63-2e68e04a6710.png
  :target: https://user-images.githubusercontent.com/14288520/189527784-551b3af9-1143-4c19-9e63-2e68e04a6710.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Selected Statistics: List->List Main-> :doc:`List Statistics </nodes/list_main/statistics>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

.. image:: https://user-images.githubusercontent.com/14288520/189527787-c03e8141-8050-4fd3-a514-4b121d1ae24f.png
  :target: https://user-images.githubusercontent.com/14288520/189527787-c03e8141-8050-4fd3-a514-4b121d1ae24f.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Selected Statistics: List->List Main-> :doc:`List Statistics </nodes/list_main/statistics>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

Using noise to mask a mesh
--------------------------

.. image:: https://user-images.githubusercontent.com/14288520/189533504-00a43a7f-3d60-4739-92d4-e5225dc4c779.png
  :target: https://user-images.githubusercontent.com/14288520/189533504-00a43a7f-3d60-4739-92d4-e5225dc4c779.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Modifiers->Modifier Change-> :doc:`Mask Vertices </nodes/modifier_change/vertices_mask>`
* Selected Statistics: List->List Main-> :doc:`List Statistics </nodes/list_main/statistics>`
* BIG: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

.. image:: https://user-images.githubusercontent.com/14288520/189533697-b8c2f6a0-3d9f-4375-a463-de84fa206f9a.gif
  :target: https://user-images.githubusercontent.com/14288520/189533697-b8c2f6a0-3d9f-4375-a463-de84fa206f9a.gif

Adding noise transformations
----------------------------

.. image:: https://user-images.githubusercontent.com/14288520/189527797-4a4f7c60-c3a6-4dfc-a1fc-69273a6a6d56.png
  :target: https://user-images.githubusercontent.com/14288520/189527797-4a4f7c60-c3a6-4dfc-a1fc-69273a6a6d56.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* A * SCALAR: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Add: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/189527806-4303cde4-86f5-4659-8ea8-a9ec2d8dd9de.gif
  :target: https://user-images.githubusercontent.com/14288520/189527806-4303cde4-86f5-4659-8ea8-a9ec2d8dd9de.gif

Using noise to filter a 3d grid
-------------------------------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/noise/noise_sverchok_blender_example_6.png 
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/noise/noise_sverchok_blender_example_6.png 

* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* DIV X,Y, MUL X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Sine Oscillator: Number-> :doc:`Oscillator </nodes/number/oscillator>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* LESS X, BIG X: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Scene-> :doc:`Frame Info </nodes/scene/frame_info_mk2>`
* Scene-> :doc:`Metaball Out Node (MB Alpha) </nodes/viz/viewer_metaball>`

Custom noises
-------------

**Random Cells**:

.. image:: https://user-images.githubusercontent.com/14288520/189531137-be65d761-6ee8-44c8-a24b-daf244530e28.png
  :target: https://user-images.githubusercontent.com/14288520/189531137-be65d761-6ee8-44c8-a24b-daf244530e28.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

**Random Gradients**:

.. image:: https://user-images.githubusercontent.com/14288520/189531146-73e1c8b0-653d-470e-bb6c-0485694cb357.png
  :target: https://user-images.githubusercontent.com/14288520/189531146-73e1c8b0-653d-470e-bb6c-0485694cb357.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

**Ortho Gradients**:

.. image:: https://user-images.githubusercontent.com/14288520/189531320-7001fc3f-fa1d-48b2-8a75-852458275776.png
  :target: https://user-images.githubusercontent.com/14288520/189531320-7001fc3f-fa1d-48b2-8a75-852458275776.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

**Numpy Perlin**:

.. image:: https://user-images.githubusercontent.com/14288520/189531160-e0b69fe0-4925-4261-9e3d-dc70618998bd.png
  :target: https://user-images.githubusercontent.com/14288520/189531160-e0b69fe0-4925-4261-9e3d-dc70618998bd.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

Notes
-----

This documentation doesn't do the full world of noise any justice, feel free to send us layouts that you've made which rely on this node.



.. _Noise: http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html
