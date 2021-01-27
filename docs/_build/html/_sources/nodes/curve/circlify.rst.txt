Circlify
========

Dependencies
------------

This node requires Circlify_ library to work.

.. _Circlify: https://github.com/elmotec/circlify

Functionality
-------------

This node draws several circles close to one another, thus packing them into one bigger circle.

Inputs
------

This node has the following inputs:

* **Radiuses**. List of circle radiuses. Exact values of these radises are not
  used; only their relations (proportions) are used. Actual sizes of generated
  circles depend on **MajorRadius** input as well. This input is mandatory.
* **Center**. The origin point of whole generated picture. The default value is
  global origin ``(0, 0, 0)``.
* **MajorRadius**. The radius of the bigger circle, into which all other should
  be packed. The default value is 1.0.

Parameters
----------

This node has the following parameters:

* **Plane**. The coordinate plane in which the circles will be generated. The
  available values are **XY**, **YZ** and **XZ**. The default value is **XY**.
* **Show enclosure**. Whether to generate the big circle, into which all other
  are inscribed. Checked by default.

Outputs
-------

This node has the following outputs:

* **Circles**. Generated circle curve objects.
* **Centers**. Central points of generated circles.
* **Radiuses**. Radiuses of generated circles.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/86526782-9d8d6680-beb1-11ea-8ee2-b98e93c9c09f.png


