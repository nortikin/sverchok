Offset Curve
============

.. image:: https://user-images.githubusercontent.com/14288520/210442183-f0ed37ab-79d7-4062-91b4-175595212016.png
  :target: https://user-images.githubusercontent.com/14288520/210442183-f0ed37ab-79d7-4062-91b4-175595212016.png

Functionality
-------------

This node generates a Curve, calculated as offset of another Curve by some
amount. It takes all points of original curve and moves them in direction
perpendicular to curve's tangent. In other words, this "offsetting" operation
can be described as extruding one single point along the curve.

When we say "offset all points of curve in direction perpendicular to curve's
tangent", there is a good question: where exactly? There are several algorithms
how to define a reference frame associated with curve's point and curve's
tangent direction. In simplest cases, all of them will give very similar
results. In more complex cases, results will be very different. Different
algorithms give best results in different cases:

* **Frenet** or **Zero-Twist** algorithms give very good results in case when
  extrusion curve has non-zero curvature in all points (The curvature of a
  straight line is zero). If the extrusion curve
  has zero curvature points, or, even worse, it has straight segments, these
  algorithms will either make "flipping" surface, or give an error.

.. image:: https://user-images.githubusercontent.com/14288520/210894147-00b44d39-6842-4a75-80cc-2e0b3a1e2ed2.png
  :target: https://user-images.githubusercontent.com/14288520/210894147-00b44d39-6842-4a75-80cc-2e0b3a1e2ed2.png

* **Householder**, **Tracking** and **Rotation difference** algorithms are
  "curve-agnostic", they work independently of curve by itself, depending only
  on tangent direction. They give "good enough" result (at least, without
  errors or sudden flips) for all extrusion curves, but may make twisted
  surfaces in some special cases.

.. image:: https://user-images.githubusercontent.com/14288520/210892606-1e623971-82b3-4b97-a0a4-a8bda04ddc14.png
  :target: https://user-images.githubusercontent.com/14288520/210892606-1e623971-82b3-4b97-a0a4-a8bda04ddc14.png

* **Track normal** algorithm is supposed to give good results without twisting
  for all extrusion curves. It will give better results with higher values of
  "resolution" parameter, but that may be slow.

.. image:: https://user-images.githubusercontent.com/14288520/210893380-e8e5e7a3-fc7e-4b98-b712-88b64dfc90a3.png
  :target: https://user-images.githubusercontent.com/14288520/210893380-e8e5e7a3-fc7e-4b98-b712-88b64dfc90a3.png

* **Specified plane** algorithm selects offset direction vector so that it
  satisfies two conditions: 1) it is perpendicular to curve's tangent vector,
  and 2) it lies in so-called "offset operation plane", which is specified by
  user by providing the normal vector of such plane (in other words, offset
  direction vector is perpendicular to normal vector provided by user). This
  algorithm is supposed to give good results for planar or almost planar
  curves. The resulting curve may have twists in places where original curve's
  tangent vector is parallel to offset operation plane's normal (i.e. tangent
  is perpendicular to offset operation plane). Hint: you may use "Linear
  approximation" node to automatically calculate normal vector of offset
  operation plane.

https://gist.github.com/0f8f8c8d4b0dca3a403534fb1c423305

.. image:: https://user-images.githubusercontent.com/14288520/210561951-0a2a47f8-34ba-4a2f-adb7-d5db19da352b.png
  :target: https://user-images.githubusercontent.com/14288520/210561951-0a2a47f8-34ba-4a2f-adb7-d5db19da352b.png

Animation for "specified plane" mode (press image to open):

.. image:: https://user-images.githubusercontent.com/14288520/210567502-07ed3926-8eef-4fdd-b593-8b1fdb340cf0.png
  :target: https://user-images.githubusercontent.com/14288520/210567213-8e792e30-3794-4398-a298-82ea0c11c150.gif

For all algorithms, reference frame's Z axis is always pointing along curve's
tangent direction. Two other axes are always perpendicular to tangent
direction, but where exactly they are pointing - depends on the algorithm. For
Frenet algorithm, X axis is pointing along curve's normal and Y axis is
pointing along curve's binormal.

Curve domain and parametrization: the same as of original curve.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be offset. This input is mandatory.
* **Offset**. Offset amount. This input is available only if **Algorithm**
  parameter is set to **Specified plane**, or the **Direction** parameter is
  set to **X (Normal)** or **Y (Binormal)**. The input is not available when
  **Offset type** parameter is set to **Variable**. The default value is 0.1.

.. image:: https://user-images.githubusercontent.com/14288520/210970519-a9710a31-43d2-427d-bb6b-4bfb4d4258eb.png
  :target: https://user-images.githubusercontent.com/14288520/210970519-a9710a31-43d2-427d-bb6b-4bfb4d4258eb.png


