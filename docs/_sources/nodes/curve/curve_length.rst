Curve Length
============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e3daf084-d9ee-43ac-9d99-c66d55fa6018
  :target: https://github.com/nortikin/sverchok/assets/14288520/e3daf084-d9ee-43ac-9d99-c66d55fa6018

Functionality
-------------

This node calculates the length of the curve. It also can calculate the length
of certain segment of the curve within specified range of curve's T parameter.

The curve's length is calculated numerically, by subdividing the curve in many
straight segments and summing their lengths. The more segments you subdivide
the curve in, the more precise the length will be, but the more time it will
take to calculate. So the node gives you control on the number of subdivisions.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/829ea5a2-39bf-452c-abe4-c855bbd65672
  :target: https://github.com/nortikin/sverchok/assets/14288520/829ea5a2-39bf-452c-abe4-c855bbd65672

* Curves-> :doc:`Extend Curve </nodes/curve/extend_curve>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

Inputs
------

This node has the following inputs:

* **Curve**. The curve being measured. This input is mandatory.
* **TMin**. The minimum value of the T parameter of the measured segment. If
  **T Mode** parameter is set to **Relative**, then reasonable values for this
  input are within `[0 .. 1]` range. Otherwise, reasonable values are defined
  by the curve domain. The default value is 0.0.
* **TMax**. The maximum value of the T parameter of the measured segment. If
  **T Mode** parameter is set to **Relative**, then reasonable values for this
  input are within `[0 .. 1]` range. Otherwise, reasonable values are defined
  by the curve domain. The default value is 1.0.
* **Resolution**. The number of segments to subdivide the curve in to calculate
  the length. The bigger the value, the more precise the calculation will be,
  but the more time it will take. The default value is 50.

Parameters
----------

This node has the following parameter:

* **T mode**. This defines units in which **TMin**, **TMax** parameters are measured:

  * **Absolute**. The parameters will be the actual values of curve's T
    parameter. To calculate the length of the whole curve, you will have to set
    **TMin** and **TMax** to the ends of curve's domain.
  * **Relative**. The parameters values will be rescaled, so that with **TMin**
    set to 0.0 and **TMax** set to 1.0 the node will calculate the length of
    the whole curve.

Outputs
-------

This node has the following output:

* **Length**. The length of the curve (or it's segment).

Examples of usage
-----------------

The length of a unit circle is 2*pi:

.. image:: https://user-images.githubusercontent.com/284644/77850952-6b53d500-71ef-11ea-80fe-07815a5c7e1d.png
  :target: https://user-images.githubusercontent.com/284644/77850952-6b53d500-71ef-11ea-80fe-07815a5c7e1d.png

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Calculate length of some smooth curve:

.. image:: https://user-images.githubusercontent.com/284644/77849699-01cfc880-71e7-11ea-97b2-9229e0f9c630.png
  :target: https://user-images.githubusercontent.com/284644/77849699-01cfc880-71e7-11ea-97b2-9229e0f9c630.png

* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`

Take some points on the curve (with even steps in T) and calculate length from the beginning of the curve to each point:

.. image:: https://user-images.githubusercontent.com/284644/77849701-0300f580-71e7-11ea-89a7-197f7778da71.png
  :target: https://user-images.githubusercontent.com/284644/77849701-0300f580-71e7-11ea-89a7-197f7778da71.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`