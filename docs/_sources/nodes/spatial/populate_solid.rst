Populate Solid
==============

.. image:: https://user-images.githubusercontent.com/14288520/202823386-8c640d40-e5b2-40d4-8d52-ae4aa6dbf891.png
  :target: https://user-images.githubusercontent.com/14288520/202823386-8c640d40-e5b2-40d4-8d52-ae4aa6dbf891.png

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

The node can generate points either inside the Solid body, or on it's surface.

.. image:: https://user-images.githubusercontent.com/14288520/202843160-4d678ed7-f50e-4b8d-bf7c-2e9405b4a69f.png
  :target: https://user-images.githubusercontent.com/14288520/202843160-4d678ed7-f50e-4b8d-bf7c-2e9405b4a69f.png

Inputs
------

This node has the following inputs:

* **Solid**. Solid object, in which the points must be generated. This input is
  mandatory.

.. image:: https://user-images.githubusercontent.com/14288520/202843238-83e37c2e-7756-4e60-93b6-54b83a848918.png
  :target: https://user-images.githubusercontent.com/14288520/202843238-83e37c2e-7756-4e60-93b6-54b83a848918.png

Solids-> :doc:`Sphere (Solid) </nodes/solid/sphere_solid>`

* **Field**. The scalar field defining the distribution of generated points. If
  this input is not connected, the node will generate evenly distributed
  points. This input is mandatory, if **Proportional** parameter is checked.

.. image:: https://user-images.githubusercontent.com/14288520/202843480-46245c44-7dfe-4560-a7f1-1bb52292979a.png
  :target: https://user-images.githubusercontent.com/14288520/202843480-46245c44-7dfe-4560-a7f1-1bb52292979a.png

Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`

* **Count**. The number of points to be generated. The default value is 50.

.. image:: https://user-images.githubusercontent.com/14288520/202843675-b9e470ed-e2dd-40bc-974c-59db5edb320b.png
  :target: https://user-images.githubusercontent.com/14288520/202843675-b9e470ed-e2dd-40bc-974c-59db5edb320b.png

* **MinDistance**. This input is available only when **Distance** parameter is
  set to **Min. Distance**. Minimum allowable distance between generated
  points. If set to zero, there will be no restriction on distance between
  points. Default value is 0.

.. image:: https://user-images.githubusercontent.com/14288520/202844045-8b48c206-1aeb-4d99-9d66-4e3b5fc71f92.gif
  :target: https://user-images.githubusercontent.com/14288520/202844045-8b48c206-1aeb-4d99-9d66-4e3b5fc71f92.gif

Number-> :doc:`A Number </nodes/number/numbers>`

* **RadiusField**. This input is available and mandatory only when **Distance**
  parameter is set to **Radius Field**. The scalar field, which defines radius
  of free sphere around any generated point.

.. image:: https://user-images.githubusercontent.com/14288520/202844272-85199fd7-ad08-4314-9ab3-8c4521da5b38.png
  :target: https://user-images.githubusercontent.com/14288520/202844272-85199fd7-ad08-4314-9ab3-8c4521da5b38.png

Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`

* **Threshold**. Threshold value: the node will not generate points in areas
  where the value of scalar field is less than this value. The default value is
  0.5.

.. image:: https://user-images.githubusercontent.com/14288520/202844937-b2b05fe9-abac-4e17-b12c-10b81a52c026.png
  :target: https://user-images.githubusercontent.com/14288520/202844937-b2b05fe9-abac-4e17-b12c-10b81a52c026.png

Number-> :doc:`A Number </nodes/number/numbers>`, Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`

* **Field Minimum**. Minimum value of scalar field reached within the area
  defined by **Bounds** input. This input is used to define the probability of
  vertices generation at certain points. This input is only available when the
  **Proportional** parameter is checked. The default value is 0.0.
* **Field Maximum**. Maximum value of scalar field reached within the area
  defined by **Bounds** input. This input is used to define the probability of
  vertices generation at certain points. This input is only available when the
  **Proportional** parameter is checked. The default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/202845089-a14b0487-10a5-437b-a9d0-f845e38fe666.png
  :target: https://user-images.githubusercontent.com/14288520/202845089-a14b0487-10a5-437b-a9d0-f845e38fe666.png

Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`

* **FaceMask**. Mask Solid faces.

.. image:: https://user-images.githubusercontent.com/14288520/202845552-233c083b-5ae3-4287-974b-2d87c0ee798c.png
  :target: https://user-images.githubusercontent.com/14288520/202845552-233c083b-5ae3-4287-974b-2d87c0ee798c.png

Solids-> :doc:`Box (Solid) </nodes/solid/box_solid>`, Number-> :doc:`List Input </nodes/number/list_input>`

* **Seed**. Random seed. The default value is 0.

.. image:: https://user-images.githubusercontent.com/14288520/202845244-60dc104d-14c9-4c08-bf90-597e1500c218.png
  :target: https://user-images.githubusercontent.com/14288520/202845244-60dc104d-14c9-4c08-bf90-597e1500c218.png

Parameters
----------