* **OffsetCurve**. The curve defining the offset amount for each point of
  original curve. The curve is supposed to lie in XOY coordinate plane. The
  node uses this curve's mapping of T parameter to Y coordinate. For parameter
  of this offset curve, the node will use either parameter of the original
  curve, or it's length share, depending on **Offset curve type** parameter.
  This input is available and mandatory only if **Offset type** parameter is
  set to **Variable**.

.. image:: https://user-images.githubusercontent.com/14288520/210972964-d27f19cc-6caf-4ff2-b967-3983c30d48eb.png
  :target: https://user-images.githubusercontent.com/14288520/210972964-d27f19cc-6caf-4ff2-b967-3983c30d48eb.png

* **Vector**. Offset direction vector. This input is available only if
  **Algorithm** parameter is set to **Specified plane**, or the **Direction**
  parameter is set to **Custom (N/B/T)**.

  * For **Specified plane** algorithm, this input defines the normal vector of
    offset operation plane (offset direction vector will be always
    perpendicular to it).

    .. image:: https://user-images.githubusercontent.com/14288520/210975432-3eb5d15b-310f-4b85-8f2f-c84e855f2d58.png
      :target: https://user-images.githubusercontent.com/14288520/210975432-3eb5d15b-310f-4b85-8f2f-c84e855f2d58.png

    .. image:: https://user-images.githubusercontent.com/14288520/210978406-fc76c02c-4ab0-4b64-9f0f-060fb57bc9bb.gif
      :target: https://user-images.githubusercontent.com/14288520/210978406-fc76c02c-4ab0-4b64-9f0f-060fb57bc9bb.gif


  * For other algorithms, Components of the vector are used within curve frame,
    calculated according to **Algorithm** parameter. For Frenet algorithm, X
    component of the vector represents offset along curve's normal, Y component
    of the vector represents offset along curve's binormal, and Z component of
    the vector represents offset along curve's tangent.
    
    .. image:: https://user-images.githubusercontent.com/14288520/211044420-85db6cd8-5d8e-4f5a-bab2-8f642ba1ee7b.png
      :target: https://user-images.githubusercontent.com/14288520/211044420-85db6cd8-5d8e-4f5a-bab2-8f642ba1ee7b.png

  The default value is ``(0.1, 0, 0)``.
      
* **Resolution**. Number of samples for **Zero-Twist** or **Track normal**
  rotation algorithm calculation. It is also used for curve length calculation,
  when **Offset type** parameter is set to **Variable**, and **Offset curve
  use** parameter is set to **Curve length**. The more the number is, the more
  precise the calculation is, but the slower. The default value is 50. This
  input is only available when **Algorithm** parameter is set to **Zero-Twist**
  or **Track normal**, or when **Offset type** parameter is set to **Variable**
  and **Offset curve use** parameter is set to **Curve length**.

.. image:: https://user-images.githubusercontent.com/14288520/211007523-82c07800-6c0f-4a47-8313-ef51da2b3aaa.png
  :target: https://user-images.githubusercontent.com/14288520/211007523-82c07800-6c0f-4a47-8313-ef51da2b3aaa.png

.. image:: https://user-images.githubusercontent.com/14288520/211007253-36290b0b-de32-4606-bf5b-35cbf6a57e33.gif
  :target: https://user-images.githubusercontent.com/14288520/211007253-36290b0b-de32-4606-bf5b-35cbf6a57e33.gif

Parameters
----------

This node has the following parameters:

* **Algorithm**. Curve frame calculation algorithm. The available options are:

