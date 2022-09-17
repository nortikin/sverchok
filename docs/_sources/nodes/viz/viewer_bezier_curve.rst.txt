Bezier Curve Out
================

.. image:: https://user-images.githubusercontent.com/14288520/190408245-df362558-a1a0-44cf-919b-cbe76acee6f3.png
  :target: https://user-images.githubusercontent.com/14288520/190408245-df362558-a1a0-44cf-919b-cbe76acee6f3.png

.. image:: https://user-images.githubusercontent.com/14288520/190408272-286eba6e-1e9c-483e-adc9-7eda320a0905.png
  :target: https://user-images.githubusercontent.com/14288520/190408272-286eba6e-1e9c-483e-adc9-7eda320a0905.png

Functionality
-------------

This node generates Blender Curve objects of Bezier type. Blender's curve
bevelling feature is supported as well.

This node can be used to bring Sverchok's Bezier, NURBS or NURBS-lie curves
into Blender scene.

Note that Blender's Bezier curves can have only one possible degree of 3.
However, Sverchok can automatically elevate degree of the curve, so this node
can also take curves of degree 1 or 2 as input.

Inputs
------

This node has the following inputs:

* **Curve**. Sverchok's Curve object to be generated as Blender object. This
  input is available and mandatory only if **Input mode** parameter is set to
  **Bezier curve** or **BSpline curve**.
* **ControlPoints**. Control points of curve to be generated. This input is
  available and mandatory only when **Input mode** parameter is set to **Curve
  control points** or **Segment control points**.
* **Matrix**. Transformation matrix to be applied to the generated object. By
  default, identity matrix is used (no transformation).
* **Radius**. Bevel radius. The node can process either single value per curve,
  or a specific value per Bezier control point. Default value is 0.0.
* **Tilt**. Tilt value. The node can process either single value per curve,
  or a specific value per Bezier control point. Default value is 0.0.
* **BevelObject**. Blender's Curve object to be used as Bevel object. If not
  specified and **Bevel Depth** is not zero, then round profile will be used.
* **TaperObject**. Blender's Curve object to be used as Taper object. This
  input is optional.

Parameters
----------

This node has the following parameters:

- **Live** - Processing only happens if *update* is ticked
- **Hide View** - Hides current meshes from view
- **Hide Select** - Disables the ability to select these meshes
- **Hide Render** - Disables the renderability of these meshes
- **Base Name** - Base name for Objects and Meshes made by this node
- **Select** - Select every object in 3dview that was created by this Node
- **Material Select** - Assign materials to Objects made by this node
- **Add material** - It creates new material and assigns to generated objects
- **Bevel depth** - Changes the size of the bevel. To disable bevelling, you
  have to set this to 0 and unset **BevelObject** input / parameter.
- **Input mode**. This defines how input curves are provided. The available options are:

   * **Segment control points**. In the **ControlPoints** input, the node will
     expect a list of lists, each of which consists of exactly 4 control points
     for each Bezier segment.
   * **Curve control points**. In the **ControlPoints** input, the node will
     expect a single list of all (concatenated) Bezier segments.
   * **Bezier curve**. In the **Curve** input, the node will expect a
     Sverchok's Bezier Curve object. Such an object can be generated, for
     example, by **Bezier Spline** node.
   * **BSpline curve**. In the **Curve** input, the node will expect Sverchok's
     BSpline curve, i.e. non-rational NURBS curve or NURBS-like curve.

   The default option is **BSpline curve**.

Outputs
-------

This node has the following output:

* **Objects**. Generated Blender's Curve objects.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/136706135-6fb22e96-420b-4c03-9e6c-af1e369c76bf.png
  :target: https://user-images.githubusercontent.com/284644/136706135-6fb22e96-420b-4c03-9e6c-af1e369c76bf.png

.. image:: https://user-images.githubusercontent.com/14288520/190419047-95e1f166-564b-4cc2-ad80-9cc2070a8eb8.png
  :target: https://user-images.githubusercontent.com/14288520/190419047-95e1f166-564b-4cc2-ad80-9cc2070a8eb8.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Curves->Primitives-> :doc:`Polyline </nodes/curve/polyline>`
* Curves-> :doc:`Curve Segment </nodes/curve/curve_segment>`