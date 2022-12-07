Bezier Spline Segment (Curve)
=============================

.. image:: https://user-images.githubusercontent.com/14288520/206110543-cd184387-be30-462b-8839-73b7babc703a.png
  :target: https://user-images.githubusercontent.com/14288520/206110543-cd184387-be30-462b-8839-73b7babc703a.png

Functionality
-------------

This node generates a Bezier_ Curve object. It is possible to generate curves
of second order (quadratic), third order (cubic), or arbitrary order (generic).
For cubic curves, there are several ways to define the control points.

.. _Bezier: https://en.wikipedia.org/wiki/B%C3%A9zier_curve

Curve parametrization: from 0 to 1.

.. image:: https://user-images.githubusercontent.com/14288520/206113591-da604efc-e8ae-49ce-8425-3bf0fa222654.png
  :target: https://user-images.githubusercontent.com/14288520/206113591-da604efc-e8ae-49ce-8425-3bf0fa222654.png

Inputs
------

This node has the following inputs:

* **Start**. Starting point of the curve. This node is not available if
  **Mode** parameter is set to **Generic**.

.. image:: https://user-images.githubusercontent.com/14288520/206116839-23263736-33f0-4064-ae9a-12e65858db03.png
  :target: https://user-images.githubusercontent.com/14288520/206116839-23263736-33f0-4064-ae9a-12e65858db03.png

* **Control1** / **Tangent1**. Exact meaning of this input depends on **Mode** parameter:

   * When mode is **Cubic 2pts + 2 controls**, then this is the first control point.
   * When mode is **Cubic 2pts + 2 tangents**, then this is a tangent vector at the starting point.
   * When mode is **Cubic 4pts**, then this is the second point on the curve, used for interpolation.
   * When mode is **Quadratic**, then this is a middle control point of the curve.
   * This input is not available when mode is **Generic**.

.. image:: https://user-images.githubusercontent.com/14288520/206122112-dc073838-2fd0-4237-85c9-65ffc54a4419.png
  :target: https://user-images.githubusercontent.com/14288520/206122112-dc073838-2fd0-4237-85c9-65ffc54a4419.png

* **Control2** / **Tangent2**. Exact meaning of this input depends on **Mode** parameter:

  * When mode is **Cubic 2pts + 2 controls**, then this is the second control point.
  * When mode is **Cubic 2pts + 2 tangents**, then this is a tangent vector at the end point of the curve.
  * When mode is **Cubic 4pts**, then this is the third point on the curve, used for interpolation.
  * This input is not available in other modes.

.. image:: https://user-images.githubusercontent.com/14288520/206125260-a13cc613-db49-4e09-9b36-ffa0d6b01177.png
  :target: https://user-images.githubusercontent.com/14288520/206125260-a13cc613-db49-4e09-9b36-ffa0d6b01177.png

* **End**. Ending point of the curve. This node is not available if
  **Mode** parameter is set to **Generic**.

.. image:: https://user-images.githubusercontent.com/14288520/206127115-54d56fba-db73-4bc1-8d39-c94d99dda24e.png
  :target: https://user-images.githubusercontent.com/14288520/206127115-54d56fba-db73-4bc1-8d39-c94d99dda24e.png

* **ControlPoints**. Control points of the curve. This input is only available
  when the **Mode** parameter is set to **Generic**. Note that Bezier curve
  begins at it's first control point and ends at it's last control point, but
  it in general does not pass through all other control points.

.. image:: https://user-images.githubusercontent.com/14288520/206128059-cd82f52b-4b17-465d-89bb-41e67420e384.png
  :target: https://user-images.githubusercontent.com/14288520/206128059-cd82f52b-4b17-465d-89bb-41e67420e384.png


Parameters
----------

This node has the following parameters:

