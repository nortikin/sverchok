NURBS Curve Extremes
====================

Functionality
-------------

This node searches for points on the curve, which are extreme points along the specified direction. For example, if specified direction is along Z axis, this node will search for points which have maximum or minimum Z coordinate.

This node is similar to "Curve Extremes" node, but has the following differences:

* This node can work only with non-rational NURBS curves (i.e. NURBS curves which do not use weights) of degrees 1 (polyline), 2, 3 or 4.
* This node can search for extremes only along some direction, not along arbitrary scalar field.
* Thanks to these restrictions, this node works several times faster than "Curve Extremes".

Inputs
------

This node has the following inputs:

* **Curve**. The curve to find extremes on. This input is mandatory.
* **Direction**. Vector specifying the direction to find extremes along. The default value is (0, 0, 1) (Z axis).

Parameters
----------

This node has the following parameters:

* **Sign**. This defines what kind of extreme points it is required to
  find. The available values are **Min** and **Max**. The default option is
  **Max**.
* **Global only**. If checked, the node will search for global extremes only.
  Otherwise, it will search for global and local extreme points. Checked by
  default.

Outputs
-------

This node has the following outputs:

* **Point**. Extreme point in 3D space.
* **T**. Curve's T parameter, corresponding to the extreme point.

