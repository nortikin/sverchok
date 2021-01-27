Sweep Face (Solid)
==================

Dependencies
------------

This node requires FreeCAD_ libraries installed to work.

.. _FreeCAD: https://www.freecadweb.org/

Functionality
-------------

This node takes a Solid Face (i.e. a Surface trimmed by some edges), called
"profile", and makes a Solid object from it, by sweeping it along the provided
Curve (called "Path").

Solid Face object can be created with nodes from "Make Face" submenu (such as
"Face from Curve"); also any NURBS or NURBS-like surface can be used as a Solid
Face.

This node supports only NURBS and NURBS-like curves and surfaces.

**NOTE**: there are known pitfails with this node:

1. It can not work with non-planar profile faces.
2. If the path curve has points with zero curvature, and in some other cases of
   complex path curves, the node sometimes produces weird shapes.
3. If "Align Face Location" parameter is not checked, and the profile face is
   not located near the beginning of the path curve, then the node most
   probably will generate a weird shape.

Inputs
------

This node has the following inputs:

* **Profile**. The Solid Face (or Surface object) to be sweeped along the path.
  This input is mandatory.
* **Path**. The Curve object to be used as a sweep path. This input is
  mandatory.

Parameters
----------

This node has the following parameters:

* **Frenet**. If checked, then the node will use Frenet frame of the path curve
  to control rotation of the profile face during sweep. Otherwise, FreeCAD
  built-in algorithm will be used. Frenet algorithm is known to cause twisted
  shapes when the path curve has points with zero curvature. For complex path
  curves, you probabbly will have to try both values of this parameter to find
  out which suits you better. Checked by default.
* **Align Face Location**. If checked, then the profile face will be moved to
  the beginning of the path curve before the sweeping process; so the beginning
  of the resulting shape will be at the place where the path curve begins.
  Otherwise, the resulting shape will start at the place where the profile face
  is located initially. Checked by default.
* **Align Face Rotation**. If checked, then the profile face will be rotated to
  be perpendicular to the path curve, before the sweeping process. Checked by
  default.

Outputs
-------

This node has the following output:

* **Solid**. The generated Solid object.

Example of Usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/92308554-e3e96980-efb7-11ea-8d0f-dd2be6745043.png

