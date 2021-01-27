Ellipse (Curve)
===============

Functionality
-------------

This node generates a Curve object representing an ellipse. The ellipse is
defined by a set of parameters: major/minor radii (a.k.a. major/minor
semi-axis), eccentricity, focal length.

Inputs
------

This node has the following inputs:

* **Major Radius**. The value of ellipse's major radius (semiaxis). The default
  value is 1.0.
* **Minor Radius**. The value of ellipse's minor radius (semiaxis). The default
  value is 0.8. This input is available only when **Mode** parameter is set to
  **ab**.
* **Eccentricity**. The value of ellipse's eccentricity. The default value is
  0.6. This input is available only when **Mode** parameter is set to **ae**.
* **Focal length**. Distance from ellipse's center to it's focal points. The
  default value is 0.6. This input is available only when **Mode** parameter is
  set to **ac**.
* **Matrix**. This defines the center and the orientation of the ellipse curve.
  By default, ellipse's origin is placed at the global origin ``(0, 0, 0)``,
  and the ellipse is placed in XOY plane.

Parameters
----------

This node has the following parameters:

* **Mode**. This defines which parameters are used to define the ellipse. The
  available options are:

  * **ab**. The ellipse is defined by two semiaxis - **Major Radius** and
    **Minor Radius** inputs.
  * **ae**. The ellipse is defined by major semiaxis and eccentricity.
  * **ac**. The ellipse is defined by major semiaxis and focal length.

  The default value is **ab**.

* **Centering**. This defines where the curve's origin is placed. The available options are:

  * **F1**, **F2**. The curve's origin is placed at one of ellipse's focal points.
  * **C**. The curve's origin is placed at the center of the ellipse.

  The default value is **C**.

Outputs
-------

This node has the following outputs:

* **Ellipse**. The generated curve object.
* **F1**, **F2**. Focal points of the ellipse.

Examples of usage
-----------------

Default settings:

.. image:: https://user-images.githubusercontent.com/284644/84289369-d6107d80-ab5b-11ea-909f-62a9c9205de2.png

Extrude smaller ellipse along bigger one:

.. image:: https://user-images.githubusercontent.com/284644/84289874-7666a200-ab5c-11ea-8483-c7b885cab805.png