https://gist.github.com/0ca7f735f7d85f5ed6ff456b89f088ff

  * **Frenet**. Rotate the profile curve according to Frenet frame of the
    extrusion curve (press image to animate). 
    
    .. image:: https://user-images.githubusercontent.com/14288520/211011794-3cdaecce-991c-4e10-a551-efad0b25c277.png 
      :target: https://user-images.githubusercontent.com/14288520/211011663-0150f048-ab33-4591-a593-4097a17fa570.gif

  * **Zero-Twist**. Rotate the profile curve according to "zero-twist" frame of
    the extrusion curve.

    .. image:: https://user-images.githubusercontent.com/14288520/211012243-84eaf3e9-187d-43d9-96bc-1677db73294e.png
      :target: https://user-images.githubusercontent.com/14288520/211012646-108ade70-735f-4efe-a5bf-2adf8f228805.gif

  * **Householder**. Calculate rotation by using Householder's reflection matrix
    (see Wikipedia_ article).               

    .. image:: https://user-images.githubusercontent.com/14288520/211013397-b606e1eb-3b96-49a2-83f9-120fa3434f01.png
      :target: https://user-images.githubusercontent.com/14288520/211013591-1bc61f00-bfd8-4b3a-b4b2-5d964d32a1c3.gif

  * **Tracking**. Use the same algorithm as in Blender's "TrackTo" kinematic
    constraint. This node currently always uses X as the Up axis.

    .. image:: https://user-images.githubusercontent.com/14288520/211013932-f1d03a0b-9685-4250-b2ce-334084054698.png
      :target: https://user-images.githubusercontent.com/14288520/211014189-8315f06f-8c4b-4caf-bcf0-884ee99a893c.gif

  * **Rotation difference**. Calculate rotation as rotation difference between two
    vectors.                    

    .. image:: https://user-images.githubusercontent.com/14288520/211032437-537b9d20-35e6-49f8-80e7-9e9694dd8492.png
      :target: https://user-images.githubusercontent.com/14288520/211032854-08120c6f-85ef-4b20-9845-f1faa8fce5b2.gif

  * **Track normal**. Try to maintain constant normal direction by tracking it
    along the curve. 

    .. image:: https://user-images.githubusercontent.com/14288520/211033494-833df34c-a151-42ff-aed0-86bb20895e1d.png
      :target: https://user-images.githubusercontent.com/14288520/211033788-c94a2f21-e151-41a1-99d4-9f65da89e4f5.gif

  * **Specified plane**. Offset direction vector will be always lying in a
    plane which is defined by normal vector provided in **Vector** input. (https://gist.github.com/c000254e670af7a3435e84ca301ded81)

    .. image:: https://user-images.githubusercontent.com/14288520/211036054-327073ee-bb27-44c0-b34a-47055731736a.png
      :target: https://user-images.githubusercontent.com/14288520/211037516-2c25c468-5751-45d2-a9a9-6ee2e175421f.gif

  The default option is **Householder**.

* **Direction**. This defines offset direction. This input is not available
  when **Algorithm** parameter is set to **Specified plane**. The available
  options are:

   * **X (Normal)**. Offset along curve reference frame's X axis (for Frenet
     frame - curve normal).
   * **Y (Binormal)**. Offset along curve reference frame's Y axis (for Frenet
     frame - curve binormal).
   * **Custom (N/B/T)**. Offset along user-provided vector.

   The default option is **X (Normal)**.

.. _Wikipedia: https://en.wikipedia.org/wiki/QR_decomposition#Using_Householder_reflections

.. image:: https://user-images.githubusercontent.com/14288520/211070103-24aa4724-7677-4733-8740-2b81b2c940a9.png
  :target: https://user-images.githubusercontent.com/14288520/211070103-24aa4724-7677-4733-8740-2b81b2c940a9.png

Outputs
-------

This node has the following output:

* **Curve**. The offsetted curve.

.. image:: https://user-images.githubusercontent.com/14288520/211048162-b8e636c8-34a0-40f0-9885-6c18f50f5df4.png
  :target: https://user-images.githubusercontent.com/14288520/211048162-b8e636c8-34a0-40f0-9885-6c18f50f5df4.png


Examples of usage
-----------------

Offset one curve with several different offset amounts:

.. image:: https://user-images.githubusercontent.com/14288520/211057398-9c88a831-d9e6-4f47-b306-bc29f5a5153f.png
  :target: https://user-images.githubusercontent.com/14288520/211057398-9c88a831-d9e6-4f47-b306-bc29f5a5153f.png

* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

---------

Example of **Custom (N/B/T)** mode usage:

.. image:: https://user-images.githubusercontent.com/14288520/211058665-ba9623df-b1db-4751-b773-505f5f6ee5d8.png
  :target: https://user-images.githubusercontent.com/14288520/211058665-ba9623df-b1db-4751-b773-505f5f6ee5d8.png

* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Example of **Specified plane** mode usage. Here **Linear approximation** node
is used to automatically detect the plane where the curve is lying (mostly); it
outputs a normal vector, which is nearly OY axis, so the offset operation plane
will be nearly XOZ. Note that the offsetted curve has a twist in a place where
the tangent of original curve is perpendicular to offset operation plane.

.. image:: https://user-images.githubusercontent.com/14288520/211066233-f38a07f4-be2e-4c04-85da-79ad36d32d52.png
  :target: https://user-images.githubusercontent.com/14288520/211066233-f38a07f4-be2e-4c04-85da-79ad36d32d52.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Analyzers-> :doc:`Linear Approximation </nodes/analyzer/linear_approx>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Example of **Variable** offset mode usage:

.. image:: https://user-images.githubusercontent.com/14288520/211068041-f2f513fc-067f-4d4a-8e2d-1235b485e86c.png
  :target: https://user-images.githubusercontent.com/14288520/211068041-f2f513fc-067f-4d4a-8e2d-1235b485e86c.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Surfaces-> :doc:`Curve Formula </nodes/curve/curve_formula>`
* Analyzers-> :doc:`Linear Approximation </nodes/analyzer/linear_approx>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/211071408-a2f9312f-e857-4141-9646-c133b2cb9c73.gif
  :target: https://user-images.githubusercontent.com/14288520/211071408-a2f9312f-e857-4141-9646-c133b2cb9c73.gif