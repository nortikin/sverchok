Blend Curves
============

.. image:: https://user-images.githubusercontent.com/14288520/211316021-6e449b78-4c6a-41a6-b0c5-39130a994131.png
  :target: https://user-images.githubusercontent.com/14288520/211316021-6e449b78-4c6a-41a6-b0c5-39130a994131.png

Functionality
-------------

This node takes two or more Curve objects, and connects them by adding new
curve(s) in the middle, to generate a smooth blending. For example, the end of
the first curve is connected to the beginning of the second curve. Generated
blending curves are Bezier curves. It is possible to define how smooth the
connection between initial curves and blending curve(s) should be.  

.. image:: https://user-images.githubusercontent.com/14288520/211318302-3d60c8a6-7ea0-40e0-b499-103434be8ddb.png
  :target: https://user-images.githubusercontent.com/14288520/211318302-3d60c8a6-7ea0-40e0-b499-103434be8ddb.png

Inputs
------

This node has the following inputs:

* **Curve1**. First curve to be blended. This input is available and mandatory
  only if **Blend** parameter is set to **Two curves**.
* **Curve2**. Second curve to be blended. This input is available and mandatory
  only if **Blend** parameter is set to **Two curves**.

.. image:: https://user-images.githubusercontent.com/14288520/211320056-fa1479a3-9008-4a2a-bdea-ee06288fd553.png
  :target: https://user-images.githubusercontent.com/14288520/211320056-fa1479a3-9008-4a2a-bdea-ee06288fd553.png

* **Curves**. List of curves to be blended. This input is available and
  mandatory only if **Blend** parameter is set to **List of curves**.

.. image:: https://user-images.githubusercontent.com/14288520/211327893-7146c794-134c-4bb6-a7af-8df174ffd096.png
  :target: https://user-images.githubusercontent.com/14288520/211327893-7146c794-134c-4bb6-a7af-8df174ffd096.png

* **Factor1**. This input is available and mandatory only if **Blend**
  parameter is set to **Two curves**, and **Continuity** parameter is set to
  **Tangency**. This defines the strength with which the tangent vector of the
  first curve at it's end point will affect the generated blending curve. The
  default value is 1.0.
* **Factor2**. This input is available and mandatory only if **Blend**
  parameter is set to **Two curves**, and **Continuity** parameter is set to
  **Tangency**. This defines the strength with which the tangent vector of the
  second curve at it's starting point will affect the generated blending curve.
  The default value is 1.0.

.. image:: https://user-images.githubusercontent.com/14288520/211328655-e60a86ad-d435-4e22-919d-55ab96ca5ccf.png
  :target: https://user-images.githubusercontent.com/14288520/211328655-e60a86ad-d435-4e22-919d-55ab96ca5ccf.png

* **Parameter**. This input is available only if **Continuity** parameter is
  set to **BiArc**. This defines the value of P parameter of the family of
  biarc_ curves, that are generated as blending curves. The default value is 1.0.

.. _biarc: https://en.wikipedia.org/wiki/Biarc

.. image:: https://user-images.githubusercontent.com/14288520/211330393-602e757b-5897-49a2-8d33-3fa24adbd545.png
  :target: https://user-images.githubusercontent.com/14288520/211330393-602e757b-5897-49a2-8d33-3fa24adbd545.png

Parameters
----------

This node has the following parameters:

* **Continuity**. This defines how smooth the connection between initial curves
  and generated blending curves should be. The available options are:

  * **C0 - Position**. Blending curve starts at the end of first curve and ends
    at the beginning of the second curve, but no attempts are made to make
    these connections smooth. As a result, the blending curve is always a
    segment of a straight line.

    .. image:: https://user-images.githubusercontent.com/14288520/211332041-419c7002-28bb-45ca-b507-238ff4f13dcd.png
      :target: https://user-images.githubusercontent.com/14288520/211332041-419c7002-28bb-45ca-b507-238ff4f13dcd.png

  * **G1 - Tangency**. The blending curves are generated so that the tangent
    vectors of the curves are equal at their meeting points. The generated
    curves are cubic Bezier curves.

    .. image:: https://user-images.githubusercontent.com/14288520/211333493-3dfe0a3f-1143-429f-bd1c-7a9c04ce45bf.png
      :target: https://user-images.githubusercontent.com/14288520/211333493-3dfe0a3f-1143-429f-bd1c-7a9c04ce45bf.png

  * **G1 - Bi Arc**. The blending curves are generated as biarc_ curves, i.e.
    pairs of circular arcs; they are generated so that the tanent vectors of
    the curves are equal at their meeting points.

    .. image:: https://user-images.githubusercontent.com/14288520/211338021-ae8c68d9-bc02-4323-8cc5-8888c0c8ad33.png
      :target: https://user-images.githubusercontent.com/14288520/211338021-ae8c68d9-bc02-4323-8cc5-8888c0c8ad33.png

  * **C2 - Smooth Normals**. The blending curves are generated so that 1) tangent
    vectors of the curves are equal at the meeting points; 2) second
    derivatives of the curves are also equal at the meeting points. Thus,
    normal and binormal vectors of the curves are equal at their meeting
    points. The generated curves are Bezier curves of fifth order.

    .. image:: https://user-images.githubusercontent.com/14288520/211343223-f0c9bc79-bf16-4833-a3cd-6b651d52d099.png
      :target: https://user-images.githubusercontent.com/14288520/211343223-f0c9bc79-bf16-4833-a3cd-6b651d52d099.png

  * **C3 - Smooth Curvature**. The blending curves are generated so that 1) tangent
    vectors of the curves are equal at the meeting points; 2) second and third
    derivatives of the curves are also equal at the meeting points. Thus,
    normal and binormal vectors of the curves, as well as curvatures of the
    curves, are equal at their meeting points. The generated curves are Bezier
    curves of order 7.

    .. image:: https://user-images.githubusercontent.com/14288520/211344080-1146e033-7296-4f92-9bd5-f36348d7ebd7.png
      :target: https://user-images.githubusercontent.com/14288520/211344080-1146e033-7296-4f92-9bd5-f36348d7ebd7.png

  * **G2 - Curvature**. This means continuous curvature. Curvature comb rim
    line is continuous, but not smooth. In this sense, this mode is similar to
    "C2 - Smooth Normals" mode. But with G2 mode, the blending curve does not
    go so far from touching points as in C2 or C3 mode.

    .. image:: https://user-images.githubusercontent.com/284644/210864882-de4a8a95-f73a-42d3-b30f-1f01ad7a6c33.png
      :target: https://user-images.githubusercontent.com/284644/210864882-de4a8a95-f73a-42d3-b30f-1f01ad7a6c33.png

  The default value is **1 - Tangency**.

