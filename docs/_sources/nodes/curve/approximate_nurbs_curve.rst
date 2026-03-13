Approximate NURBS Curve
=======================

.. image:: https://user-images.githubusercontent.com/14288520/206873352-c1fafa58-1779-4324-b536-d019e27b1ec9.png
  :target: https://user-images.githubusercontent.com/14288520/206873352-c1fafa58-1779-4324-b536-d019e27b1ec9.png

Dependencies
------------

This node requires either Geomdl_, SciPy_ or FreeCAD_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/
.. _SciPy: https://scipy.org/
.. _FreeCAD: https://www.freecad.org/

Functionality
-------------

This node builds a NURBS_ Curve object, which approximates the given set of
points, i.e. goes as close to them as possible while remaining a smooth curve.

In fact, the generated curve always will be a non-rational curve, which means
that all weights will be equal to 1.

This node supports three different implementations for curve approximation.
Every single implementation offers different ways of control:

* Geomdl_ implementation can either define the number of control points of
  generated curve automatically, or you can provide it with desired number of
  control points. This implementation supports only two metrics - euclidean and
  centripetal. This implementation can not generate cyclic (closed) curves.
* SciPy_ implementation allows you to define "smoothing" parameter, to define
  how smooth you want the curve to be. By default, it selects the smoothing
  factor automatically. If you explicitly set the smoothing factor to zero, the
  curve will go exactly through all provided points, i.e. the node will perform
  interpolation instead of approximation. This implementation supports wider
  selection of metrics. This implementation can make cyclic (closed) curves.
  Additionally, when smoothing factor is not zero, you can provide different
  weights for different points.
* FreeCAD_ implementation supports three approximation methods and a wide variety of options:

  An exact curve degree cannot be specified. An interval ( Minimal Degree, Maximal Degree ) is used instead.
  The final curve degree is a result of all the constraints applied and will be in the specified interval.
  
  A global precision of the approximation can be specified as a **Tolerance** value.
  Lower values mean that the approximation curve will pass closely to the input Vertices.
  
  The **"Parameterization"** approximation method allows lots of inner continuity options   
  and offers a list of metrics for the parametrization.
  
  The **"Variational Smoothing"** method uses three additional parameters - "Length Weight",
  "Curvature Weight" and "Torsion Weight". The functions approximates the points using variational
  smoothing algorithm, which tries to minimize additional criterium:
  
  **LengthWeight*CurveLength + CurvatureWeight*Curvature + TorsionWeight*Torsion**
  
  where Continuity must be **C0, C1** ( with "Maximal Degree" >= 3 ) or
  **C2** ( with "Maximal Degree" >= 5 ).
  
  With the **"Explicit Knots"** method a custom knot sequence can be specified. The knot sequence can be
  also provided with the use of the `Generate Knotvector <https://nortikin.github.io/sverchok/docs/nodes/curve/generate_knotvector.html>`_ node based on the metrics from it.
  
  The **"Continuity"** parameter defines how smooth will be the curve internally.
  The values it can take depend on the approximation method used. It defaults to C2.
  However, it may not be applied if it conflicts with other parameters ( especially "Maximal Degree" ).


.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline
.. _"Generate Knotvector": https://nortikin.github.io/sverchok/docs/nodes/curve/generate_knotvector.html

Inputs
------

This node has the following inputs:

* **Vertices**. The points to be approximated. This input is mandatory.
* **Weights**. This input is available only when **Implementation** parameter
  is set to **SciPy**. Weights of points to be approximated. Bigger values of
  weight mean that the curve will pass through corresponding point at the
  smaller distance. This does not have sense if **Smoothing** input is set to
  zero. Optional input. If not connected, the node will consider weights of all
  points as equal.
* **Degree**. Available for **Geomdl** and **SciPy** only. Degree of the curve to be built. 
  Default value is 3. Most useful values are 3, 5 and 7. 
  If Scipy implementation is used, then maximum supported degree is 5. 
  For Geomdl, there is no hard limit, but curves of very high degree can be hard to manipulate with.
* **PointsCnt**. Number of curve's control points. This input is available only
  when **Implementation** parameter is set to **Geomdl**, and **Specify points
  count** parameter is checked. Default value is 5.
* **Smoothing**. This input is available only when **Implementation** parameter
  is set to **SciPy**, and **Scpecify smoothing** parameter is checked.
  Smoothing factor. Bigger values will make more smooth curves. Value of 0
  (zero) mean that the curve will exactly pass through all points. The default
  value is 0.1.

FreeCAD implementation specific inputs:

* **Knots**. The knot sequence. Available only if the "Explicit Knots" method is used.
  Must contain unique floats in an ascending order. When not connected, the curve will be
  calculated using Euclidean metric.
* **Minimal Degree**. Minimal possible degree of the curve to be built. 
  Default value is 3.
* **Maximal Degree**. Maximal possible degree of the curve to be built. 
  Default value is 5.
* **Tolerance**. Maximal distance of the built curve from the init Vertices.
  Default value is 0.0001.
  
* **Length Weight**. Available only for the "Variational Smoothing" method. 
  Default value is 1.0.
* **Curvature Weight**. Available only for the "Variational Smoothing" method. 
  Default value is 1.0.
* **Torsion Weight**. Available only for the "Variational Smoothing" method. 
  Default value is 1.0.


Parameters
----------

This node has the following parameters:

