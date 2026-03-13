RBF Curve
=========

.. image:: https://user-images.githubusercontent.com/14288520/206016462-a0f0c4a9-933a-4e98-bd9a-01c0d2a85ef3.png
  :target: https://user-images.githubusercontent.com/14288520/206016462-a0f0c4a9-933a-4e98-bd9a-01c0d2a85ef3.png

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Curve, based on provided points, by use of RBF_ method (RBF_SciPy_).
Depending on node parameters, the curve can be either interpolating (go through
all points) or only approximating.

.. image:: https://user-images.githubusercontent.com/14288520/206018837-6e29b86a-3b4d-4d64-ae7d-aeab8582bfe9.png
  :target: https://user-images.githubusercontent.com/14288520/206018837-6e29b86a-3b4d-4d64-ae7d-aeab8582bfe9.png

.. _RBF: http://www.scholarpedia.org/article/Radial_basis_function
.. _RBF_SciPy: https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.Rbf.html

Inputs
------

This node has the following inputs:

* **Vertices**. The points to build the curve for. This input is mandatory.
* **Epsilon**. Epsilon parameter of used RBF function; it affects the shape of
  generated curve. The default value is 1.0.
* **Smooth**. Smoothness parameter of used RBF function. If this is zero, then
  the curve will go through all provided points; otherwise, it will be only an
  approximating curve. The default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/206021450-a4760a70-3117-49ca-9a24-172fce3ac072.png
  :target: https://user-images.githubusercontent.com/14288520/206021450-a4760a70-3117-49ca-9a24-172fce3ac072.png

Parameters
----------

This node has the following parameter:

* **Function**. The specific function used by the node. The available values are:

  * **Multi Quadric**. [ sqrt( (r/epsilon)^2 + 1) ]
  * **Inverse**. [ 1.0 / sqrt( (r / epsilon)^2 + 1) ]
  * **Gaussian**. [ exp(-(r/epsilon)^2) ]
  * **Cubic**. [ r^3 ]
  * **Quintic**. [ r^5 ]
  * **Thin Plate**. [ r^2 * log(r) ]

  The default function is **Multi Quadric**.

Outputs
-------

This node has the following output:

* **Curve**. The generated Curve object.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/206022382-948b948b-63b5-49d4-844f-04584e8a2897.png
  :target: https://user-images.githubusercontent.com/14288520/206022382-948b948b-63b5-49d4-844f-04584e8a2897.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`