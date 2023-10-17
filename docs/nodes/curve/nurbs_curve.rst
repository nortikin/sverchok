Build NURBS Curve
=================

.. image:: https://user-images.githubusercontent.com/14288520/206802961-8bfcc0bf-11a3-4835-a217-7ff24e9bbcdf.png
  :target: https://user-images.githubusercontent.com/14288520/206802961-8bfcc0bf-11a3-4835-a217-7ff24e9bbcdf.png

Dependencies
------------

This node can optionally use Geomdl_ library; also it can optionally use FreeCAD_ libraries.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/
.. _FreeCAD: https://www.freecadweb.org/

Functionality
-------------

This node generates a NURBS_ Curve object, given all it's details: control points, weights and knot vector.

.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline
 
.. image:: https://user-images.githubusercontent.com/14288520/206803431-318d41b1-a9f3-43bd-8c5c-d3def98f61fe.png
  :target: https://user-images.githubusercontent.com/14288520/206803431-318d41b1-a9f3-43bd-8c5c-d3def98f61fe.png

Inputs
------

This node has the following inputs:

* **ControlPoints**. NURBS curve control points. This input is mandatory.

    .. image:: https://user-images.githubusercontent.com/14288520/206803792-e8189dd5-e8ef-44c9-b170-1115c31b815f.png
      :target: https://user-images.githubusercontent.com/14288520/206803792-e8189dd5-e8ef-44c9-b170-1115c31b815f.png

* **Weights**. NURBS curve control point weights. If this input is not linked,
  it will be assumed that all control points have weight of 1. This input is
  not available when **Curve mode** parameter is set to **BSpline**.

    .. image:: https://user-images.githubusercontent.com/14288520/206859966-478c9426-5204-4523-a322-998695325b48.png
      :target: https://user-images.githubusercontent.com/14288520/206859966-478c9426-5204-4523-a322-998695325b48.png

* **Knots**. NURBS curve knot vector. This input is not available if
  **Knots** parameter is set to **Auto**.

    .. image:: https://user-images.githubusercontent.com/14288520/206849746-f514f3b0-9d26-4c2a-8ecf-9b33a3be658b.png
      :target: https://user-images.githubusercontent.com/14288520/206849746-f514f3b0-9d26-4c2a-8ecf-9b33a3be658b.png

* **Degree**. NURBS curve degree. The default value is 3.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7551f5c8-372a-4184-a01a-40f212dd5732
      :target: https://github.com/nortikin/sverchok/assets/14288520/7551f5c8-372a-4184-a01a-40f212dd5732

Parameters
----------

This node has the following parameters:

* **Implementation**. This defines the implementation of NURBS mathematics to be used. The available options are:

    .. image:: https://user-images.githubusercontent.com/14288520/206850688-61bae59d-5fdb-426e-93d7-bd6819ab4737.png
      :target: https://user-images.githubusercontent.com/14288520/206850688-61bae59d-5fdb-426e-93d7-bd6819ab4737.png

  * **Geomdl**. Use Geomdl_ library. This option is available only when Geomdl package is installed.
  * **Sverchok**. Use built-in Sverchok implementation.
  * **FreCAD**. Use FreeCAD_ libraries. This option is available only when FreeCAD libraries are installed.
  
  In general, built-in implementation should be faster; but Geomdl implementation is better tested.
  The default option is **Geomdl**, when it is available; otherwise, built-in implementation is used.

* **Curve mode**. This defines the type of curve to be built:

    .. image:: https://user-images.githubusercontent.com/14288520/206850743-a02a37d3-48b5-4000-a0ac-f6037c0cd89e.png
      :target: https://user-images.githubusercontent.com/14288520/206850743-a02a37d3-48b5-4000-a0ac-f6037c0cd89e.png

  * NURBS: rational B-Spline curve (with ability to have different weights of control points)
  * BSpline: non-rational B-Spline curve (all control points have equal weight)

  The default option is NURBS.

* **Knots**. This defines how the knot vector is specified:

    .. image:: https://user-images.githubusercontent.com/14288520/206850990-15e88e1b-180c-4442-973c-988101bf86cd.png
      :target: https://user-images.githubusercontent.com/14288520/206850990-15e88e1b-180c-4442-973c-988101bf86cd.png

  * **Auto**: Knot vector is generated automatically (the curve will be clamped and periodic).
  * **Explicit**: Knot vector is explicitly defined in the **Knots** input of the node.
   
  The default option is Auto.

* **Normalize knots**. If checked, all knotvector values will be rescaled to
  ``[0 .. 1]`` range; so, the curve domain will always be from 0 to 1. If not
  checked, the curve domain will be defined by knotvector.

    .. image:: https://user-images.githubusercontent.com/14288520/206851280-24d632ef-d444-424b-887c-11683ad12307.png
      :target: https://user-images.githubusercontent.com/14288520/206851280-24d632ef-d444-424b-887c-11683ad12307.png

* **Cyclic**. Whether the curve should be cyclic (closed). This option is
  available only when the **Knots** parameter is set to **Auto**. Unchecked by
  default.

    .. image:: https://user-images.githubusercontent.com/14288520/206852256-57bd4b12-6338-4be1-9a49-2b511b6de5f8.png
      :target: https://user-images.githubusercontent.com/14288520/206852256-57bd4b12-6338-4be1-9a49-2b511b6de5f8.png

Outputs
-------

This node has the following outputs:

* **Curve**. The generated NURBS curve object.
* **Knots**. NURBS curve knotvector.

    .. image:: https://user-images.githubusercontent.com/14288520/206858099-db937584-edf4-4aa0-96fa-6ed637255c9f.png
      :target: https://user-images.githubusercontent.com/14288520/206858099-db937584-edf4-4aa0-96fa-6ed637255c9f.png

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/86948496-a6f32900-c166-11ea-850f-5977d5a0fea8.png
  :target: https://user-images.githubusercontent.com/284644/86948496-a6f32900-c166-11ea-850f-5977d5a0fea8.png

* Curves-> :doc:`Evaluate Curve </nodes/curve/eval_curve>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`

---------

Updated example:

.. image:: https://user-images.githubusercontent.com/14288520/206858775-33daf322-7f68-4883-97c6-688bedda897c.png
  :target: https://user-images.githubusercontent.com/14288520/206858775-33daf322-7f68-4883-97c6-688bedda897c.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`