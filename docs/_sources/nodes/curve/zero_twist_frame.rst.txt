Curve Zero-Twist Frame
======================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ceb19d9c-8873-4bda-a391-92b1d78b8089
  :target: https://github.com/nortikin/sverchok/assets/14288520/ceb19d9c-8873-4bda-a391-92b1d78b8089

Functionality
-------------

This node calculates a reference frame along the curve, which has minimal
rotation around curve's tangent while moving along the curve.

Two algorithms are implemented for calculating of such a frame.

The first algorithm is to rotate curve's Frenet_ frame around curve's
tangent (in the negative direction). More precisely, an indefinite integral of
curve's torsion_ is calculated to get the total rotation of Frenet frame around
the tangent while moving from curve's starting point to any other point.

The indefinite integral is calculated numerically, by subdividing the domain of
the curve in many pieces. The more pieces are used, the more precise the
calculation will be, but the more time it will take. So, this node allows one
to specify the number of curve subdivisions to be used.

Note that it is not possible to correctly calculate Frenet frame of the curve
at the point where it has zero curvature (or at a straight segment of the
curve), and, therefore, the calculation by the first algorithm can also fail in
such cases.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/9ccc28e7-f6fa-4b8b-a3bb-29f38ec80370
  :target: https://github.com/nortikin/sverchok/assets/14288520/9ccc28e7-f6fa-4b8b-a3bb-29f38ec80370

The second algorithm is to take the normal direction at the starting point to
curve and to "track" it along the curve, by projecting previous normal
direction on the plane that is perpendicular to curve's tangent at the next
"knot" point. The frame at arbitrary point is then calculated by quaternion
linear interpolation. The second algorithm is supposed to work with any curves.

.. _Frenet: https://en.wikipedia.org/wiki/Frenet%E2%80%93Serret_formulas
.. _torsion: https://en.wikipedia.org/wiki/Torsion_of_a_curve

.. image:: https://github.com/nortikin/sverchok/assets/14288520/3ffc57c5-1442-4b52-b81a-cebddcdcd369
  :target: https://github.com/nortikin/sverchok/assets/14288520/3ffc57c5-1442-4b52-b81a-cebddcdcd369

* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Inputs
------

This node has the following inputs:

* **Curve**. The curve to calculate frame for. This input is mandatory.
* **Resolution**. The number of segments to subdivide the curve in to calculate the torsion integral. The bigger the value is, the more precise calculation will be, but the more time it will take. The default value is 50.
* **T**. The value of curve's T parameter to calculate the frame at. The default value is 0.5.

Parameters
----------

This node has the following parameters:

* **Algorithm**. The following algorithms are available:

  * **Integrate torsion**. Calculate frame by "substracting" indefinite
    integral of curve torsion from curve's Frenet frame matrices.
  * **Track normal**. Calculate frames by "tracking" normal direction from
    along the curve.
  
  The default option is **Integrate torsion**.

* **Join**. If checked, the node will output the single list of matrices,
  joined from any number of input curves provided. Otherwise, the node will
  output a separate list of matrices for each input curve. Checked by default.

Outputs
-------

This node has the following outputs:

* **CumulativeTorsion**. Total angle of curve's Frenet frame rotation around
  curve's tangent, when moving from curve's starting point to the specified T
  parameter value — i.e., the indefinite integral of curve's torsion. The angle
  is expressed in radians. This output is only available when **Algorithm**
  parameter is set to **Integrate torsion**.
* **Matrix**. Curve's zero-twist frame at specified value of the T parameter.
  The location component of the matrix is the point of the curve. Z axis of the
  matrix points along curve's tangent.

Example of usage
----------------

Use zero-twist frames to put cubes along the curve:

.. image:: https://user-images.githubusercontent.com/284644/78504364-20edcd80-7786-11ea-831e-80db9be81e2b.png
  :target: https://user-images.githubusercontent.com/284644/78504364-20edcd80-7786-11ea-831e-80db9be81e2b.png
  
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Compare that to the use of curve's Frenet frames:

.. image:: https://user-images.githubusercontent.com/284644/78504337-ed12a800-7785-11ea-9a6c-1427ced45d55.png
  :target: https://user-images.githubusercontent.com/284644/78504337-ed12a800-7785-11ea-9a6c-1427ced45d55.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c414cff5-b51d-48c3-ba47-122fbd2b8249
  :target: https://github.com/nortikin/sverchok/assets/14288520/c414cff5-b51d-48c3-ba47-122fbd2b8249
  
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`