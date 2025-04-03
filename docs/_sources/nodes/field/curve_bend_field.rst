Bend Along Curve Field
======================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/24e3fe93-4eb7-4cea-9d80-1b97e32802ab
  :target: https://github.com/nortikin/sverchok/assets/14288520/24e3fe93-4eb7-4cea-9d80-1b97e32802ab

Functionality
-------------

This node generates a Vector Field, which bends some part of 3D space along the
provided Curve object.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/9b3e1f64-c352-487a-a9ef-86677644059f
  :target: https://github.com/nortikin/sverchok/assets/14288520/9b3e1f64-c352-487a-a9ef-86677644059f

It is in general not a trivial task to rotate a 3D object along a vector,
because there are always 2 other axes of object and it is not clear where
should they be directed to. So, this node supports 3 different algorithms of
object rotation calculation. In many simple cases, all these algorithms will
give exactly the same result. But in more complex setups, or in some corner
cases, results can be very different. So, just try all algorithms and see which
one fits you better.

* "**Frenet**" or "**Zero-Twist**" algorithms give very good results in case when
  extrusion curve has non-zero curvature in all points. If the extrusion curve
  has zero curvature points, or, even worse, it has straight segments, these
  algorithms will either make "flipping" surface, or give an error.
 
    .. image:: https://github.com/nortikin/sverchok/assets/14288520/cd204b2f-438f-4cef-bdea-1e10b2c0bf85
      :target: https://github.com/nortikin/sverchok/assets/14288520/cd204b2f-438f-4cef-bdea-1e10b2c0bf85

* "**Householder**", "**Tracking**" and "**Rotation difference**" algorithms are
  "curve-agnostic", they work independently of curve by itself, depending only
  on tangent direction. They give "good enough" result (at least, without
  errors or sudden flips) for all extrusion curves, but may make twisted
  surfaces in some special cases.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/1a2a405b-e669-4470-af5f-bace59d4c885
      :target: https://github.com/nortikin/sverchok/assets/14288520/1a2a405b-e669-4470-af5f-bace59d4c885

* "**Track normal**" algorithm is supposed to give good results without twisting
  for all extrusion curves. It will give better results with higher values of
  "resolution" parameter, but that may be slow.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c3964449-d1a7-4080-b5c1-e314460a3b1c
      :target: https://github.com/nortikin/sverchok/assets/14288520/c3964449-d1a7-4080-b5c1-e314460a3b1c

Inputs
------

This node has the following inputs:

* **Curve**. The curve to bend the space along. This input is mandatory.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/bd514fa4-06f8-4848-9640-b9daa8680d5f
      :target: https://github.com/nortikin/sverchok/assets/14288520/bd514fa4-06f8-4848-9640-b9daa8680d5f

* **Src T Min**. The minimum value of the orientation coordinate, where the
  bending should begin. For example, if **Orientation axis** parameter is set
  to **Z**, this is the minimum value of **Z** coordinate. The default value is **-1.0**.
* **Src T Max**. The maximum value of the orientation coordinate, where the
  bending should end. For example, if **Orientation axis** parameter is set to
  **Z**, this is the maximum value of **Z** coordinate. The default value is **1.0**.

    Cylinder Z start do not equal Src T min

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/8d454251-d08a-4fc6-a5d8-ff0806996c7c
      :target: https://github.com/nortikin/sverchok/assets/14288520/8d454251-d08a-4fc6-a5d8-ff0806996c7c

    Cylinder Z start equal "Src T min" and Cylinder Z top equal "Src T max" and Cylinder Height equal curve's T Range

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/dbadce3f-e328-48c7-8135-db6419dfe4c0
      :target: https://github.com/nortikin/sverchok/assets/14288520/dbadce3f-e328-48c7-8135-db6419dfe4c0

    * Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
    * Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
    * Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`

* **Resolution**. The number of samples along the curve, used to calculate
  curve length parameter. This input is only available when **Scale along
  curve** parameter is set to **Curve length**. The higher the value is, the
  more precise is the calculation, but more time it is going to take. The
  default value is 50.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/d1bc55b1-2a19-4d34-a4ad-7573714fb584
      :target: https://github.com/nortikin/sverchok/assets/14288520/d1bc55b1-2a19-4d34-a4ad-7573714fb584

The field bends the part of space which is between **Src T Min** and **Src T
Max**, along the curve. For example, with default settings, the source part of
space is the space between Z = -1 and Z = 1. The behaviour of the field outside
of these bounds is not guaranteed.

Changing Cylinder height and position and Changing of T min/max (see example 2)

.. image:: https://github.com/nortikin/sverchok/assets/14288520/6bebd03a-e0af-4f52-b6f7-b0c84a4d0782
  :target: https://github.com/nortikin/sverchok/assets/14288520/6bebd03a-e0af-4f52-b6f7-b0c84a4d0782

Parameters
----------

This node has the following parameters:

* **Orientation**. Which axis of the source space should be elongated along the
  curve. The available values are X, Y and Z. The default value is Z. When the
  **Algorithm** parameter is set to **Zero-Twist** or **Frenet**, the only
  available option is Z.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/f31f02cb-6cbe-464a-a90c-be7bfb22eac1
      :target: https://github.com/nortikin/sverchok/assets/14288520/f31f02cb-6cbe-464a-a90c-be7bfb22eac1

* **Scale all axis**. If checked, all three axis of the source space will be
  scaled by the same amount as is required to fit the space between **Src T
  Min** and **Src T Max** to the curve length. Otherwise, only orientation axis
  will be scaled. Checked by default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/3adefa0a-1b43-494c-bb75-14c63042f596
      :target: https://github.com/nortikin/sverchok/assets/14288520/3adefa0a-1b43-494c-bb75-14c63042f596

    * T Min, T Max: Number-> :doc:`A Number </nodes/number/numbers>`
    * CEIL X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`

