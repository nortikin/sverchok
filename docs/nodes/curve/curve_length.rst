Curve Length
============

Functionality
-------------

This node calculates the length of the curve. It also can calculate the length
of certain segment of the curve within specified range of curve's T parameter.

The curve's length is calculated numerically, by subdividing the curve in many
straight segments and summing their lengths. The more segments you subdivide
the curve in, the more precise the length will be, but the more time it will
take to calculate. So the node gives you control on the number of subdivisions.

Inputs
------

This node has the following inputs:

* **Curve**. The curve being measured. This input is mandatory.
* **TMin**. The minimum value of the T parameter of the measured segment. If
  **T Mode** parameter is set to **Relative**, then reasonable values for this
  input are within `[0 .. 1]` range. Otherwise, reasonable values are defined
  by the curve domain. The default value is 0.0.
* **TMax**. The maximum value of the T parameter of the measured segment. If
  **T Mode** parameter is set to **Relative**, then reasonable values for this
  input are within `[0 .. 1]` range. Otherwise, reasonable values are defined
  by the curve domain. The default value is 1.0.
* **Resolution**. The number of segments to subdivide the curve in to calculate
  the length. The bigger the value, the more precise the calculation will be,
  but the more time it will take. The default value is 50.

Parameters
----------

This node has the following parameter:

* **T mode**. This defines units in which **TMin**, **TMax** parameters are measured:

  * **Absolute**. The parameters will be the actual values of curve's T
    parameter. To calculate the length of the whole curve, you will have to set
    **TMin** and **TMax** to the ends of curve's domain.
  * **Relative**. The parameters values will be rescaled, so that with **TMin**
    set to 0.0 and **TMax** set to 1.0 the node will calculate the length of
    the whole curve.

Outputs
-------

This node has the following output:

* **Length**. The length of the curve (or it's segment).

Examples of usage
-----------------

The length of a unit circle is 2*pi:

.. image:: https://user-images.githubusercontent.com/284644/77850952-6b53d500-71ef-11ea-80fe-07815a5c7e1d.png

Calculate length of some smooth curve:

.. image:: https://user-images.githubusercontent.com/284644/77849699-01cfc880-71e7-11ea-97b2-9229e0f9c630.png

Take some points on the curve (with even steps in T) and calculate length from the beginning of the curve to each point:

.. image:: https://user-images.githubusercontent.com/284644/77849701-0300f580-71e7-11ea-89a7-197f7778da71.png

