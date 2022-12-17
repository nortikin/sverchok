Line (Curve)
============

.. image:: https://user-images.githubusercontent.com/14288520/205123453-f5972461-f396-4c3f-a3ce-35d1a227d364.png
  :target: https://user-images.githubusercontent.com/14288520/205123453-f5972461-f396-4c3f-a3ce-35d1a227d364.png

Functionality
-------------

This node generates a Curve object, which is a segment of straight line between two points.

.. image:: https://user-images.githubusercontent.com/14288520/205124501-de4bcbd5-4ee1-49ef-a743-6e9aa4e4b77f.png
  :target: https://user-images.githubusercontent.com/14288520/205124501-de4bcbd5-4ee1-49ef-a743-6e9aa4e4b77f.png

* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

Curve domain: defined in node's inputs, by default from 0 to 1.

.. image:: https://user-images.githubusercontent.com/14288520/205121877-50a420e7-6d04-4726-aed3-1c2e4aa9fb9e.png
  :target: https://user-images.githubusercontent.com/14288520/205121877-50a420e7-6d04-4726-aed3-1c2e4aa9fb9e.png

Behavior when trying to evaluate curve outside of it's boundaries: returns
corresponding point on the line.

.. image:: https://user-images.githubusercontent.com/14288520/205149346-8dbc3261-6974-4160-b169-a8a4655e409c.png
  :target: https://user-images.githubusercontent.com/14288520/205149346-8dbc3261-6974-4160-b169-a8a4655e409c.png

Inputs
------

This node has the following inputs:

* **Point1**. The first point on the line (the beginning of the curve, if **UMin** is set to 0).
* **Point2**. The second point on the line (the end of the curve, if **UMax** is set to 1). This input is available only if **Mode** parameter is set to **Two points**.

.. image:: https://user-images.githubusercontent.com/14288520/205124931-291bc550-eae1-40ea-8082-bed70256f135.png
  :target: https://user-images.githubusercontent.com/14288520/205124931-291bc550-eae1-40ea-8082-bed70256f135.png

* **Direction**. Directing vector of the line. This input is available only when **Mode** parameter is set to **Point and direction**.

.. image:: https://user-images.githubusercontent.com/14288520/205125279-f98c0924-4bb9-4631-9e41-fc739d2d90f8.png
  :target: https://user-images.githubusercontent.com/14288520/205125279-f98c0924-4bb9-4631-9e41-fc739d2d90f8.png

* **UMin**. Minimum value of curve parameter. The default value is 0.0.
* **UMax**. Maximum value of curve parameter. The default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/205126046-ecd09ee4-14b6-46a4-bdf4-41becd718b81.png
  :target: https://user-images.githubusercontent.com/14288520/205126046-ecd09ee4-14b6-46a4-bdf4-41becd718b81.png

Parameters
----------

This node has the following parameters:

* **Mode**:
   
  * **Two points**: line is defined by two points on the line.
  * **Point and direction**: line is defined by one point on the line and the directing vector.

.. image:: https://user-images.githubusercontent.com/14288520/205126495-ca08918e-9890-46d7-9072-26f3ead54d7c.png
  :target: https://user-images.githubusercontent.com/14288520/205126495-ca08918e-9890-46d7-9072-26f3ead54d7c.png

* **Join**. If checked, the node will output a single flat list of Curve
  objects for all sets of input parameters. Otherwise, it will output a
  separate list of Curve objects for each set of input parameters. Checked by
  default.

.. image:: https://user-images.githubusercontent.com/14288520/205127293-da38c0b3-c3ea-4475-984c-ad3bed4ca979.png
  :target: https://user-images.githubusercontent.com/14288520/205127293-da38c0b3-c3ea-4475-984c-ad3bed4ca979.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`

Outputs
-------

This node has the following output:

* **Curve**. The line curve.

Examples of usage
-----------------

Trivial example:

.. image:: https://user-images.githubusercontent.com/14288520/205145147-4617c648-0492-4d35-ad23-0294cdfabab9.png
  :target: https://user-images.githubusercontent.com/14288520/205145147-4617c648-0492-4d35-ad23-0294cdfabab9.png

* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

Generate several lines, and bend them according to noise vector field:

.. image:: https://user-images.githubusercontent.com/14288520/205147576-d1b65086-c767-4aa9-8be9-4b3fc66b9809.png
  :target: https://user-images.githubusercontent.com/14288520/205147576-d1b65086-c767-4aa9-8be9-4b3fc66b9809.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Curves-> :doc:`Apply Field to Curve </nodes/curve/apply_field_to_curve>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`

.. image:: https://user-images.githubusercontent.com/14288520/205146654-161c1f83-5b36-42fc-99cc-4649d5b2ec45.gif
  :target: https://user-images.githubusercontent.com/14288520/205146654-161c1f83-5b36-42fc-99cc-4649d5b2ec45.gif