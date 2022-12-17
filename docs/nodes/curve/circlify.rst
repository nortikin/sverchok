Circlify
========

.. image:: https://user-images.githubusercontent.com/14288520/206100789-c1b20c86-769f-42b3-8807-cb9c1e4a3607.png
  :target: https://user-images.githubusercontent.com/14288520/206100789-c1b20c86-769f-42b3-8807-cb9c1e4a3607.png

Dependencies
------------

This node requires Circlify_ library to work.

.. _Circlify: https://github.com/elmotec/circlify

Functionality
-------------

This node draws several circles close to one another, thus packing them into one bigger circle.

.. image:: https://user-images.githubusercontent.com/14288520/206101665-f92006f3-1db8-4335-b8a9-260c879e4da3.png
  :target: https://user-images.githubusercontent.com/14288520/206101665-f92006f3-1db8-4335-b8a9-260c879e4da3.png

Inputs
------

This node has the following inputs:

* **Radiuses**. List of circle radiuses. Exact values of these radises are not
  used; only their relations (proportions) are used. Actual sizes of generated
  circles depend on **MajorRadius** input as well. This input is mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/206102402-407499bc-60e2-436d-ab18-7624d06e4f45.png
  :target: https://user-images.githubusercontent.com/14288520/206102402-407499bc-60e2-436d-ab18-7624d06e4f45.png

* **Center**. The origin point of whole generated picture. The default value is
  global origin ``(0, 0, 0)``.

.. image:: https://user-images.githubusercontent.com/14288520/206103422-743dbfb1-699c-40bf-bf68-9873a85f9900.png
  :target: https://user-images.githubusercontent.com/14288520/206103422-743dbfb1-699c-40bf-bf68-9873a85f9900.png

* **MajorRadius**. The radius of the bigger circle, into which all other should
  be packed. The default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/206106202-6603fc47-01b4-4bfb-9d66-762c103d49b8.png
  :target: https://user-images.githubusercontent.com/14288520/206106202-6603fc47-01b4-4bfb-9d66-762c103d49b8.png

Parameters
----------

This node has the following parameters:

* **Plane**. The coordinate plane in which the circles will be generated. The
  available values are **XY**, **YZ** and **XZ**. The default value is **XY**.

.. image:: https://user-images.githubusercontent.com/14288520/206104804-d7f97bdb-1361-480d-8ced-200a90f10c28.png
  :target: https://user-images.githubusercontent.com/14288520/206104804-d7f97bdb-1361-480d-8ced-200a90f10c28.png

* **Show enclosure**. Whether to generate the big circle, into which all other
  are inscribed. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/206105294-5576ef76-c48f-4573-bac7-84a47ae5a456.png
  :target: https://user-images.githubusercontent.com/14288520/206105294-5576ef76-c48f-4573-bac7-84a47ae5a456.png

if **Show enclosure** is Off then **MajorRadius** and **Center** are not preset in outputs sockets data (Cicles, Centers and Radiuses)

Outputs
-------

This node has the following outputs:

* **Circles**. Generated circle curve objects.
* **Centers**. Central points of generated circles.
* **Radiuses**. Radiuses of generated circles.

.. image:: https://user-images.githubusercontent.com/14288520/206105677-6b4f1973-7707-45ee-9862-3891235911f2.png
  :target: https://user-images.githubusercontent.com/14288520/206105677-6b4f1973-7707-45ee-9862-3891235911f2.png

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/206107780-c71627b1-a22e-406e-8c2f-7ddd4c66a0ee.png
  :target: https://user-images.githubusercontent.com/14288520/206107780-c71627b1-a22e-406e-8c2f-7ddd4c66a0ee.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`