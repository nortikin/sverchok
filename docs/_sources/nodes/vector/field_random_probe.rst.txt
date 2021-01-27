Field Random Probe
==================

Functionality
-------------

This node generates random points, which are distributed according to the provided Scalar Field. It has two modes:

* Generate uniformly distributed points in areas where the value of scalar
  field is greater than threshold;
* Generate points according to the value of scalar field: put more points in
  areas where the value of scalar field is greater. More precisely, the
  probability of the vertex appearence at some point is proportional to the
  value of the scalar field at that point.

Inputs
------

This node has the following inputs:

* **Field**. The scalar field defining the distribution of generated points. This input is mandatory.
* **Bounds**. Vertices defining the general area where the points will be
  generated. Only bounding box of these vertices will be used. This input is
  mandatory.
* **Count**. The number of points to be generated. The default value is 50.
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

This node has the following parameter:

* **Proportional**. If checked, then the points density will be distributed
  proportionally to the values of scalar field. Otherwise, the points will be
  uniformly distributed in the area where the value of scalar field exceeds
  threshold. Unchecked by default.

When **Proportional** mode is enabled, then the probability of vertex
appearance at the certain point is calculated as ``P = (V - FieldMin) /
(FieldMax - FieldMin)``, where V is the value of scalar field at that point,
and FieldMin, FieldMax are values of corresponding node inputs.

Outputs
-------

This node has the following outputs:

* **Vertices**. Generated vertices.

Examples of usage
-----------------

Generate cubes near the cyllinder:

.. image:: https://user-images.githubusercontent.com/284644/81504481-f2be5900-9302-11ea-8948-fb189c3fc3c5.png

Generate cubes according to the scalar field defined by some formula:

.. image:: https://user-images.githubusercontent.com/284644/81504488-f94cd080-9302-11ea-9da5-f27f633f2191.png

