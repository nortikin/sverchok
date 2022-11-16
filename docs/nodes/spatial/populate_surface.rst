Populate Surface
================

.. image:: https://user-images.githubusercontent.com/14288520/201608736-28204c15-b113-4206-bcd6-13c98fdff4e9.png
  :target: https://user-images.githubusercontent.com/14288520/201608736-28204c15-b113-4206-bcd6-13c98fdff4e9.png

Functionality
-------------

This node generates a number of random points, distributed on a given Surface
according to the provided Scalar Field. It has two modes:

* Generate uniformly distributed points in areas where the value of scalar
  field is greater than threshold;
* Generate points according to the value of scalar field: put more points in
  areas where the value of scalar field is greater. More precisely, the
  probability of the vertex appearance at some point is proportional to the
  value of the scalar field at that point.

This node can make sure that generated points are not too close to one another.
This can be controlled in one of two ways:

* By specifying minimum distance between any two different points;
* Or by specifying a radius around each generated points, which should be free.
  More precisely, the node makes sure that if you place a sphere of specified
  radius at each point as a center, these spheres will never intersect. The
  radiuses of such spheres are provided as a scalar field: it defines a radius
  value for any point in the space.

Inputs
------

This node has the following inputs:

* **Surface**. Surface object, on which random points must be generated. This
  input is mandatory.
* **Field**. The scalar field defining the distribution of generated points. If
  this input is not connected, the node will generate evenly distributed
  points. This input is mandatory, if **Proportional** parameter is checked.

.. image:: https://user-images.githubusercontent.com/14288520/201907163-7538e450-54dc-4e5f-8145-a37e875e6a68.png
  :target: https://user-images.githubusercontent.com/14288520/201907163-7538e450-54dc-4e5f-8145-a37e875e6a68.png

* **Count**. The number of points to be generated. The default value is 50.
* **MinDistance**. This input is available only when **Distance** parameter is
  set to **Min. Distance**. Minimum allowable distance between generated
  points. If set to zero, there will be no restriction on distance between
  points. Default value is 0.

.. image:: https://user-images.githubusercontent.com/14288520/201924063-ee6625d7-ef58-468a-9862-c1328f47194e.png
  :target: https://user-images.githubusercontent.com/14288520/201924063-ee6625d7-ef58-468a-9862-c1328f47194e.png

* **RadiusField**. This input is available and mandatory only when **Distance**
  parameter is set to **Radius Field**. The scalar field, which defines radius
  of free sphere around any generated point.
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

* **Distance**. This defines how minimum distance between generated points is
  defined. The available options are:

   * **Min. Distance**. The user provides minimum distance between any two
     points in the **MinDistance** input.
   * **RadiusField**. The user defines a radius of a sphere that should be
     empty around each generated point, by providing a scalar field in the
     **RadiusField** input. The node makes sure that these spheres will not
     intersect.

   The default value is **Min. Distance**.

.. image:: https://user-images.githubusercontent.com/14288520/201926268-9c60c609-a218-4ee6-b33d-6273b5d64973.png
  :target: https://user-images.githubusercontent.com/14288520/201926268-9c60c609-a218-4ee6-b33d-6273b5d64973.png

* **Proportional**. If checked, then the points density will be distributed
  proportionally to the values of scalar field. Otherwise, the points will be
  uniformly distributed in the area where the value of scalar field exceeds
  threshold. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/201914936-7fe629b9-179f-40bf-a41e-5d413d69ad6d.png
  :target: https://user-images.githubusercontent.com/14288520/201914936-7fe629b9-179f-40bf-a41e-5d413d69ad6d.png

* **Random Radius**. This parameter is available only when **Distance**
  parameter is set to **RadiusField**. If checked, then radiuses of empty
  spheres will be generated randomly, by using uniform distribution between 0
  (zero) and the value defined by the scalar field provided in the
  **RadiusField** input. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/201896127-68213c7a-9fff-4a9a-b246-ec345f7836e0.gif
  :target: https://user-images.githubusercontent.com/14288520/201896127-68213c7a-9fff-4a9a-b246-ec345f7836e0.gif

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

.. image:: https://user-images.githubusercontent.com/14288520/201771930-bfc79962-80a4-47ac-b4fc-e198780d20f5.png
  :target: https://user-images.githubusercontent.com/14288520/201771930-bfc79962-80a4-47ac-b4fc-e198780d20f5.png

Example of "Radius Field" mode usage:

.. image:: https://user-images.githubusercontent.com/14288520/201777764-65ecca39-799a-4b17-88d5-b1da8a4d84ad.png
  :target: https://user-images.githubusercontent.com/14288520/201777764-65ecca39-799a-4b17-88d5-b1da8a4d84ad.png