This node has the following parameters:

* **Generation mode**. This defines where the points will be generated. The available options are:

  * **Volume**. The points will be generated inside the Solid object.
  * **Surface**. The points will be generated on the surface of the Solid object.

  The default value is **Volume**

.. image:: https://user-images.githubusercontent.com/14288520/202845679-df6b1eb2-936c-4f4d-8769-765f26a9aee8.png
  :target: https://user-images.githubusercontent.com/14288520/202845679-df6b1eb2-936c-4f4d-8769-765f26a9aee8.png

* **Distance**. This defines how minimum distance between generated points is
  defined. The available options are:

   * **Min. Distance**. The user provides minimum distance between any two
     points in the **MinDistance** input.
   * **RadiusField**. The user defines a radius of a sphere that should be
     empty around each generated point, by providing a scalar field in the
     **RadiusField** input. The node makes sure that these spheres will not
     intersect.

   The default value is **Min. Distance**.

.. image:: https://user-images.githubusercontent.com/14288520/202846408-88497a53-c69d-4d6c-bfaa-61f3d8852e8e.png
  :target: https://user-images.githubusercontent.com/14288520/202846408-88497a53-c69d-4d6c-bfaa-61f3d8852e8e.png

Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`, Solids-> :doc:`Box (Solid) </nodes/solid/box_solid>`, Number-> :doc:`A Number </nodes/number/numbers>`

* **Proportional**. If checked, then the points density will be distributed
  proportionally to the values of scalar field. Otherwise, the points will be
  uniformly distributed in the area where the value of scalar field exceeds
  threshold. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202846803-8536c6a0-d952-43cc-a9ad-453f72d65ba8.gif
  :target: https://user-images.githubusercontent.com/14288520/202846803-8536c6a0-d952-43cc-a9ad-453f72d65ba8.gif

Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`, Solids-> :doc:`Box (Solid) </nodes/solid/box_solid>`, Number-> :doc:`A Number </nodes/number/numbers>`

* **Random Radius**. This parameter is available only when **Distance**
  parameter is set to **RadiusField**. If checked, then radiuses of empty
  spheres will be generated randomly, by using uniform distribution between 0
  (zero) and the value defined by the scalar field provided in the
  **RadiusField** input. Unchecked by default.

.. image:: https://user-images.githubusercontent.com/14288520/202846901-c14239c3-c7d5-4b2b-803d-6d097f90385d.gif
  :target: https://user-images.githubusercontent.com/14288520/202846901-c14239c3-c7d5-4b2b-803d-6d097f90385d.gif

Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`, Solids-> :doc:`Box (Solid) </nodes/solid/box_solid>`, Number-> :doc:`A Number </nodes/number/numbers>`

* **Accept in surface**. This parameter is only available when the **Generation
  mode** parameter is set to **Volume**. This defines whether it is acceptable
  to generate points on the surface of the body as well as inside it. Checked
  by default.
* **Accuracy**. This parameter is available in the N panel only. This defines
  the accuracy of defining whether the point lies on the surface of the body.
  The higher the value, the more precise this process is. The default value is
  5.

.. image:: https://user-images.githubusercontent.com/14288520/202847008-cf135052-a08d-49ae-838e-9ee4e458489d.png
  :target: https://user-images.githubusercontent.com/14288520/202847008-cf135052-a08d-49ae-838e-9ee4e458489d.png

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

.. image:: https://user-images.githubusercontent.com/14288520/202847380-7b36aa68-4e6d-4c79-88a3-3017fb174eae.png
  :target: https://user-images.githubusercontent.com/14288520/202847380-7b36aa68-4e6d-4c79-88a3-3017fb174eae.png

* Solids-> :doc:`Cylinder (Solid) </nodes/solid/cylinder_solid>`
* Solids-> :doc:`Solid Boolean </nodes/solid/solid_boolean>`
* Solids-> :doc:`Solid Viewer </nodes/solid/solid_viewer>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Example of "Radius Field" mode usage:

.. image:: https://user-images.githubusercontent.com/14288520/202847664-26cd5174-bfe9-4f44-b594-0dd5ea13f402.png
  :target: https://user-images.githubusercontent.com/14288520/202847664-26cd5174-bfe9-4f44-b594-0dd5ea13f402.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`
* Solids-> :doc:`Cylinder (Solid) </nodes/solid/cylinder_solid>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/202847746-7b1c966a-85b6-41ab-8173-f5296cdab34b.gif
  :target: https://user-images.githubusercontent.com/14288520/202847746-7b1c966a-85b6-41ab-8173-f5296cdab34b.gif

---------

.. image:: https://user-images.githubusercontent.com/14288520/202848027-ff0bf841-2b98-4df8-95a8-11078ec2ab09.png
  :target: https://user-images.githubusercontent.com/14288520/202848027-ff0bf841-2b98-4df8-95a8-11078ec2ab09.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`
* Solids-> :doc:`Cylinder (Solid) </nodes/solid/cylinder_solid>`
* Solids-> :doc:`Voronoi on Solid </nodes/spatial/voronoi_on_solid_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`