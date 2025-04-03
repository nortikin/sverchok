Circle (Curve)
==============

.. image:: https://user-images.githubusercontent.com/14288520/205152583-01ddf73b-7351-4e20-b4fa-c4550db090ed.png
  :target: https://user-images.githubusercontent.com/14288520/205152583-01ddf73b-7351-4e20-b4fa-c4550db090ed.png

Functionality
-------------

This node generates a Curve object, which represents a circle, or an arc of the circle.

.. image:: https://user-images.githubusercontent.com/14288520/205153334-7169eb01-661e-4a13-80ca-b666d70dbe75.png
  :target: https://user-images.githubusercontent.com/14288520/205153334-7169eb01-661e-4a13-80ca-b666d70dbe75.png

Specifics of curve parametrization: the T parameter is proportional to curve
length, and equals to the angle along the circle arc.

Curve domain: defined in node's inputs, by default from 0 to 2*pi.

Behavior when trying to evaluate curve outside of it's boundaries: returns
corresponding point on the circle.

.. image:: https://user-images.githubusercontent.com/14288520/205154574-26b91c66-9725-4796-9b87-da02a1df5efe.gif
  :target: https://user-images.githubusercontent.com/14288520/205154574-26b91c66-9725-4796-9b87-da02a1df5efe.gif

Optionally, this node can generate a NURBS Curve object. Note that when NURBS
mode is enabled, the parametrization of the curve is different from standard
parametrization of the circle (defined by the angle).

Inputs
------

This node has the following inputs:

* **Center**. A matrix defining the location of the circle. This may be used to
  move, scale or rotate the curve. By default, the center of matrix is at the
  origin, and the circle is laying in the XOY plane.

.. image:: https://user-images.githubusercontent.com/14288520/205167481-45d0674d-792d-4be3-b4a2-e95f9bb70b3b.png
  :target: https://user-images.githubusercontent.com/14288520/205167481-45d0674d-792d-4be3-b4a2-e95f9bb70b3b.png

.. image:: https://user-images.githubusercontent.com/14288520/205164394-6ae6703a-ba01-4794-a987-6426ddda2df6.gif
  :target: https://user-images.githubusercontent.com/14288520/205164394-6ae6703a-ba01-4794-a987-6426ddda2df6.gif

Generator-> :doc:`NGon </nodes/generator/ngon>`, Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`



* **Radius**. Circle radius. The default value is 1.0.
* **T Min**. Minimum value of the curve parameter. In **Generic** mode, the
  parameter is the angle on the arc. The default value is 0.0.
* **T Max**. Maximum value of the curve parameter. In **Generic** mode, the
  parameter is the angle on the arc. The default value is 2*pi (radians).
* **NPoints**. This input is available only when **Mode** parameter is set to
  **NURBS**. Defines the number of corners in curve's control polygon. The
  minimum value is 3. The default value is 4.

.. image:: https://user-images.githubusercontent.com/14288520/205166485-c0de25de-6748-499e-99e2-0ce584477d46.png
  :target: https://user-images.githubusercontent.com/14288520/205166485-c0de25de-6748-499e-99e2-0ce584477d46.png

Parameters
----------

This node has the following parameters:

* **Mode**. This defines the type of the curve to be generated. The available
  options are:

  * **Generic**. Create a generic Circle Curve object with standard angle-based
    parametrization.
  * **NURBS**. Create a NURBS Curve object.

  The default mode is **Generic**.

.. image:: https://user-images.githubusercontent.com/14288520/205167179-a0a0d98a-2045-4651-a3c3-0822bf7f2c33.png
  :target: https://user-images.githubusercontent.com/14288520/205167179-a0a0d98a-2045-4651-a3c3-0822bf7f2c33.png

* **Angle Units**. The units in which values of **T Min**, **T Max** inputs are
  measured. The available options are:

  * **Rad**. Radians (2*pi is full circle).
  * **Deg**. Degrees (360 is full circle).
  * **Uni**. Unit circles (1.0 is full circle).

  The default value is **Rad**.

.. image:: https://user-images.githubusercontent.com/14288520/205166877-72ef1527-56d1-436c-9f6e-5e0dbafa827a.png
  :target: https://user-images.githubusercontent.com/14288520/205166877-72ef1527-56d1-436c-9f6e-5e0dbafa827a.png

Outputs
-------

This node has one output:

* **Curve**. The circle (or arc) curve.

Examples of usage
-----------------

**Simple use**:

.. image:: https://user-images.githubusercontent.com/14288520/205167957-bc337eba-13b0-41d6-9deb-ce834063fbd7.png
  :target: https://user-images.githubusercontent.com/14288520/205167957-bc337eba-13b0-41d6-9deb-ce834063fbd7.png

* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

**Use together with Extrude node to create a surface**:

.. image:: https://user-images.githubusercontent.com/14288520/205169257-40a7d17f-966a-4a86-aee0-88481e9ba816.png
  :target: https://user-images.githubusercontent.com/14288520/205169257-40a7d17f-966a-4a86-aee0-88481e9ba816.png

* Surfaces-> :doc:`Extrude Curve Along Vector </nodes/surface/extrude_vector>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Viz-> :doc:`Viewer Draw Surface </nodes/viz/viewer_draw_surface>`

---------

**Example of NURBS mode usage**:

.. image:: https://user-images.githubusercontent.com/14288520/205170454-356bc19a-efae-42c8-8c16-c96a4b60c278.png
  :target: https://user-images.githubusercontent.com/14288520/205170454-356bc19a-efae-42c8-8c16-c96a4b60c278.png

* Curves->Curve NURBS-> :doc:`Deconstruct Curve </nodes/curve/deconstruct_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

.. image:: https://user-images.githubusercontent.com/14288520/205172043-6ac2e137-0777-4091-9443-0591db5e53a5.gif
  :target: https://user-images.githubusercontent.com/14288520/205172043-6ac2e137-0777-4091-9443-0591db5e53a5.gif