Line (Curve)
============

Functionality
-------------

This node generates a Curve object, which is a segment of straight line between two points.

Curve domain: defined in node's inputs, by default from 0 to 1.

Behavior when trying to evaluate curve outside of it's boundaries: returns
corresponding point on the line.

Inputs
------

This node has the following inputs:

* **Point1**. The first point on the line (the beginning of the curve, if **UMin** is set to 0).
* **Point2**. The second point on the line (the end of the curve, if **UMax is set to 1). This input is available only if **Mode** parameter is set to **Two points**.
* **Direction**. Directing vector of the line. This input is available only when **Mode** parameter is set to **Point and direction**.
* **UMin**. Minimum value of curve parameter. The default value is 0.0.
* **UMax**. Maximum value of curve parameter. The default value is 1.0.

Parameters
----------

This node has the following parameters:

* **Mode**:
   
  * **Two points**: line is defined by two points on the line.
  * **Point and direction**: line is defined by one point on the line and the directing vector.

* **Join**. If checked, the node will output a single flat list of Curve
  objects for all sets of input parameters. Otherwise, it will output a
  separate list of Curve objects for each set of input parameters. Checked by
  default.

Outputs
-------

This node has the following output:

* **Curve**. The line curve.

Examples of usage
-----------------

Trivial example:

.. image:: https://user-images.githubusercontent.com/284644/77443595-fc503800-6e0c-11ea-9340-6473785a6a51.png

Generate several lines, and bend them according to noise vector field:

.. image:: https://user-images.githubusercontent.com/284644/77443601-fd816500-6e0c-11ea-9ed2-0516eba95951.png

