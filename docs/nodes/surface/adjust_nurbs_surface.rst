Adjust NURBS Surface
====================

Functionality
-------------

The node can do two things:

* Adjust a surface in such a way that it would pass through a specified curve
  at specified value of surface's U or V parameter; i.e., the curve would
  become one of the surface's iso-curves.
* Adjust a surface in such a way that it would pass through a specified point
  at specified values of surface's U and V parameters.

This node can work with NURBS or NURBS-like surfaces and curves only.

During adjustment, the topology of the surface (number of control points and
The adjustment is performed in such a way, that the total amount of control
points movement is minimal.
Thus, the topology of initial surface (number of control points and knotvector)
is important for the shape of the resulting surface. One can control the result
by inserting additional knots into the surface before applying "Adjust NURBS
Surface" node.

Inputs
------

This node has the following inputs:

* **Surface**. The surface to be adjusted. This input is mandatory.
* **Curve**. The target curve. This input is only available and mandatory when
  the **Mode** parameter is set to **Iso U/V Curve**.
* **Parameter**. The value of surface's U or V parameter, iso-curve at which is
  to be moved to coincide with the target curve. This input is only available
  when the **Mode** parameter is set to **Iso U/V Curve**. The default value is
  0.5.
* **UVPoint**. The point in surafce's U/V space, which is to be moved to
  coincide with the target point. X and Y coordinates of this point are
  interpreted as U and V parameters on the surface, correspondingly; Z
  coordinate is ignored. This input is only available and mandatory when the
  **Mode** parameter is set to **Point**.

Parameters
----------

This node has the following parameters:

* **Mode**. The available modes are:

  * **Iso U/V Curve**. Adjust the surface in such a way that it would pass
    through the specified curve at specified value of U or V surface parameter.
    This is the default mode.
  * **Point**. Adjust the surface in such a way that it would pass trhough the
    specified point in 3D space at specified values of surface's U and V
    parameters.

* **Direction**. This parameter is only available when **Mode** parameter is
  set to **Isu U/V Curve**. The available options are **U** and **V**. If this
  parameter is set to **U**, then the surface will be adjusted in such a way
  that it would pass through the specified curve at specified value of **U**
  parameter; and similarly for the **V** direction. The default option is **U**.
* **Preserve tangents**. This parameter is only available when **Mode** parameter is
  set to **Isu U/V Curve**. If checked, then, when adjusting the surface, the
  node will try to preserve surface's tangents along the second direction.
  Unchecked by default.

Outputs
-------

This node has the following output:

* **Surface**. The resulting surface.

