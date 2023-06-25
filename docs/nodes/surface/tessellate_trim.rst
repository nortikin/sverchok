Tessellate & Trim Surface
=========================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/db74eb59-dd2d-4473-a93d-f80523e604de
  :target: https://github.com/nortikin/sverchok/assets/14288520/db74eb59-dd2d-4473-a93d-f80523e604de

Functionality
-------------

This node "visualizes" the Surface object (turns it into a mesh), by drawing a cartesian (rectangular) grid on it and then cutting (trimming) that grid with the specified Curve object.

The provided trimming curve is supposed to be planar (flat), and be defined in the surface's U/V coordinates frame.

Note that this node is supported since Blender 2.81 only. It will not work in Blender 2.80.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/aa35b243-a3e2-48be-a3bc-a44c7b53ff85
  :target: https://github.com/nortikin/sverchok/assets/14288520/aa35b243-a3e2-48be-a3bc-a44c7b53ff85

Inputs
------

This node has the following inputs:

* **Surface**. The surface to tessellate. This input is mandatory.
* **TrimCurve**. The curve used to trim the surface. This input is mandatory.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/804204ed-6de0-4008-81d7-5b542fdbde9b
  :target: https://github.com/nortikin/sverchok/assets/14288520/804204ed-6de0-4008-81d7-5b542fdbde9b

* **SamplesU**. The number of tessellation samples along the surface's U direction. The default value is 25.
* **SamplesV**. The number of tessellation samples along the surface's V direction. The default value is 25.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/42f920e9-8e07-44ed-989b-d38cf4af0bb6
      :target: https://github.com/nortikin/sverchok/assets/14288520/42f920e9-8e07-44ed-989b-d38cf4af0bb6

* **SamplesT**. The number of points to evaluate the trimming curve at. The default value is 100.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/fcde6bdf-96c9-4cba-ba7d-ec25f066a688
      :target: https://github.com/nortikin/sverchok/assets/14288520/fcde6bdf-96c9-4cba-ba7d-ec25f066a688

Parameters
----------

This node has the following parameters:

* **Curve plane**. The coordinate plane in which the trimming curve is lying.
  The available options are XY, YZ and XZ. The third coordinate is just
  ignored. For example, if XY is selected, then X coordinates of the curve's
  points will be used as surface's U parameter, and Y coordinates of the
  curve's points will be used as surface's V parameter. The default option is
  XY.
* **Cropping mode**. This defines which part of the surface to output:

   * **Inner** - generate the part of the surface which is inside the trimming curve;
   * **Outer** - generate the part of the surface which is outside of the
     trimming curve (make a surface with a hole in it).

   The default option is Inner.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/80801816-0f57-482c-a44e-dc3a1e8b1508
      :target: https://github.com/nortikin/sverchok/assets/14288520/80801816-0f57-482c-a44e-dc3a1e8b1508

* **Accuracy**. This parameter is available in the node's N panel only. This defines the precision of the calculation. The default value is 5. Usually you do not have to change this value.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/13c3f826-b51a-4b85-a5a4-a01614a3815a
    :target: https://github.com/nortikin/sverchok/assets/14288520/13c3f826-b51a-4b85-a5a4-a01614a3815a

Outputs
-------

This node has the following outputs:

* **Vertices**. The vertices of the tessellated surface.
* **Faces**. The faces of the tessellated surface.

Examples of usage
-----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4a8750b8-5e79-4058-ab1d-05c017d04dd0
  :target: https://github.com/nortikin/sverchok/assets/14288520/4a8750b8-5e79-4058-ab1d-05c017d04dd0

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Surfaces-> :doc:`Minimal Surface </nodes/surface/minimal_surface>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Bezier Input </nodes/exchange/bezier_in>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4b9025e8-3ded-44f0-806f-6a62c360fb8f
  :target: https://github.com/nortikin/sverchok/assets/14288520/4b9025e8-3ded-44f0-806f-6a62c360fb8f

---------

Trim some (formula-generated) surface with a circle:

.. image:: https://user-images.githubusercontent.com/284644/79388812-72b50580-7f87-11ea-9eab-2fd205b632d8.png
  :target: https://user-images.githubusercontent.com/284644/79388812-72b50580-7f87-11ea-9eab-2fd205b632d8.png

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Surfaces-> :doc:`Surface Formula </nodes/surface/surface_formula>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Cut a circular hole in the surface:

.. image:: https://user-images.githubusercontent.com/284644/79388815-73e63280-7f87-11ea-9bc9-de200fce3c59.png
  :target: https://user-images.githubusercontent.com/284644/79388815-73e63280-7f87-11ea-9bc9-de200fce3c59.png

* Curves-> :doc:`Circle (Curve) </nodes/curve/curve_circle>`
* Surfaces-> :doc:`Surface Formula </nodes/surface/surface_formula>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
