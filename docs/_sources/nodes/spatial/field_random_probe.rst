Field Random Probe
==================

.. image:: https://user-images.githubusercontent.com/14288520/201920986-aab5aaa6-7a49-4604-876b-5031dc52feab.png
  :target: https://user-images.githubusercontent.com/14288520/201920986-aab5aaa6-7a49-4604-876b-5031dc52feab.png

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

.. image:: https://user-images.githubusercontent.com/14288520/201991541-76e85981-e32a-4153-8a2f-2b2fca84b38e.png
  :target: https://user-images.githubusercontent.com/14288520/201991541-76e85981-e32a-4153-8a2f-2b2fca84b38e.png

**Fields**-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`

* **Bounds**. Vertices defining the general area where the points will be
  generated. Only bounding box of these vertices will be used. This input is
  mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/201993790-04ffeb02-ec26-409f-bdfc-c137eff69bb1.png
  :target: https://user-images.githubusercontent.com/14288520/201993790-04ffeb02-ec26-409f-bdfc-c137eff69bb1.png

* **Count**. The number of points to be generated. The default value is 50.

.. image:: https://user-images.githubusercontent.com/14288520/201993542-e174184f-2bd4-4a39-a0a1-01469c61b0af.png
  :target: https://user-images.githubusercontent.com/14288520/201993542-e174184f-2bd4-4a39-a0a1-01469c61b0af.png

* **MinDistance**. This input is available only when **Distance** parameter is
  set to **Min. Distance**. Minimum allowable distance between generated
  points. If set to zero, there will be no restriction on distance between
  points. Default value is 0.

.. image:: https://user-images.githubusercontent.com/14288520/201994709-323a12fa-3f52-4280-ad78-9db8d62df3bf.png
  :target: https://user-images.githubusercontent.com/14288520/201994709-323a12fa-3f52-4280-ad78-9db8d62df3bf.png

* **RadiusField**. This input is available and mandatory only when **Distance**
  parameter is set to **Radius Field**. The scalar field, which defines radius
  of free sphere around any generated point.

.. image:: https://user-images.githubusercontent.com/14288520/201995939-d21f87f6-ea58-49ef-b845-355d473a6130.png
  :target: https://user-images.githubusercontent.com/14288520/201995939-d21f87f6-ea58-49ef-b845-355d473a6130.png

* **Threshold**. Threshold value: the node will not generate points in areas
  where the value of scalar field is less than this value. The default value is
  0.5.

.. image:: https://user-images.githubusercontent.com/14288520/201998468-7320eae9-3901-4b2f-b769-0a03b599d1cd.png
  :target: https://user-images.githubusercontent.com/14288520/201998468-7320eae9-3901-4b2f-b769-0a03b599d1cd.png

* **Field Minimum**. Minimum value of scalar field reached within the area
  defined by **Bounds** input. This input is used to define the probability of
  vertices generation at certain points. This input is only available when the
  **Proportional** parameter is checked. The default value is 0.0.

.. image:: https://user-images.githubusercontent.com/14288520/201997186-64476415-8bda-4f8a-b3f1-8ac2faf05af3.png
  :target: https://user-images.githubusercontent.com/14288520/201997186-64476415-8bda-4f8a-b3f1-8ac2faf05af3.png

* **Field Maximum**. Maximum value of scalar field reached within the area
  defined by **Bounds** input. This input is used to define the probability of
  vertices generation at certain points. This input is only available when the
  **Proportional** parameter is checked. The default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/201999011-dc9a2ce2-94d0-48d4-9b70-bd2255fd9907.png
  :target: https://user-images.githubusercontent.com/14288520/201999011-dc9a2ce2-94d0-48d4-9b70-bd2255fd9907.png

* **Seed**. Random seed. The default value is 0.

.. image:: https://user-images.githubusercontent.com/14288520/201999569-8908019a-0c55-4d3f-aff8-c04f78f6547e.png
  :target: https://user-images.githubusercontent.com/14288520/201999569-8908019a-0c55-4d3f-aff8-c04f78f6547e.png

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
     intersect. (If radius is negative then result is unpredictable)

   The default value is **Min. Distance**.

**Min.Distance**

.. image:: https://user-images.githubusercontent.com/14288520/202023076-208dd585-9f3b-462f-b17e-66479165a397.gif
  :target: https://user-images.githubusercontent.com/14288520/202023076-208dd585-9f3b-462f-b17e-66479165a397.gif

**Radius Field**

.. image:: https://user-images.githubusercontent.com/14288520/202022780-85482c48-14c0-4e8b-b78e-90b2af9d9cf0.gif
  :target: https://user-images.githubusercontent.com/14288520/202022780-85482c48-14c0-4e8b-b78e-90b2af9d9cf0.gif

* **Proportional**. If checked, then the points density will be distributed
  proportionally to the values of scalar field. Otherwise, the points will be
  uniformly distributed in the area where the value of scalar field exceeds
  threshold. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202024927-d3b7bc4b-8130-4bd9-ba64-9d9284bb9112.gif
  :target: https://user-images.githubusercontent.com/14288520/202024927-d3b7bc4b-8130-4bd9-ba64-9d9284bb9112.gif

* **Flat output**. If checked, the node will generate
  one flat list of objects for all sets of input parameters. Otherwise, a
  separate list of objects will be generated for each set of input parameter
  values.

.. image:: https://user-images.githubusercontent.com/14288520/202544718-b6bf467a-b044-42cb-b036-9214ed8d3c73.png
  :target: https://user-images.githubusercontent.com/14288520/202544718-b6bf467a-b044-42cb-b036-9214ed8d3c73.png

* **Random Radius**. This parameter is available only when **Distance**
  parameter is set to **RadiusField**. If checked, then radiuses of empty
  spheres will be generated randomly, by using uniform distribution between 0
  (zero) and the value defined by the scalar field provided in the
  **RadiusField** input. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202025651-21db71da-9001-4c06-b93c-2b927d51c475.gif
  :target: https://user-images.githubusercontent.com/14288520/202025651-21db71da-9001-4c06-b93c-2b927d51c475.gif

When **Proportional** mode is enabled, then the probability of vertex
appearance at the certain point is calculated as ``P = (V - FieldMin) /
(FieldMax - FieldMin)``, where V is the value of scalar field at that point,
and FieldMin, FieldMax are values of corresponding node inputs.

Outputs
-------

This node has the following outputs:

* **Vertices**. Generated vertices.
* **Radius**.

Examples of usage
-----------------

Generate cubes near the cylinder:

.. image:: https://user-images.githubusercontent.com/14288520/202032902-34d25e2c-d641-4568-aeee-e4608037b2d5.png
  :target: https://user-images.githubusercontent.com/14288520/202032902-34d25e2c-d641-4568-aeee-e4608037b2d5.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Generate cubes according to the scalar field defined by some formula:

.. image:: https://user-images.githubusercontent.com/284644/81504488-f94cd080-9302-11ea-9da5-f27f633f2191.png
  :target: https://user-images.githubusercontent.com/284644/81504488-f94cd080-9302-11ea-9da5-f27f633f2191.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Example of **Radius Field** mode usage:

.. image:: https://user-images.githubusercontent.com/14288520/202041621-1b474361-f34b-4023-ad92-8414171f31fd.gif
  :target: https://user-images.githubusercontent.com/14288520/202041621-1b474361-f34b-4023-ad92-8414171f31fd.gif

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/202041205-f782a3dd-16cd-44bd-bef3-3b69a82ea12c.png
  :target: https://user-images.githubusercontent.com/14288520/202041205-f782a3dd-16cd-44bd-bef3-3b69a82ea12c.png



Here we are placing spheres of different radiuses at each generated point.
Since radiuses of the sphere are defined by the same scalar field which is used
for RadiusField input, these spheres do never intersect.

