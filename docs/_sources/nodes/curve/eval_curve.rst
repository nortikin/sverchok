Evaluate Curve
==============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/7b2ecf3d-f82c-45d1-8dd4-75cf55612637
  :target: https://github.com/nortikin/sverchok/assets/14288520/7b2ecf3d-f82c-45d1-8dd4-75cf55612637

Functionality
-------------

This node calculates the point on the curve at a given value of curve
parameter. It can also automatically calculate a set of points at a series of
evenly distributed values of curve parameter.

You will be using this node a lot, to visualize any curve, or to convert it to mesh.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/1489fe08-9016-4cb3-91f6-b01c6379bbad
  :target: https://github.com/nortikin/sverchok/assets/14288520/1489fe08-9016-4cb3-91f6-b01c6379bbad

* Curves-> :doc:`Rounded Rectangle </nodes/curve/rounded_rectangle>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Inputs
------

This node has the following inputs:

* **Curve**. Curve to be evaluated. This input is mandatory.
* **T**. The value of curve parameter to calculate the point on the curve for.
  This input is available only when **Mode** parameter is set to **Manual**.
  Sensible range values for this input corresponds to the domain of the curve
  provided in the **Curve** input. [:doc:`Curve Domain </nodes/curve/curve_range>`]
* **Samples**. Number of curve parameter values to calculate the curve points
  for. This input is available only when **Mode** parameter is set to **Auto**.
  The default value is 50.

Parameters
----------

This node has the following parameters:

* **Mode**:

  * **Automatic**. Calculate curve points for the set of curve parameter values which are evenly distributed within curve domain.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/da5efc27-6df0-4f91-868e-9ae38ac585f1
      :target: https://github.com/nortikin/sverchok/assets/14288520/da5efc27-6df0-4f91-868e-9ae38ac585f1

    * Curves-> :doc:`Rounded Rectangle </nodes/curve/rounded_rectangle>`
    * Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

  * **Manual**. Calculate curve point for the provided value of curve parameter.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/0dd779ba-4e86-4853-b430-80c1ebb4d0d5
      :target: https://github.com/nortikin/sverchok/assets/14288520/0dd779ba-4e86-4853-b430-80c1ebb4d0d5

    * Number-> :doc:`Number Range </nodes/number/number_range>`
    * Curves-> :doc:`Rounded Rectangle </nodes/curve/rounded_rectangle>`
    * Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

* **Join**. If checked, then the node will output one single list of objects
  for all provided curves - for example, data in **Verties** output will have
  nesting level 3 even if data in **Curve** input had nesting level 2.
  Otherwise, the node will output separate list of object for each list of
  curves in the input - i.e., **Verties** output will have nesting level 4 if
  **Curve** input had nesting level 2. Checked by default.

Outputs
-------

This node has the following outputs:

* **Vertices**. The calculated points on the curve.
* **Edges**. Edges between the calculated points. This output is only available when the **Mode** parameter is set to **Auto**.
* **Tangents**. Curve tangent vectors for each value of curve parameter.

Examples of usage
-----------------

This node used for line visualization:

.. image:: https://user-images.githubusercontent.com/284644/77443595-fc503800-6e0c-11ea-9340-6473785a6a51.png
  :target: https://user-images.githubusercontent.com/284644/77443595-fc503800-6e0c-11ea-9340-6473785a6a51.png

* Curves->Curve Primitives-> :doc:`Line (Curve) </nodes/curve/line>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/43f40de2-c2ac-46cc-8d46-3f23b27569f3
  :target: https://github.com/nortikin/sverchok/assets/14288520/43f40de2-c2ac-46cc-8d46-3f23b27569f3

* Curves-> :doc:`Rounded Rectangle </nodes/curve/rounded_rectangle>`
* Curves-> :doc:`Curve Domain </nodes/curve/curve_range>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Viz-> :doc:`Viewer Draw Curve </nodes/viz/viewer_draw_curve>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`