* **Implementation**. Approximation algorithm implementation to be used. The available values are:

  * **Geomdl**. Use the implementation from Geomdl_ library. This is available only when Geomdl library is installed.
  * **SciPy**. Use the implementation from SciPy_ library. This is available only when SciPy library is installed.
  * **FreeCAD**. Use the implementation from FreeCAD_ library. This is available only when FreeCAD library is installed.

  By default, the first available implementation is used.

* **Centripetal**. This parameter is available only when **Implementation**
  parameter is set to **Geomdl**. This defines whether the node will use
  centripetal metric. If not checked, the node will use euclidean metric.
  Unchecked by default.
* **Specify points count**. This parameter is available only when
  **Implementation** parameter is set to **Geomdl**. If checked, then it will
  be possible to specify the number of curve's control points in **PointsCnt**
  input. Otherwise, the node will determine required number of control points
  by itself (this number can be too big for many applications).
* **Cyclic**. This parameter is available only when **Implementation**
  parameter is set to **SciPy**. Defines whether the generated curve will be
  cyclic (closed). Unchecked by default.
* **Auto**. This parameter is available only when **Implementation** parameter
  is set to **SciPy**, and **Cyclic** parameter is enabled. If checked, the
  node will automatically decide if the curve should be cyclic (closed), based
  on the distance between the first and last points being approximated: if the
  points are close enough, the curve will be closed. If not checked, the curve
  will be closed regardless of distance between points, just because **Cyclic**
  parameter is checked. Unchecked by default.
* **Cyclic threshold**. This parameter is available only when
  **Implementation** parameter is set to **SciPy**, **Cyclic** parameter is
  enabled, and **Auto** parameter is enabled as well. This defines maximum
  distance between the first and the last points being approximated, for which
  the node will make the curve cyclic. Default value is 0.0, i.e. the points
  must exactly coincide in order for curve to be closed.
* **Metric**. This parameter is available when **Implementation**
  parameter is set to **SciPy** and **FreeCAD/Parametrization**. It's the metric (the specific knot values) to be used for interpolation. The
  available options are:

  * **Manhattan** metric is also known as Taxicab metric or rectilinear distance.
  * **Euclidean** also known as Chord-Length or Distance metric. The parameters of the points are proportionate to the distances between them.
  * **Points** also known as Uniform metric. The parameters of the points are distributed uniformly. Just the number of the points from the beginning.
  * **Chebyshev** metric is also known as Chessboard distance.
  * **Centripetal** The parameters of the points are proportionate to square roots of distances between them.
  * **X, Y, Z axis** Use distance along one of coordinate axis, ignore others.

  The default value is Euclidean.

* **Specify smoothing**. This parameter is available only when
  **Implementation** parameter is set to **SciPy**. If checked, the node will
  allow you to specify smoothing factor via **Smoothing** input. If not
  checked, the node will select the smoothing factor automatically. Unchecked
  by default.
  
* **Method**. Available only for the FreeCAD_ implementation. Approximation algorithm implementation to be used. The available values are:

  * **Parametrization**.
  * **Variational smoothing**.
  * **Explicit Knots**.

* **Continuity**. Available only for the FreeCAD_ implementation. Desired internal smoothness of the result curve. The available values are:

  * **C0** : Only positional continuity.
  * **G1** : Geometric tangent continuity. Available only for the "Parametrization" method.
  * **C1** : Continuity of the first derivative all along the Curve.
  * **G2** : Geometric curvature continuity. Available only for the "Parametrization" method.
  * **C2** : Continuity of the second derivative all along the Curve.
  * **C3** : Continuity of the third derivative all along the Curve. Available only for the "Parametrization" method.
  * **CN** : Infinite order of continuity. Available only for Parametrization method.


Outputs
-------

This node has the following outputs:

* **Curve**. The generated NURBS curve object.
* **ControlPoints**. Control points of the generated curve.
* **Knots**. Knot vector of the generated curve.

Example of usage
----------------

Take points from Greasepencil drawing and approximate them with a smooth curve:

.. image:: https://user-images.githubusercontent.com/284644/74363000-7becef00-4deb-11ea-9963-e864dc3a3599.png
  :target: https://user-images.githubusercontent.com/284644/74363000-7becef00-4deb-11ea-9963-e864dc3a3599.png

* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* BPY Data-> :doc:`Object ID Selector+ </nodes/object_nodes/get_asset_properties_mk2>`

---------

Use SciPy implementation to make a closed curve:

.. image:: https://user-images.githubusercontent.com/284644/101246890-d61ebe00-3737-11eb-942d-c31e02bf3c3d.png
  :target: https://user-images.githubusercontent.com/284644/101246890-d61ebe00-3737-11eb-942d-c31e02bf3c3d.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Example of the FreeCAD implementation usage. Euclidean parametrization:

.. image:: https://user-images.githubusercontent.com/66558924/216157300-8480c5a9-29e4-4110-8f46-3ba15f25b3d6.jpg
  :target: https://user-images.githubusercontent.com/66558924/216157300-8480c5a9-29e4-4110-8f46-3ba15f25b3d6.jpg

* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

Example of the FreeCAD implementation using the Explicit Knots method and utilizing the "Generate Knotvector" node:

.. image:: https://user-images.githubusercontent.com/66558924/216157176-288d70c4-040d-4e4e-bf90-e110b32c4d20.jpg
  :target: https://user-images.githubusercontent.com/66558924/216157176-288d70c4-040d-4e4e-bf90-e110b32c4d20.jpg

* Curves-> :doc:`Generate Knotvector </nodes/curve/generate_knotvector>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`