* **Blend**. These defines how the curves to be joined are provided. The available options are:

  * **Two curves**. The node will blend two curves, which are provided in
    inputs **Curve1** and **Curve2**, correspondingly.
  * **List of curves**. The node will blend arbitrary number of curves, which
    are provided in the **Curves** input.

    .. image:: https://user-images.githubusercontent.com/14288520/211346162-2f59795b-39bc-4d5b-83e6-1a276e84a067.png
      :target: https://user-images.githubusercontent.com/14288520/211346162-2f59795b-39bc-4d5b-83e6-1a276e84a067.png

  The default value is **Two curves**.

* **Concatenate**. If checked, then the node will output all initial curves
  together with generated blending curves, concatenated into one curve.
  Otherwise, original curves (optionally) and generated curves will be output
  as separate Curve objects. Checked by default.

  .. image:: https://user-images.githubusercontent.com/14288520/211353990-25dc1a7a-4952-4329-8f91-ce54a2139e99.png
    :target: https://user-images.githubusercontent.com/14288520/211353990-25dc1a7a-4952-4329-8f91-ce54a2139e99.png

* **Cyclic**. This parameter is available only when the **Blend** parameter is set
  to **List of curves**. If checked, then the node will connect the end of last
  curve to the beginning of the first curve. Unchecked by default.

  .. image:: https://user-images.githubusercontent.com/14288520/211355312-faadcef7-557b-4c8b-ae97-f10e68db5439.png
    :target: https://user-images.githubusercontent.com/14288520/211355312-faadcef7-557b-4c8b-ae97-f10e68db5439.png

* **Output source curves**. This parameter is available only when the **Blend**
  parameter is set to **List of curves**, and **Concatenate** parameter is not
  checked. If **Output source curves** is enabled, then the node will output
  original curves in single list with generated blending curves - for example,
  ``[Original curve 1; Blending curve 1; Original curve 2; Blending curve 2;
  Original curve 3]``. Otherwise, the node will output generated blending
  curves only. Checked by default.

.. image:: https://user-images.githubusercontent.com/14288520/211358649-4e10c9f6-b70f-4004-af47-2a5b62cdaf16.png
  :target: https://user-images.githubusercontent.com/14288520/211358649-4e10c9f6-b70f-4004-af47-2a5b62cdaf16.png

Outputs
-------

This node has the following outputs:

* **Curve**. The generated curve (or list of curves).
* **ControlPoints**. Control points of all generated blending curves.

.. image:: https://user-images.githubusercontent.com/14288520/211362482-670f165a-da6b-46bd-b7fc-266b1e918018.png
  :target: https://user-images.githubusercontent.com/14288520/211362482-670f165a-da6b-46bd-b7fc-266b1e918018.png

Example of usage
----------------

Generate two cubic curves from mesh objects (one of them is white - selected,
another is black - unselected); and blend them together with a smooth curve:

.. image:: https://user-images.githubusercontent.com/14288520/211370981-6db2f1b3-666d-422d-a5f9-84479dcb5042.png
  :target: https://user-images.githubusercontent.com/14288520/211370981-6db2f1b3-666d-422d-a5f9-84479dcb5042.png

* Curves-> :doc:`Cubic Spline </nodes/curve/cubic_spline>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/211372837-5f53efaf-6325-4a03-add5-8559b083df4c.png
  :target: https://user-images.githubusercontent.com/14288520/211372837-5f53efaf-6325-4a03-add5-8559b083df4c.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

---------

Cycle one curve

.. image:: https://user-images.githubusercontent.com/14288520/211379616-f43aac03-c3a5-4023-8f51-e243990c74e4.png
  :target: https://user-images.githubusercontent.com/14288520/211379616-f43aac03-c3a5-4023-8f51-e243990c74e4.png

* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
