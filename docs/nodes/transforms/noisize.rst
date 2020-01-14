Vector Noise
============

This noise node displaces a list of Vectors. The seed value permits you to apply a different noise calculation to identical inputs.

Inputs & Parameters
-------------------

+----------------+-------------------------------------------------------------------------+
| Parameters     | Description                                                             |
+================+=========================================================================+
| Mode           | Pick between Scalar along Normal and Vector output                      |
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

Examples
--------



.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noisize/noisize_blender_sverchok_example_1.png

Basic example

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noisize/noisize_blender_sverchok_example_2.png

Seed and scale per vertex can be passed, in this example the seed is chosen by determining the closest point of another mesh and the scale is based on the distance to that point

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noisize/noisize_blender_sverchok_example_4.png

One matrix per point can be passed if the matrix list is wrapped, note that the "Flat Output" checkbox of the matrix in is un-checked

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noisize/noisize_blender_sverchok_example_3.png

The node offers three ways of matching the list lengths "Repeat Last", "Cycle" and "Match Short" in this example "Cycle" is used to alternate the noise matrix

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noisize/noisize_blender_sverchok_example_5.png

In this example the scale output is used to blend with another oscillation texture

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noisize/noisize_blender_sverchok_example_6.png

The "Vector" Mode does not use vertex normals so it can be used just with verts

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/noisize/noisize_blender_sverchok_example_7.png

The "Scale out" input can be used to mask the affected vertices



.. _Noise: http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html
