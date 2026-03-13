Minimal Surface from Curve
==========================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/36d36059-be37-46e4-9793-bba7082f30f5
  :target: https://github.com/nortikin/sverchok/assets/14288520/36d36059-be37-46e4-9793-bba7082f30f5

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Surface, based on the provided Curve, by use of RBF_
method. To do so, the node evaluates the curve in many points, and then
generates an RBF surface for these points.  Depending on node parameters, the
curve can be either interpolating (go through all points) or only approximating.

The generated surface is not, strictly speaking, guaranteed to be minimal_; but
in many simple cases it is close enough to the minimal.

.. _RBF: http://www.scholarpedia.org/article/Radial_basis_function
.. _minimal: https://en.wikipedia.org/wiki/Minimal_surface

.. image:: https://github.com/nortikin/sverchok/assets/14288520/55ef75d8-747c-4271-9a11-4a3d3da3407b
  :target: https://github.com/nortikin/sverchok/assets/14288520/55ef75d8-747c-4271-9a11-4a3d3da3407b

* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Inputs
------

This node has the following inputs:

* **Curve**. The curve to generate surface from. This input is mandatory.
* **Samples**. Number of samples to evaluate the curve in. Theoretically,
  greater number of samples will give the surface which follows the curve more
  precisely. However, for some RBF functions too high values generate weird
  results. The default value is 50.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/8f811065-cd92-48c2-ad9b-98ca3cdc1a57
    :target: https://github.com/nortikin/sverchok/assets/14288520/8f811065-cd92-48c2-ad9b-98ca3cdc1a57

* **Epsilon**. Epsilon parameter of used RBF function; it affects the shape of
  generated surface. The default value is 1.0.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/270750e7-5189-4c68-a30c-bb5f1e23992a
    :target: https://github.com/nortikin/sverchok/assets/14288520/270750e7-5189-4c68-a30c-bb5f1e23992a

* **Smooth**. Smoothness parameter of used RBF function. If this is zero, then
  the surface will go through all provided points; otherwise, it will be only an
  approximating surface. The default value is 0.0.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/cbde4c9c-3659-4afb-9d85-461b89913c0e
    :target: https://github.com/nortikin/sverchok/assets/14288520/cbde4c9c-3659-4afb-9d85-461b89913c0e

Parameters
----------

This node has the following parameter:

* **Function**. The specific function used by the node. The available values are:

  * Multi Quadric
  * Inverse
  * Gaussian
  * Cubic
  * Quintic
  * Thin Plate

  The default function is Multi Quadric. `Scipy RBF Functions <https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.Rbf.html>`_ :

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/36d36059-be37-46e4-9793-bba7082f30f5
    :target: https://github.com/nortikin/sverchok/assets/14288520/36d36059-be37-46e4-9793-bba7082f30f5



Outputs
-------

This node has the following outputs:

* **Surface**. The generated surface object.
* **TrimCurve**. The curve in surface's U/V space, which corresponds to the
  provided input Curve. This output can be used with "Trim & Tessellate" or
  "Adaptive tessellate" nodes to trim the surface.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/61341dfd-bfdc-4f4d-9a7a-d9b7a2f6d520
      :target: https://github.com/nortikin/sverchok/assets/14288520/61341dfd-bfdc-4f4d-9a7a-d9b7a2f6d520

  * Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
  * Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
  * Surfaces-> :doc:`Tesselate & Trim Surface </nodes/surface/tessellate_trim>`
  * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
  * Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

* **Curve**. The curve from **TrimCurve** output mapped to the surface.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/7888aafb-f5d9-4f8d-9b5f-38d2c7802935
    :target: https://github.com/nortikin/sverchok/assets/14288520/7888aafb-f5d9-4f8d-9b5f-38d2c7802935

  * Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
  * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
  * Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87231392-54b54080-c3d0-11ea-8374-a7e1c0528e5b.png
  :target: https://user-images.githubusercontent.com/284644/87231392-54b54080-c3d0-11ea-8374-a7e1c0528e5b.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Curves->Curve Primitives-> :doc:`Fillet Polyline </nodes/curve/fillet_polyline>`
* Surfaces-> :doc:`Tesselate & Trim Surface </nodes/surface/tessellate_trim>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`