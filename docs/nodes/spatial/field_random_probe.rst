Field Random Probe
==================

Functionality
-------------

This node generates random points, which are distributed according to the provided Scalar Field. It has two modes:

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

* **Field**. The scalar field defining the distribution of generated points. If
  this input is not connected, the node will generate evenly distributed
  points. This input is mandatory, if **Proportional** parameter is checked.
* **Bounds**. Vertices defining the general area where the points will be
  generated. Only bounding box of these vertices will be used. This input is
  mandatory.
* **Count**. The number of points to be generated. The default value is 50.
* **MinDistance**. This input is available only when **Distance** parameter is
  set to **Min. Distance**. Minimum allowable distance between generated
  points. If set to zero, there will be no restriction on distance between
  points. Default value is 0.
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

* **Proportional**. If checked, then the points density will be distributed
  proportionally to the values of scalar field. Otherwise, the points will be
  uniformly distributed in the area where the value of scalar field exceeds
  threshold. Unchecked by default.
* **Random Radius**. This parameter is available only when **Distance**
  parameter is set to **RadiusField**. If checked, then radiuses of empty
  spheres will be generated randomly, by using uniform distribution between 0
  (zero) and the value defined by the scalar field provided in the
  **RadiusField** input. Unchecked by default.

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

Example of "Radius Field** mode usage:

.. image:: https://user-images.githubusercontent.com/284644/102390341-1ca4d000-3ff6-11eb-90f5-dfa07646f941.png

Here we are placing spheres of different radiuses at each generated point.
Since radiuses of the sphere are defined by the same scalar field which is used
for RadiusField input, these spheres do never intersect.

