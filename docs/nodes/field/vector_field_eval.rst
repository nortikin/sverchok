Evaluate Vector Field
=====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/11055b4a-b9c1-406d-9c56-c7c7054b6d9b
  :target: https://github.com/nortikin/sverchok/assets/14288520/11055b4a-b9c1-406d-9c56-c7c7054b6d9b

Functionality
-------------

This node calculates the values of the provided Vector Field at the given
points. More precisely, given the field VF (which is a function from vectors to
vectors), and point X, it calculates the vector VF(X).

.. image:: https://github.com/nortikin/sverchok/assets/14288520/3b015573-a8c3-4724-8c32-396169b70eb8
  :target: https://github.com/nortikin/sverchok/assets/14288520/3b015573-a8c3-4724-8c32-396169b70eb8

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5b6ebc53-29a8-46d2-9698-03c15bc98cd0
  :target: https://github.com/nortikin/sverchok/assets/14288520/5b6ebc53-29a8-46d2-9698-03c15bc98cd0

Inputs
------

This node has the following inputs:

* **Field**. The vector field to be evaluated. This input is mandatory.
* **Vertices**. The points at which to evaluate the field. The default value is `(0, 0, 0)`.

Parameters
----------

* **Output NumPy**. Outputs NumPy arrays in stead of regular python lists. Improves performance

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/84b5166d-092f-4ff3-8802-a2da38f4b25d
      :target: https://github.com/nortikin/sverchok/assets/14288520/84b5166d-092f-4ff3-8802-a2da38f4b25d

    * Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Outputs
-------

This node has the following output:

* **Vectors**. The vectors calculated at the provided points.

Performance Notes
-----------------

This node works faster when the vertices list are NumPy Arrays

Examples of usage
-----------------

Example of description:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ba8e4458-cc1a-444b-b1ef-413ea28b89a7
  :target: https://github.com/nortikin/sverchok/assets/14288520/ba8e4458-cc1a-444b-b1ef-413ea28b89a7

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Vector Field Math </nodes/field/vector_field_math>`
* Fields-> :doc:`Vector Field Lines </nodes/field/vector_field_lines>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* SUB: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Replace each point of straight line segment with the result of noise vector field evaluation at that point:

.. image:: https://user-images.githubusercontent.com/284644/79476391-5c0fbc80-8022-11ea-9457-1babe56f4388.png
  :target: https://user-images.githubusercontent.com/284644/79476391-5c0fbc80-8022-11ea-9457-1babe56f4388.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Visualize vector field vectors by connecting original points of the line segment and the points obtained by moving the original points by the results of vector field evaluation:

.. image:: https://user-images.githubusercontent.com/284644/79476395-5d40e980-8022-11ea-846b-68da09ed2e41.png
  :target: https://user-images.githubusercontent.com/284644/79476395-5d40e980-8022-11ea-846b-68da09ed2e41.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`