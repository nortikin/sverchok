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
|                | * Blender                                                               |
|                | * Cell Noise                                                            |
|                | * New Perlin                                                            |
|                | * Standard Perlin                                                       |
|                | * Voronoi Crackle                                                       |
|                | * Voronoi F1                                                            |
|                | * Voronoi F2                                                            |
|                | * Voronoi F2F1                                                          |
|                | * Voronoi F3                                                            |
|                | * Voronoi F4                                                            |
|                | See mathutils.noise docs ( _Noise )                                     |
+----------------+-------------------------------------------------------------------------+
| Seed           | Accepts float values, they are hashed into *Integers* internally.       |
|                | Seed values of 0 will internally be replaced with a randomly picked     |
|                | constant to allow all seed input to generate repeatable output.         |
|                | (Seed=0 would otherwise generate random values based on system time)    |
+----------------+-------------------------------------------------------------------------+


.. _Noise: http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html