Populate Surface
================

Functionality
-------------

This node generates a number of random points, distributed on a given Surface
according to the provided Scalar Field. It has two modes:

* Generate uniformly distributed points in areas where the value of scalar
  field is greater than threshold;
* Generate points according to the value of scalar field: put more points in
  areas where the value of scalar field is greater. More precisely, the
  probability of the vertex appearence at some point is proportional to the
  value of the scalar field at that point.

Inputs
------

This node has the following inputs:

* **Surface**. Surface object, on which random points must be generated. This
  input is mandatory.
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
* **UVPoints**. Coordinates of generated vertices in surface's U/V space. Third
  coordinate of these points is always zero.

Example of usage
----------------

Distribute points on a Moebius band according to some attractor field:

.. image:: https://user-images.githubusercontent.com/284644/99146076-7ed88100-2696-11eb-8175-67b5f268f36e.png

