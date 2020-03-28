Noise Displace
==============

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
|                | Seed values of 0 will internally be replaced with a randomly picked     |
|                | constant to allow all seed input to generate repeatable output.         |
|                | (Seed=0 would otherwise generate random values based on system time)    |
+----------------+-------------------------------------------------------------------------+
| Scale Out      | Vector to multiply the added vector                                     |
+----------------+-------------------------------------------------------------------------+
| Noise Matrix   | Matrix input to determinate noise origin, scale and rotation            |
+----------------+-------------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**List Match**: Define how list with different lengths should be matched

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster with  Custom noises slower with Mathutils noises).

Examples
--------


.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noise_displace/noise_displace_blender_sverchok_example_1.png

Basic example


.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noise_displace/noise_displace_blender_sverchok_example_3.png

The node offers three ways of matching the list lengths "Repeat Last", "Cycle" and "Match Short" in this example "Cycle" is used to alternate the noise matrix

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noise_displace/noise_displace_blender_sverchok_example_5.png

In this example the scale output is used to blend with another oscillation texture

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noise_displace/noise_displace_blender_sverchok_example_6.png

The "Vector" Mode does not use vertex normals so it can be used just with vertices


.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noise_displace/noise_displace_blender_sverchok_example_7.png

The "Scale out" input can be used to mask the affected vertices


.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noise_displace/noise_displace_blender_sverchok_example_11.png

You can create many different outputs from one set of vertices if you input multiple seeds :

For the Mathutils Noises:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noise_displace/noise_displace_blender_sverchok_example_2.png

Seed and scale per vertex can be passed, in this example the seed is chosen by determining the closest point of another mesh and the scale is based on the distance to that point.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noise_displace/noise_displace_blender_sverchok_example_4.png

One matrix per point can be passed if the matrix list is wrapped, note that the "Flat Output" checkbox of the matrix in is un-checked

For the custom noises:


.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noise_displace/noise_displace_blender_sverchok_example_8.png

The custom noises will only allow one seed and matrix per object but they offer two different interpolations per noise to change the noise look.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noise_displace/noise_displace_blender_sverchok_example_9.png

Scale will be passed per vertex allowing different effects.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noise_displace/noise_displace_blender_sverchok_example_10.png

When interpolate is off there will be seams in the texture. As the seems are placed every unit with the use of the matrix can be used to produce hard edges.


.. _Noise: http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html
