Extend Curve
============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/bc848d08-3c37-49a6-8aca-bf61cd984bb5
  :target: https://github.com/nortikin/sverchok/assets/14288520/bc848d08-3c37-49a6-8aca-bf61cd984bb5

Functionality
-------------

This node generates a continuation of given Curve beyond it's end points in a
smooth manner. It can be used if you for some reason have just a segment of a
curve, and want to continue it, for example, until it meets some plane or
surface.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5974da75-a142-4f25-83fb-1af361e6936b
  :target: https://github.com/nortikin/sverchok/assets/14288520/5974da75-a142-4f25-83fb-1af361e6936b

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be extended. This input is mandatory.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f2868357-5132-4e55-bb75-e136f1ba9e29
  :target: https://github.com/nortikin/sverchok/assets/14288520/f2868357-5132-4e55-bb75-e136f1ba9e29

* **StartExt**. This defines how far the curve should be extended beyond it's
  starting point. Depending on **Extend by** parameter, this is measured either
  in terms of curve's T parameter, or in terms of curve length. Default value
  is 1.0. If this input is set to 0.0, then no continuation will be generated
  beyond curve's starting point.

* **EndExt**. This defines how far the curve should be extended beyond it's
  ending point. Depending on **Extend by** parameter, this is measured either
  in terms of curve's T parameter, or in terms of curve length. Default value
  is 1.0. If this input is set to 0.0, then no continuation will be generated
  beyond curve's ending point.

Parameters
----------

This node has the following parameters:

* **Type**. Extending curves type. The available options are:

  * **1 - Line**. Extend the curve with straight line segments. The direction of
    lines is calculated accordingly to curve's tangent directions at starting
    and ending point. Thus, it is guaranteed that the resulting curve will have
    continuous first derivative at the point where original curve is glued with
    it's extension.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/296b9895-c5cb-4acb-848f-a804c12513c5
        :target: https://github.com/nortikin/sverchok/assets/14288520/296b9895-c5cb-4acb-848f-a804c12513c5


  * **1 - Arc**. Extend the curve with circular arcs. Extension direction and arc
    radius is calculated from curve's tangents. The plane where the arc will
    lie is calculated based on curve's second derivatives at ending points.
    Thus, it is guaranteed that the resulting curve will have continuous first
    derivative at the point where original curve is glued with it's extension.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/8d6812be-a400-41cb-b569-74c4eaf0ba98
        :target: https://github.com/nortikin/sverchok/assets/14288520/8d6812be-a400-41cb-b569-74c4eaf0ba98


  * **2 - Smooth - Normal**. Extend the curve with segments of second order
    (quadratic) curves. The coefficients of curves are calculated based on
    original curve's tangent and second derivatives directions at the ending
    points. Thus, it is guaraneed that the resulting curve will have continuous
    first and second derivatives at the point where original curve is glued
    with it's extension.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/a804f9d9-e274-408c-8051-d8a52db2b8ca
        :target: https://github.com/nortikin/sverchok/assets/14288520/a804f9d9-e274-408c-8051-d8a52db2b8ca


  * **3 - Smooth - Curvature**. Extend the curve with segments of third order
    (cubic) curves. The coefficients of curves are calculated based on
    original curve's tangent, second and third derivatives directions at the ending
    points. Thus, it is guaraneed that the resulting curve will have continuous
    first, second and third derivatives at the point where original curve is glued
    with it's extension.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/7fc31678-10eb-4ba0-a03b-f72d83283300
        :target: https://github.com/nortikin/sverchok/assets/14288520/7fc31678-10eb-4ba0-a03b-f72d83283300


  The default option is **1 - Line**.

* **Extend by**. This defines the units in which values of **StartExt**,
  **EndExt** inputs is measured. The available options are:

  * **Curve parameter**. Inputs define the range of curve's T parameter. Since
    coefficients of the generated extension curves are calculated
    automatically, the length of extension curves can be hard to predict from
    the input values. On the other hand, this option is the faster one.
  * **Curve length**. Inputs define the length of extension curves. Required
    ranges of curve's T parameter is calculated numerically, so this option is
    slower.

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/3994636b-4fac-4c28-bb43-eefd584c6bd9
        :target: https://github.com/nortikin/sverchok/assets/14288520/3994636b-4fac-4c28-bb43-eefd584c6bd9

  The default option is **Curve parameter**.

* **Length resolution**. This parameter is available in the N panel only, and
  only when **Extend by** parameter is set to **Curve length**. Defines the
  resolution value for curve length calculation. The higher the value is, the
  more precisely extension curves length will be equal to the specified inputs,
  but the slower the computation will be. The default value is 50.

Outputs
-------

This node has the following outputs:

* **ExtendedCurve**. The original curve extended by one extension curve at the
  beginning and another curve at the end.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/e49b567e-90cc-4a83-a781-3b62ad13d4c6
      :target: https://github.com/nortikin/sverchok/assets/14288520/e49b567e-90cc-4a83-a781-3b62ad13d4c6

* **StartExtent**. Extension curve generated at the beginning of the original curve.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/faa2c57c-4813-4a9c-8c91-958bdc8183bc
      :target: https://github.com/nortikin/sverchok/assets/14288520/faa2c57c-4813-4a9c-8c91-958bdc8183bc

* **EndExtent**. Extension curve generated at the end of the original curve.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7b697ee7-7ebc-4cad-90c4-4249d503f1e2
      :target: https://github.com/nortikin/sverchok/assets/14288520/7b697ee7-7ebc-4cad-90c4-4249d503f1e2

Example of usage
----------------

Build part of curve from points, and then extend it to additional length of 1
at the beginning and to additional length of 2 at the end:

.. image:: https://user-images.githubusercontent.com/284644/84564568-07679400-ad7c-11ea-8370-c4a8008a8c74.png
  :target: https://user-images.githubusercontent.com/284644/84564568-07679400-ad7c-11ea-8370-c4a8008a8c74.png

* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`