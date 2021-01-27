Curve Frame on Surface
======================

Functionality
-------------

Given a surface and a curve in the surface's U/V space, this node calculates a reference frame of a curve for the given value of curve's T parameter. The frame is calculated so that:

* it's X axis is pointing along surface's normal;
* it's Z axis is pointing along curve's tangent (in 3D space);
* it's Y axis is perpendicular to both X and Z.

This node allows one to place some object at the curve on the surface, while
aligning it both with curve's tangent and surface's normal.

Inputs
------

This node has the following inputs:

* **Surface**. The surface to put the curve into. This input is mandatory.
* **UVCurve**. The curve to calculate frame for. The curve is supposed to lie
  in XOY plane; X coordinate means U parameter of the surface, and Y coordinate
  means V parameter. This input is mandatory.
* **T**. The value of curve's T parameter. The default value is 0.5.

Parameters
----------

This node has the following parameter:

* **Join**. If checked, then the node will output single (concatenated) list of
  matrices for all input curves. Otherwise, it will output separate list of
  matrices per each input curve. Checked by default.

Outputs
-------

This node has the following outputs:

* **Matrix**. The matrix defining the frame for the curve at the specified
  value of T parameter. The location component of the matrix is the point of
  the curve.
* **Tangent**. The direction of curve's tangent vector at the specified value of T parameter.
* **Normal**. The direction of curve's main normal at the specified value of T parameter.
* **Binormal**. The direction of curve's binormal at the specified value of T parameter.

Examples of usage
-----------------

Let's generate an ellipse by generating a sine wave in U/V space of cylindrical
curve. Then we use "Curve Frame" node to place cubes along that ellipse:

.. image:: https://user-images.githubusercontent.com/284644/89296471-d28d0480-d67b-11ea-9ac0-d6104821ea94.png

As you can see, the cubes are aligned with a plane where the ellipse lies, but
they are not aligned with the cylinder surface. Now let's use "Curve frame on surface" node instead:

.. image:: https://user-images.githubusercontent.com/284644/89296479-d456c800-d67b-11ea-9409-2f83e9db415b.png

