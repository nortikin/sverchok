Vector Turbulence
=================

.. image:: https://user-images.githubusercontent.com/14288520/189534743-2d4cd1ab-0ebf-4637-b9ae-1744bde603a3.png
  :target: https://user-images.githubusercontent.com/14288520/189534743-2d4cd1ab-0ebf-4637-b9ae-1744bde603a3.png

This Vector Turbulence node takes a list of Vectors and outputs a list of equal length containing Floats in the range 0.0 to 1.0.
May output scalars or vectors.
For some noise types, if your output goes to the texture viewer you need to remap them, otherwise your texture
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
|                |                                                                         |
|                | The number of different noise frequencies used.                         |
+----------------+-------------------------------------------------------------------------+
| Hard           | Accepts bool values: Hard( True ) or Soft( False )                      |
|                |                                                                         |
|                | Specifies whether returned turbulence                                   |
|                |                                                                         |
|                | is hard (sharp transitions) or soft (smooth transitions).               |
+----------------+-------------------------------------------------------------------------+
| Amplitude      | Accepts float values. The amplitude scaling factor.                     |
+----------------+-------------------------------------------------------------------------+
| Frequency      | Accepts float values. The frequency scaling factor.                     |
+----------------+-------------------------------------------------------------------------+


Range table
-----------

Scalar values from turbulence node with size(n.verts)=64x64, step=0.05, octaves=3, amplitude=0.5, frequency=2.0, random seed=0.
Plug a map range node in the scalar output and map it to the desired range (min=0, max=1) as in the image below.

+----------------+----------------------+---------------------+----------------------+
|  Noise Type    |       median         |  maximum            |   minimum            |
+================+======================+=====================+======================+
| Blender        | 0.4574402868747711   | 1.2575798034667969  | 0.0                  |
+----------------+----------------------+---------------------+----------------------+
| Stdperlin      | 0.37063807249069214  | 0.972740530967712   | 0.0                  |
+----------------+----------------------+---------------------+----------------------+
| Newperlin      | 0.2982039898633957   | 0.7674642205238342  | 0.0                  |
+----------------+----------------------+---------------------+----------------------+
| Voronoi_F1     | 0.5178706049919128   | 1.184566617012024   | 0.016996487975120544 |
+----------------+----------------------+---------------------+----------------------+
| Voronoi_F2     | 0.9441720247268677   | 1.696974754333496   | 0.07561451196670532  |
+----------------+----------------------+---------------------+----------------------+
| Voronoi_F3     | 1.3248268961906433   | 2.267115831375122   | 0.24465730786323547  |
+----------------+----------------------+---------------------+----------------------+
| Voronoi_F4     | 1.6119314432144165   | 2.4261345863342285  | 0.7868537306785583   |
+----------------+----------------------+---------------------+----------------------+
| Voronoi_F1F2   | 1.0320665836334229   | 1.7262239456176758  | 0.06919857859611511  |
+----------------+----------------------+---------------------+----------------------+
| Voronoi_Crackle| 1.5918831825256348   | 1.75                | 0.12337762117385864  |
+----------------+----------------------+---------------------+----------------------+
| Cellnoise      | 0.9668738842010498   | 1.5000858306884766  | 0.1691771298646927   |
+----------------+----------------------+---------------------+----------------------+

.. image:: https://user-images.githubusercontent.com/14288520/189534748-aac04542-bb00-4ce8-b199-812150925285.png
  :target: https://user-images.githubusercontent.com/14288520/189534748-aac04542-bb00-4ce8-b199-812150925285.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189534901-110976a3-79ef-47b1-844f-9f1393838691.png
  :target: https://user-images.githubusercontent.com/14288520/189534901-110976a3-79ef-47b1-844f-9f1393838691.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Vector-> :doc:`Vector Rewire </nodes/vector/vector_rewire>`
* Selected Statistics: List->List Main-> :doc:`List Statistics </nodes/list_main/statistics>`
* List->List Struct-> :doc:`List First & Last </nodes/list_struct/start_end>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

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
