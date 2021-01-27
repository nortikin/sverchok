Apply Field to Curve
====================

Functionality
-------------

This node generates a Curve object by taking another Curve and "bending" it
according to some Vector Field. More precisely, it generates a curve, each
point of which is calculated as `x + Coefficient * VectorPoint(x)`.

Optionally, for NURBS and NURBS-like curves, this node can apply a Vector
Fields to control points of NURBS curve, instead of applying to all points of
the curve. Such mode is supported for the following types of curves:

* NURBS curves
* Bezier curves
* Cubic splines
* Polylines
* Circular arcs
* Line segments

Some nodes, that output complex curves composed from simple curves (for
example, "Rounded rectangle"), have **NURBS output** parameter; when it is
checked, such nodes output NURBS curves, so "Apply Field to Curve" can work
with them.

If this mode is enabled, then output curve will be always a NURBS curve.

Note that mathematically, for NURBS and Bezier curves, if you apply an affine
transformation (such as translation, scale, rotation - i.e. vector field
defined by a Matrix) to control points of a NURBS curve, you will have a curve
of exactly the same shape, but translated / scaled / rotated according to the
transformation. For any more complex transformation (attractor field, for
example), the resulting curve will have different shape; and also it will be
different from a curve that you would receive if you applied the vector field
to all points of the curve instead.

Curve domain: the same as the domain of curve being deformed.

Inputs
------

This node has the following inputs:

* **Field**. Vector field to be applied to the curve. This input is mandatory.
* **Curve**. Curve to be "bent" by vector field. This input is mandatory.
* **Coefficient**. Vector field application coefficient (0 means vector field
  will have no effect). The default value is 1.0.

Parameters
----------

This node has the following parameter:

* **Use Control Points**. If checked, then the vector field will be applied to
  control points of a NURBS curve, instead of applying it to all points of the
  curve. This node will fail (become red) if this mode is enabled, but input
  curve is not a NURBS and can not be presented as a NURBS. If not checked,
  then the node will apply the vector fields to all points of the curve; in
  such a case, it can process any type of curve. Disabled by default.

Outputs
-------

This node has the following output:

* **Curve**. The curve modified by vector field.

Example of usage
----------------

Several Line curves modified by Noise vector field:

.. image:: https://user-images.githubusercontent.com/284644/77443601-fd816500-6e0c-11ea-9ed2-0516eba95951.png

Apply Attractor field to control points of a NURBS curve. Control polygon of a resulting curve is indicated with red:

.. image:: https://user-images.githubusercontent.com/284644/90950162-8c4fe780-e468-11ea-9fa2-8d133fa07c58.png

If we apply the same curve to all points of curve (disable "Use control points" mode), we will have different curve:

.. image:: https://user-images.githubusercontent.com/284644/90950165-9245c880-e468-11ea-8439-0b450ae58010.png

