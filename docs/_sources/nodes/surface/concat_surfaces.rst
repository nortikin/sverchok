Concatenate Surfaces
====================

Functionality
-------------

This node concatenates several Surface objects into one Surface object. This is
similar to what "Concatenate curves" node does, but for surfaces instead of
curves.

Similar to Curves, in order to concatenate two Surfaces their edges must
exactly coincide, along whole edge length. In practice, this is usually only
possible when two Surface objects were constructed in such a way that they have
common edge.

If you have two Surfaces which are NURBS, and their edges do not exactly
coincide, you may want to use "Snap Surfaces" node first in order to stitch two
surfaces edges first.

If all input surfaces are NURBS, the node can produce a NURBS surface.
Otherwise, the node can only generate a generic Surface object.

Inputs
------

This node has the following inputs:

* **Surfaces**. Surfaces to be concatenated. This input is only available when
  the **Input mode** parameter is set to **List of Surfaces**. The surfaces
  must be provided in such an order, that their edges coincide in consecutive
  order: second edge of the first surface coincides with the first edge of the
  second surface, and so on.
* **Surface1**, **Surface2**. Surfaces to be concatenated. These inputs are
  only available when the **Input mode** parameter is set to **Two Surfaces**.
  One of edges of the second surface must coincide with the opposite edge of
  the second surface.

Parameters
----------

This node has the following parameters:

* **Input mode**. The available modes are **Two surfaces** and **List of
  surfaces**. The default mode is **Two surfaces**.
* **Direction**. Surface parameter direction along which the surfaces are to be
  concatenated. The available options are **U** and **V**. The default option
  is **U**.
* **NURBS option**. This defines the type of Surface object which will be generated the available options are:

  * **Generic**. Generic Surface object will be generated regardless of type of input surfaces.
  * **Always NURBS**. The node will always try to generate a NURBS surface;
    this is not possible if one of input surfaces is not NURBS, so in this case
    the node will raise an error (become red) and stop processing.
  * **NURBS if possible**. The node will generate a NURBS surface if it is
    possible (i.e. if all input surfaces are NURBS). Otherwise, a generic
    Surface object will be generated. This is the default option.

* **Check edges coincidence**. If this parameter is checked, then before
  generating a new Surface object, the node will try to check that
  corresponding edges of input Surface objects are coinciding. This is done by
  generating a series of points on surface edges and checking that they are
  coinciding. Unchecked by default.
* **Number of points to check**. This parameter is only available when the
  **Check edges coindidence** parameter is checked. Defines the number of
  points in which it will be checked that the edges are coindiding. The default
  value is 10.
* **Tolerance**. This parameter is only available when the **Check edges
  coincidence** parameter is checked. Defines the maximum distance that is
  allowed between corresponding surface edges in order for node to concider
  edges as coinciding. The default value is ``1e-6`` (one per million).
* **Unify surfaces**. This parameter is available in the N panel only, and only
  if the **NURBS option** parameter is not set to **Generic**. If this
  parameter is checked, then for NURBS surfaces the node will insert knots in
  all input surfaces, such that all input surfaces would have the same
  knotvector. If this is not done, and input NURBS surfaces have different
  knotvectors (or different number of control points), then the construction of
  concatenated NURBS surface is not possible; so this parameter is enabled by
  default. However, if you know that the input surfaces already have the same
  knotvector and the same number of control points, then unification procedure
  will just take excessive time without being useful.
* **Knotvector accuracy**. This parameter is available only in the N panel, and
  only when the **Unify surfaces** parameter is checked. The precision (number
  of exact digits after decimal points) for knotvector unification procedure.
  The default value is 4.

Outputs
-------

This node has the following output:

* **Surface**. The resulting Surface object.

