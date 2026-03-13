Cast Curve
==========

.. image:: https://user-images.githubusercontent.com/14288520/210331787-21a0ac18-34ad-4c72-80e2-02e205155415.png
  :target: https://user-images.githubusercontent.com/14288520/210331787-21a0ac18-34ad-4c72-80e2-02e205155415.png

Functionality
-------------

This node generates a Curve object by casting (projecting) another Curve onto one of predefined shapes.

Curve domain: the same as the curve being projected.

Inputs
------

This node has the following inputs:

* **Curve**. Curve to be projected. This input is mandatory.
* **Center**. The meaning of this input depends on **Target form** parameter:

   * for **Plane**, this is a point on the plane;
   * for **Sphere**, this is the center of the sphere;
   * for **Cylinder**, this is a point on cylinder's axis line.

* **Direction**. This parameter is available only when **Target form** parameter is set to **Plane** or **Cylinder**. It's meaning depends on target form:

  * for **Plane**, this is the normal direction of the plane;
  * for **Cyinder**, this is the directing vector of cylinder's axis line.

.. image:: https://user-images.githubusercontent.com/14288520/210342515-508ba724-b85d-4794-a2d2-b39d6ed9dd5d.png
  :target: https://user-images.githubusercontent.com/14288520/210342515-508ba724-b85d-4794-a2d2-b39d6ed9dd5d.png

* **Radius**. This parameter is available only when **Target form** parameter is set to **Sphere** or **Cylinder**. It's meaning depends on target form:

  * for **Sphere**, this is the radius of the sphere;
  * for **Cylinder**, this is the radius of the cylinder.

.. image:: https://user-images.githubusercontent.com/14288520/210342769-14a50d6d-75a6-4497-b132-a4571697bb01.png
  :target: https://user-images.githubusercontent.com/14288520/210342769-14a50d6d-75a6-4497-b132-a4571697bb01.png

* **Coefficient**. Casting effect coefficient. 0 means no effect, 1.0 means
  output the curve on the target form. Use other values for linear
  interpolation or linear extrapolation. The default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/210342988-32076af3-a43b-4c88-aabb-0e81aacfedb2.png
  :target: https://user-images.githubusercontent.com/14288520/210342988-32076af3-a43b-4c88-aabb-0e81aacfedb2.png

Parameters
----------

This node has the following parameter:

* **Target form**. The available forms are:

  * **Plane** is defined by **Center** (a point on the plane) and **Direction** (plane normal vector direction).
  * **Sphere** is defined by **Center** of the sphere and **Radius**.
  * **Cylinder** is defined by **Center** (a point on cylinder's axis),
    **Direction** (directing vector of the cylinder's axis) and **Radius** of
    the cylinder.

.. image:: https://user-images.githubusercontent.com/14288520/210343311-5baadd9d-482d-4da4-88f0-2ee7b56571eb.png
  :target: https://user-images.githubusercontent.com/14288520/210343311-5baadd9d-482d-4da4-88f0-2ee7b56571eb.png

* **Use control points**. If checked, then for NURBS curves the node will
  project only control points of the curve, instead of projecting each point of
  the curve. For non-NURBS curves, the node will raise an error (become red),
  and processing will stop. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/210350854-0cec95d6-4330-4f4d-ba33-ed21a0b58293.png
  :target: https://user-images.githubusercontent.com/14288520/210350854-0cec95d6-4330-4f4d-ba33-ed21a0b58293.png

Outputs
-------

This node has the following output:

* **Curve**. The casted curve.

Example of usage
----------------

A line and the same line casted onto the unit sphere:

.. image:: https://user-images.githubusercontent.com/284644/77565225-ba46f500-6ee5-11ea-95ea-1baa8555d024.png

* Curves->Curve Primitives-> :doc:`Line (Curve) </nodes/curve/line>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/210354406-ffb583a6-a9e6-421b-9274-39f1ca1af5ea.png
  :target: https://user-images.githubusercontent.com/14288520/210354406-ffb583a6-a9e6-421b-9274-39f1ca1af5ea.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Curves-> :doc:`Approximate Bezier Curve </nodes/curve/bezier_fit>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* DEGREES: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

.. image:: https://user-images.githubusercontent.com/14288520/210355094-6388d29c-17c0-451d-bce9-50b5081fc638.gif 
  :target: https://user-images.githubusercontent.com/14288520/210355094-6388d29c-17c0-451d-bce9-50b5081fc638.gif

.. image:: https://user-images.githubusercontent.com/14288520/210355510-aa8825b8-a1b9-4a24-8212-b247a5f40d86.gif
  :target: https://user-images.githubusercontent.com/14288520/210355510-aa8825b8-a1b9-4a24-8212-b247a5f40d86.gif

.. image:: https://user-images.githubusercontent.com/14288520/210356368-addf641c-74d6-4e4c-b452-ef0bec313674.gif
  :target: https://user-images.githubusercontent.com/14288520/210356368-addf641c-74d6-4e4c-b452-ef0bec313674.gif