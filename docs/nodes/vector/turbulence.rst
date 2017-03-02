Turbulence
==========

This Turbulence node takes a list of Vectors and outputs a list of equal length containing Floats in the range 0.0 to 1.0.
May output scalars o vectors.
For some noise types, if your output goes to the texture viewer you need to remap them, otherwise in same cases your texture
will be supersaturated or undersaturated. See below 'range table' for a detailed description.


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
+----------------+-------------------------------------------------------------------------+
| Octaves        | Accepts integers values                                                 |
|                | The number of different noise frequencies used.                         |
+----------------+-------------------------------------------------------------------------+
| Hard           | Accepts bool values: Hard( True ) or Soft( False )                      |
|                | Specifies whether returned turbulence                                   |
|                | is hard (sharp transitions) or soft (smooth transitions).               |
+----------------+-------------------------------------------------------------------------+
| Amplitude      | Accepts float values. The amplitude scaling factor.                     |
+----------------+-------------------------------------------------------------------------+
| Frequency      | Accepts float values. The frequency scaling factor.                     |
+----------------+-------------------------------------------------------------------------+

Range table
-----------
to do...soon


Examples
--------
.. image:: https://cloud.githubusercontent.com/assets/1275858/22593143/744dbdae-ea1d-11e6-8945-16a8be9f597c.png

Basic example with a Scalar output and Vector rewire node.


Notes
-----

This documentation doesn't do the full world of fractals any justice, feel free to send us layouts that you've made which rely on this node.

Links
-----
Fractals description from wikipedia: https://en.wikipedia.org/wiki/Fractal

A Perlin Noise and Turbulence description by Prof. Paul Bourke: http://paulbourke.net/texture_colour/perlin/

An introduction on Noise and Turbulence by Dr. Matthew O. Ward:  https://web.cs.wpi.edu/~matt/courses/cs563/talks/noise/noise.html

A very interesting resource is "the book of shaders", it's about shader programming but there is a very useful fractal paragraph:

http://thebookofshaders.com/13/ and on github repo: https://github.com/patriciogonzalezvivo/thebookofshaders/tree/master/13



.. _Noise: http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html
..
