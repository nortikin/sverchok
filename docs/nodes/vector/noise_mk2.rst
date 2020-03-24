Vector Noise
============

This noise node takes a list of Vectors and outputs a list of equal length containing either Vectors or Floats in the range 0.0 to 1.0. The seed value permits you to apply a different noise calculation to identical inputs.

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
|                | Seed values of 0 will internally be replaced with a randomly picked     |
|                | constant to allow all seed input to generate repeatable output.         |
|                | (Seed=0 would otherwise generate random values based on system time)    |
+----------------+-------------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster in Scalar mode and in Vector Mode with  Custom noises).

Examples
--------

Different noises:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/noise/noise_sverchok_blender_example_1.png
.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/noise/noise_sverchok_blender_example_2.png

Using noise to mask a mesh:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/noise/noise_sverchok_blender_example_3.png

Adding noise transformations:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/noise/noise_sverchok_blender_example_4.png

Using noise to filter a 3d grid:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/noise/noise_sverchok_blender_example_6.png

Custom noises:

- Random Cells:
.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/noise/noise_sverchok_blender_example_5.png

- Random Gradients:
.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/noise/noise_sverchok_blender_example_7.png

-Ortho Gradients:
.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/noise/noise_sverchok_blender_example_8.png

- Numpy Perlin:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/vector/noise/noise_sverchok_blender_example_9.png

Notes
-----

This documentation doesn't do the full world of noise any justice, feel free to send us layouts that you've made which rely on this node.



.. _Noise: http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html
