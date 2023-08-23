Ellipse (Curve)
===============

.. image:: https://user-images.githubusercontent.com/14288520/205259757-70c83631-6abf-4501-86b0-fa9ad5ba1f76.png
  :target: https://user-images.githubusercontent.com/14288520/205259757-70c83631-6abf-4501-86b0-fa9ad5ba1f76.png

Functionality
-------------

This node generates a Curve object representing an ellipse. The ellipse is
defined by a set of parameters: major/minor radii (a.k.a. major/minor
semi-axis), eccentricity, focal length.

.. image:: https://user-images.githubusercontent.com/14288520/205485273-bff2586d-69e1-45a8-8310-eb8b3aa27851.png
  :target: https://user-images.githubusercontent.com/14288520/205485273-bff2586d-69e1-45a8-8310-eb8b3aa27851.png

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

.. image:: https://user-images.githubusercontent.com/14288520/205485604-7321fa32-4254-44b3-a18b-b72239bb787f.png
  :target: https://user-images.githubusercontent.com/14288520/205485604-7321fa32-4254-44b3-a18b-b72239bb787f.png

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

.. image:: https://user-images.githubusercontent.com/14288520/205485803-12cfb9da-11e9-4238-b490-08249600644b.png
  :target: https://user-images.githubusercontent.com/14288520/205485803-12cfb9da-11e9-4238-b490-08249600644b.png

* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

Extrude smaller ellipse along bigger one:

.. image:: https://user-images.githubusercontent.com/14288520/205486157-dca072ac-8353-4756-8f7b-f9519905afa7.png
  :target: https://user-images.githubusercontent.com/14288520/205486157-dca072ac-8353-4756-8f7b-f9519905afa7.png

* Surfaces-> :doc:`Extrude Curve Along Curve </nodes/surface/extrude_curve>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`