Vector Fractal
==============

.. image:: https://user-images.githubusercontent.com/14288520/189541357-ddf35d58-b09b-4d7c-b96d-77c755e972e2.png
  :target: https://user-images.githubusercontent.com/14288520/189541357-ddf35d58-b09b-4d7c-b96d-77c755e972e2.png

This fractal node takes a list of Vectors and outputs a list of equal length containing Floats in the range 0.0 to 1.0.

Inputs & Parameters
-------------------

+----------------+-------------------------------------------------------------------------+
| Parameters     | Description                                                             |
+================+=========================================================================+
| Noise Function | The node output only Scalar values                                      |
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
| Fractal Type   | Pick between several fractal types                                      |
|                |                                                                         |
|                | - Fractal                                                               |
|                | - MultiFractal                                                          |
|                | - Hetero terrain                                                        |
|                | - Ridged multi fractal                                                  |
|                | - Hybrid multi fractal                                                  |
+----------------+-------------------------------------------------------------------------+
| H_factor       | Accepts float values, they are hashed into *Integers* internally.       |
+----------------+-------------------------------------------------------------------------+
| Lacunarity     | Accepts float values                                                    |
+----------------+-------------------------------------------------------------------------+
| Octaves        | Accepts integers values                                                 |
+----------------+-------------------------------------------------------------------------+
| Offset         | Accepts float values                                                    |
+----------------+-------------------------------------------------------------------------+
| Gain           | Accepts float values                                                    |
+----------------+-------------------------------------------------------------------------+

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189541446-f587f199-02da-4ed2-b2cb-0ea72a3535e5.png
  :target: https://user-images.githubusercontent.com/14288520/189541446-f587f199-02da-4ed2-b2cb-0ea72a3535e5.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Selected Statistic: List->List Main-> :doc:`List Statistics </nodes/list_main/statistics>`
* Vector-> :doc:`Vector Rewire </nodes/vector/vector_rewire>`
* List->List Struct-> :doc:`List First & Last </nodes/list_struct/start_end>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

.. image:: https://user-images.githubusercontent.com/14288520/189541519-593b3653-95dc-41c9-89d4-ddc4f2be1cfe.gif
  :target: https://user-images.githubusercontent.com/14288520/189541519-593b3653-95dc-41c9-89d4-ddc4f2be1cfe.gif

Basic example with a Vector rewire node.

json file: https://gist.github.com/satabol/bda8eb2d753d19c08ab50261c4ab319b

Notes
-----

This documentation doesn't do the full world of fractals any justice, feel free to send us layouts that you've made which rely on this node.

Links
-----
Fractals description from wikipedia: https://en.wikipedia.org/wiki/Fractal

A very interesting resource is "the book of shaders", it's about shader programming but there is a very useful fractal paragraph:

http://thebookofshaders.com/13/ and on github repo: https://github.com/patriciogonzalezvivo/thebookofshaders/tree/master/13



.. _Noise: http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html
..
