Variable Lacunarity
===================

.. image:: https://user-images.githubusercontent.com/14288520/189540443-c568ccaf-b714-4624-903b-ac7eeeb5c896.png
  :target: https://user-images.githubusercontent.com/14288520/189540443-c568ccaf-b714-4624-903b-ac7eeeb5c896.png

This node takes a list of Vectors and outputs a list of equal length containing Floats in the range -1.0 to 1.0.  
The seed value permits you to apply a different noise calculation to identical inputs.
This nodes "_returns variable lacunarity noise value, a distorted variety of noise,
from noise type 1 distorted by noise type 2 at the specified position."


Inputs & Parameters
-------------------

+----------------+-------------------------------------------------------------------------+
| Parameters     | Description                                                             |
+================+=========================================================================+
| **Noise Type** | Pick between several noise types                                        |
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
| **Seed**       | Accepts int values.                                                     |
+----------------+-------------------------------------------------------------------------+
| **Distortion** | Accepts floats values, modulate the two noise basis.                    |
+----------------+-------------------------------------------------------------------------+

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189540266-02370793-10f8-44e9-9545-ef43dae80987.png
  :target: https://user-images.githubusercontent.com/14288520/189540266-02370793-10f8-44e9-9545-ef43dae80987.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Vector-> :doc:`Vector Rewire </nodes/vector/vector_rewire>`
* Selected Statistics: List->List Main-> :doc:`List Statistics </nodes/list_main/statistics>`
* List->List Struct-> :doc:`List First & Last </nodes/list_struct/start_end>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`

Notes
-----

This documentation doesn't do the full world of noise any justice, feel free to send us layouts that you've made which rely on this node.



.. _Noise: http://www.blender.org/documentation/blender_python_api_current/mathutils.noise.html