* **Algorithm**. Rotation calculation algorithm. Available values are:

  * **Householder**: calculate rotation by using Householder's reflection matrix
    (see Wikipedia_ article).                   
  * **Tracking**: use the same algorithm as in Blender's "TrackTo" kinematic
    constraint. This algorithm gives you a bit more flexibility comparing to
    other, by allowing to select the Up axis.                                                         
  * **Rotation difference**: calculate rotation as rotation difference between two
    vectors.                                         
  * **Frenet**: rotate the space according to curve's Frenet frame.
  * **Zero-Twist**: rotate the space according to curve's "zero-twist" frame.
  * **Track normal**: try to maintain constant normal direction by tracking it along the curve.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/17a5b971-3242-49e1-8a22-d83fee3d9b7a
      :target: https://github.com/nortikin/sverchok/assets/14288520/17a5b971-3242-49e1-8a22-d83fee3d9b7a

  Default value is Householder.

* **Up axis**.  Axis of donor object that should point up in result. This
  parameter is available only when Tracking algorithm is selected.  Value of
  this parameter must differ from **Orientation** parameter, otherwise you will
  get an error. Default value is X.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/a131d717-deb6-4d07-9595-c525ec3c4eda
      :target: https://github.com/nortikin/sverchok/assets/14288520/a131d717-deb6-4d07-9595-c525ec3c4eda

* **Scale along curve**. This defines how the scaling of the space along the
  curve is to be calculated. The available options are:

   * **Curve parameter**. Scale the space proportional to curve's T parameter.
   * **Curve length**. Scale the space proportional to curve's length. This
     usually gives more natural results, but takes more time to compute.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/45b2c295-08a7-4600-99c4-52d76a80f742
      :target: https://github.com/nortikin/sverchok/assets/14288520/45b2c295-08a7-4600-99c4-52d76a80f742

  The default option is **Curve parameter**.

.. _Wikipedia: https://en.wikipedia.org/wiki/QR_decomposition#Using_Householder_reflections

Outputs
-------

This node has the following output:

* **Field**. The generated bending vector field.

Examples of usage
-----------------

Example 1 of description:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a73f3c58-9af4-4d05-baff-7ea27a35b853
  :target: https://github.com/nortikin/sverchok/assets/14288520/a73f3c58-9af4-4d05-baff-7ea27a35b853

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/628d3de4-3f64-4c5f-a685-ccb883869064
  :target: https://github.com/nortikin/sverchok/assets/14288520/628d3de4-3f64-4c5f-a685-ccb883869064

---------

Example 2 of description

.. image:: https://github.com/nortikin/sverchok/assets/14288520/fa0af069-1b6c-4b23-b172-e862d214a066
  :target: https://github.com/nortikin/sverchok/assets/14288520/fa0af069-1b6c-4b23-b172-e862d214a066

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Curves-> :doc:`Reparametrize Curve </nodes/curve/reparametrize>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* CEIL:  Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* T Min, T Max: Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Text-> :doc:`String Tools </nodes/text/string_tools>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

---------

Bend a cube along some closed curve:

.. image:: https://user-images.githubusercontent.com/284644/79593221-93e73480-80f4-11ea-8c14-7f1511b1bd7b.png
  :target: https://user-images.githubusercontent.com/284644/79593221-93e73480-80f4-11ea-8c14-7f1511b1bd7b.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`

---------

It is possible to use one field to bend several objects:

.. image:: https://user-images.githubusercontent.com/284644/79593228-95186180-80f4-11ea-930f-59f3f124da63.png
  :target: https://user-images.githubusercontent.com/284644/79593228-95186180-80f4-11ea-930f-59f3f124da63.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`

