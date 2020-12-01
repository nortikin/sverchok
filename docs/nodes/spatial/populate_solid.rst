Populate Solid
==============

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node generates a number of random points, distributed in a given Solid
object according to the provided Scalar Field. It has two modes:

* Generate uniformly distributed points in areas where the value of scalar
  field is greater than threshold;
* Generate points according to the value of scalar field: put more points in
  areas where the value of scalar field is greater. More precisely, the
  probability of the vertex appearence at some point is proportional to the
  value of the scalar field at that point.

The node can generate points either inside the Solid body, or on it's surface.

Inputs
------

This node has the following inputs:

* **Solid**. Solid object, in which the points must be generated. This input is
  mandatory.
* **Field**. The scalar field defining the distribution of generated points. If
  this input is not connected, the node will generate evenly distributed
  points. This input is mandatory, if **Proportional** parameter is checked.
* **Count**. The number of points to be generated. The default value is 50.
* **MinDistance**. Minimum allowable distance between generated points. If set
  to zero, there will be no restriction on distance between points. Default
  value is 0.
* **Threshold**. Threshold value: the node will not generate points in areas
  where the value of scalar field is less than this value. The default value is
  0.5.
* **Field Minimum**. Minimum value of scalar field reached within the area
  defined by **Bounds** input. This input is used to define the probability of
  vertices generation at certain points. This input is only available when the
  **Proportional** parameter is checked. The default value is 0.0.
* **Field Maximum**. Maximum value of scalar field reached within the area
  defined by **Bounds** input. This input is used to define the probability of
  vertices generation at certain points. This input is only available when the
  **Proportional** parameter is checked. The default value is 1.0.
* **Seed**. Random seed. The default value is 0.

Parameters
----------

This node has the following parameters:

* **Generation mode**. This defines where the points will be generated. The available options are:

  * **Volume**. The points will be generated inside the Solid object.
  * **Surface**. The points will be generated on the surface of the Solid object.

  The default value is **Volume**

* **Proportional**. If checked, then the points density will be distributed
  proportionally to the values of scalar field. Otherwise, the points will be
  uniformly distributed in the area where the value of scalar field exceeds
  threshold. Unchecked by default.
* **Accept in surface**. This parameter is only available when the **Generation
  mode** parameter is set to **Volume**. This defines whether it is acceptable
  to generate points on the surface of the body as well as inside it. Checked
  by default.
* **Accuracy**. This parameter is available in the N panel only. This defines
  the accuracy of defining whether the point lies on the surface of the body.
  The higher the value, the more precise this process is. The default value is
  5.

When **Proportional** mode is enabled, then the probability of vertex
appearance at the certain point is calculated as ``P = (V - FieldMin) /
(FieldMax - FieldMin)``, where V is the value of scalar field at that point,
and FieldMin, FieldMax are values of corresponding node inputs.

Outputs
-------

This node has the following output:

* **Vertices**. Generated vertices.

Example of Usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/99146273-5b163a80-2698-11eb-8f1d-a41978cc96ea.png