* **Mode**. This defines how the control points will be provided, as well as
  order of the curve. The available options are:

  * **Cubic 2pts + 2 controls**. Generate a cubic spline (with four control
    points). **Start** and **End** inputs define start and end points;
    **Control1** and **Control2** points define two additional control points.
  * **Cubic 2pts + 2 tangents**. Generate a cubic spline. **Start** and **End**
    inputs define start and end points. **Tangent1** input defines the tangent
    vector at the starting point; **Tangent2** input defines the tangent vector
    at the end point. This mode of defining a Bezier curve is also known as
    Hermite spline.
  * **Cubic 4pts**. Generate a cubic spline, which goes through four provided
    control points (interpolating spline). Four control points are defined by
    **Start**, **Control1**, **Control2**, **End** inputs.
  * **Quadratic**. Generate a quadratic spline (with three control points).
    **Start** and **End** inputs define start and end points; **Control1**
    input defines an additional control point for the middle of the curve.
  * **Generic**. Generate a Bezier spline of arbitrary order, which is defined
    by number of provided control points. Control points are provided in the
    **ControlPoints** input. At least two control points must be provided.

   The default value is **Cubic 2pts + 2 controls**.

.. image:: https://user-images.githubusercontent.com/14288520/206130356-8d84c179-093d-4818-a0c8-6aa6fd6de336.png
  :target: https://user-images.githubusercontent.com/14288520/206130356-8d84c179-093d-4818-a0c8-6aa6fd6de336.png

* **Cyclic**. This parameter is only available when **Mode** parameter is set
  to **Generic**. If checked, then the node will generate a closed curve, by
  adding the first control point in the end of list of control points. Note
  that in general, closed Bezier curve will not be smooth at that closing
  point.

.. image:: https://user-images.githubusercontent.com/14288520/206131593-838cf098-8e12-4aef-acfc-8161bc772da2.png
  :target: https://user-images.githubusercontent.com/14288520/206131593-838cf098-8e12-4aef-acfc-8161bc772da2.png

Outputs
-------

This node has the following outputs:

* **Curve**. Generated Bezier curve.
* **ControlPoints**. List of all control points of generated curve(s).

.. image:: https://user-images.githubusercontent.com/14288520/206131793-894ac9c0-956c-47c2-a67d-bb3b89448ea4.png
  :target: https://user-images.githubusercontent.com/14288520/206131793-894ac9c0-956c-47c2-a67d-bb3b89448ea4.png

Examples of usage
-----------------

Cubic Bezier curve by four control points:

.. image:: https://user-images.githubusercontent.com/14288520/206133629-27790d5e-e81d-457b-9109-a4a237aa5084.png
  :target: https://user-images.githubusercontent.com/14288520/206133629-27790d5e-e81d-457b-9109-a4a237aa5084.png

* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

Cubic Bezier curve by two points and two tangents (Hermite spline):

.. image:: https://user-images.githubusercontent.com/14288520/206134657-d53343bc-2561-4489-826d-e6af1e76e5b6.png
  :target: https://user-images.githubusercontent.com/14288520/206134657-d53343bc-2561-4489-826d-e6af1e76e5b6.png

* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

Cubic Bezier curve interpolated through four points:

.. image:: https://user-images.githubusercontent.com/14288520/206135263-b48d6cb2-84f6-46d1-8513-f5468a144e54.png
  :target: https://user-images.githubusercontent.com/14288520/206135263-b48d6cb2-84f6-46d1-8513-f5468a144e54.png

* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

Quadratic Bezier curve by three points:

.. image:: https://user-images.githubusercontent.com/14288520/206135901-073c7ce0-687d-4b66-a1bb-2aa3b81c80dc.png
  :target: https://user-images.githubusercontent.com/14288520/206135901-073c7ce0-687d-4b66-a1bb-2aa3b81c80dc.png

* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

---------

Generic Bezier curve (of fifth order, in this case):

.. image:: https://user-images.githubusercontent.com/14288520/206136946-e47fa857-6dcd-4d5d-ae86-77e48f633245.png
  :target: https://user-images.githubusercontent.com/14288520/206136946-e47fa857-6dcd-4d5d-ae86-77e48f633245.png

* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

---------

Generic Bezier curve for Hilbert:

.. image:: https://user-images.githubusercontent.com/14288520/206137660-7ccd6426-d80d-4858-9a9b-b9ae98b184c8.png
  :target: https://user-images.githubusercontent.com/14288520/206137660-7ccd6426-d80d-4858-9a9b-b9ae98b184c8.png

* Generator->Generatots Extended-> :doc:`Hilbert </nodes/generators_extended/hilbert>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`