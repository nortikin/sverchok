Fillet Curve
============

Functionality
-------------

This node takes a NURBS (or NURBS-like) Curve object, finds it's "fracture"
points (i.e. points where tangent of the curve does not change continuously),
and makes a smooth fillet in such points.

For polyline curves, it is possible to make a fillet made of circular arc, and
it is possible to make the arc of user-provided radius.
For other types of curves, it is not possible to automatically calculate
circular fillet based on radius. So, for other types of curves, this node makes
fillets by use of Bezier curves or biarcs. Points where original curve is glued
with the fillet curve are in such case specified in terms of curve's T
parameter space, instead of fillet radius.

More specifically, what this node does is follows:

* If it is known that the curve is a polyline: replace all corners of the
  polyline with a circular arc of a specified radius.
* For other types of NURBS curves,

   * Find fracture points of the curve.
   * Split the curve into segments at these fracture points.
   * Of each segment, cut a small (or not small) piece at each end, based on
     **CutOffset** input and segment's T parameter span. For example, if
     CutOffset is 0.05, and segment's T parameter span is 1.0 - 2.0, then this
     will cut the segment at points 1.05 and 1.95, leaving only span of 1.05 -
     1.95. So at this step, there will be gaps between segments.
   * Place a fillet curve (Bezier curve or BiArc) at each gap.

This node will automatically detect if the input curve is closed, and, if
necessary, add a fillet at closing point.

You can also want to take a look at **Blend Curves** node.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to make fillets for. This input is mandatory.
* **Radius**. This input is only available when **Polylines only** parameter is
  checked. This specifies the fillet radius. It is possible to provide a
  separate fillet radius for each vertex of the polyline curve. The default
  value is 0.2.
* **CutOffset**. This input is only available when **Polylines only** parameter
  is not checked. This specifies the proportion of curve segment T parameter
  span, which will be cut off of each segment in order to make a place for the
  fillet curve. The default value is 0.05.
* **BulgeFactor**. This input is only available when **Polylines only**
  parameter is not checked, and **Continuity** parameter is set to **1 -
  Tangency**. This defines the strength with which the tangent vector of the
  second curve at it's starting point will affect the generated blending curve.
  The default value is 0.5.

Parameters
----------

This node has the following parameters:

* **Polylines only**. If this is checked, the curve will process only
  polylines. If you feed it with any other curve, the node will fail. In this
  mode, it is possible to make fillets in form of circular arc, and provide the
  fillet radius. If this is not checked, the node will process any NURBS or
  NURBS-like curve, but it will not be able to make circular arc fillets based
  on fillet radius.
* **Continuity**. This defines the order of continuity of the resulting curve,
  and the algorithm used to calculate the fillet curves. The available options are:

   * **0 - Position**. This will connect curve segments with a straight line
     segment. So, effectively, this does a bevel instead of smooth fillet.
   * **1 - Tangency**. The fillet curves are generated so that the tangent of
     the curves are equal at points where fillet curves are joined with
     original curve segments. The generated fillet curves are cubic Bezier
     curves.
   * **1 - BiArc**. This option is not available when **Polylines only**
     parameter is checked. The fillet curves are generated as biarc_ curves,
     i.e.  pairs of circular arcs; they are generated so that the tanent
     vectors of the segments are equal at their meeting points. Biarc parameter
     will be set to 1.0. Note that this option works only when tangents of the
     curve at points where it is replaced with fillet are coplanar. I.e., this
     will work fine for planar curves, but may fail in other cases.
   * **1 - Circular Arc**. This option is only available when **Polylines
     only** parameter is not checked. Fillet curves are calculated as circular
     arc of radiuses provided in the **Radius** input.

   The default value is **0 - Position**.

* **Concatenate**. If checked, then the node will output all segments of
  initial curve together with generated fillet curves, concatenated into one
  curve.  Otherwise, original curve segments and fillet curves will be output
  as separate Curve objects. Checked by default.
* **Even domains**. This parameter is available in the N panel only. If
  checked, give each segment a domain of length 1. This parameter is only
  available if **Concatenate** parameter is checked.  Unchecked by default.

.. _biarc: https://en.wikipedia.org/wiki/Biarc

Outputs
-------

This node has the following outputs:

* **Curve**. Generated Curve objects.
* **Centers**. This output is only available when **Polylines only** parameter
  is checked, and **Continuity** parameter is set to **1 - Circular Arc**.
  Centers of circles used to make fillet arcs. These are matrices, since this
  output provides not only centers, but also orientation of the circles.

Examples of Usage
-----------------

Make fillets on some curve:

.. image:: https://user-images.githubusercontent.com/284644/205504044-bdaa43c8-f13f-4ff4-92f4-aca8100c989b.png

Make circular arc fillets on a polyline:

.. image:: https://user-images.githubusercontent.com/284644/205504045-aab871b9-c851-484c-a908-230cd463e060.png

