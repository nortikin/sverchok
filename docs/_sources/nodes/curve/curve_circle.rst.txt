Circle (Curve)
==============

Functionality
-------------

This node generates a Curve object, which represents a circle, or an arc of the circle.

Specifics of curve parametrization: the T parameter is proportional to curve
length, and equals to the angle along the circle arc.

Curve domain: defined in node's inputs, by default from 0 to 2*pi.

Behavior when trying to evaluate curve outside of it's boundaries: returns
corresponding point on the circle.

Optionally, this node can generate a NURBS Curve object. Note that when NURBS
mode is enabled, the parametrization of the curve is different from standard
parametrization of the circle (defined by the angle).

Inputs
------

This node has the following inputs:

* **Center**. A matrix defining the location of the circle. This may be used to
  move, scale or rotate the curve. By default, the center of matrix is at the
  origin, and the circle is laying in the XOY plane.
* **Radius**. Circle radius. The default value is 1.0.
* **T Min**. Minimum value of the curve parameter. In **Generic** mode, the
  parameter is the angle on the arc. The default value is 0.0.
* **T Max**. Maximum value of the curve parameter. In **Generic** mode, the
  parameter is the angle on the arc. The default value is 2*pi (radians).
* **NPoints**. This input is available only when **Mode** parameter is set to
  **NURBS**. Defines the number of corners in curve's control polygon. The
  minimum value is 3. The default value is 4.

Parameters
----------

This node has the following parameters:

* **Mode**. This defines the type of the curve to be generated. The available
  options are:

  * **Generic**. Create a generic Circle Curve object with standard angle-based
    parametrization.
  * **NURBS**. Create a NURBS Curve object.

  The default mode is **Generic**.

* **Angle Units**. The units in which values of **T Min**, **T Max** inputs are
  measured. The available options are:

  * **Rad**. Radians (2*pi is full circle).
  * **Deg**. Degrees (360 is full circle).
  * **Uni**. Unit circles (1.0 is full circle).

  The default value is **Rad**.

Outputs
-------

This node has one output:

* **Curve**. The circle (or arc) curve.

Examples of usage
-----------------

Simple use:

.. image:: https://user-images.githubusercontent.com/284644/77347101-27794f80-6d59-11ea-9bcd-182c918222cc.png

Use together with Extrude node to create a surafce:

.. image:: https://user-images.githubusercontent.com/284644/77347798-344a7300-6d5a-11ea-88c2-e25e12be74b9.png

Example of NURBS mode usage:

.. image:: https://user-images.githubusercontent.com/284644/129481402-e45d1583-426d-4420-b231-e717ca14e081.png

