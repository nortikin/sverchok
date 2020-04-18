Evaluate Curve
==============

Functionality
-------------

This node calculates the point on the curve at a given value of curve
parameter. It can also automatically calculate a set of points at a series of
evenly distributed values of curve parameter.

You will be using this node a lot, to visualize any curve, or to convert it to mesh.

Inputs
------

This node has the following inputs:

* **Curve**. Curve to be evaluated. This input is mandatory.
* **T**. The value of curve parameter to calculate the point on the curve for.
  This input is available only when **Mode** parameter is set to **Manual**.
  Sensible range values for this input corresponds to the domain of the curve
  provided in the **Curve** input.
* **Samples**. Number of curve parameter values to calculate the curve points
  for. This input is available only when **Mode** parameter is set to **Auto**.
  The default value is 50.

Parameters
----------

This node has the following parameter:

* **Mode**:

  * **Automatic**. Calculate curve points for the set of curve parameter values which are evenly distributed within curve domain.
   * **Manual**. Calculate curve point for the provided value of curve parameter.

Outputs
-------

This node has the following outputs:

* **Vertices**. The calculated points on the curve.
* **Edges**. Edges between the calculated points. This output is only available when the **Mode** parameter is set to **Auto**.
* **Tangents**. Curve tangent vectors for each value of curve parameter.

Examples of usage
-----------------

This node used for line visualization:

.. image:: https://user-images.githubusercontent.com/284644/77443595-fc503800-6e0c-11ea-9340-6473785a6a51.png

