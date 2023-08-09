Pulga Random Force
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/461529b6-886c-4c15-8844-9afbd6c6e5c6
  :target: https://github.com/nortikin/sverchok/assets/14288520/461529b6-886c-4c15-8844-9afbd6c6e5c6

Functionality
-------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c5c3db7e-dd55-447f-b490-35cd90b1dcf9
  :target: https://github.com/nortikin/sverchok/assets/14288520/c5c3db7e-dd55-447f-b490-35cd90b1dcf9

.. image:: https://github.com/nortikin/sverchok/assets/14288520/bf291a3b-b970-4ff0-9dd4-cfb157c99675
  :target: https://github.com/nortikin/sverchok/assets/14288520/bf291a3b-b970-4ff0-9dd4-cfb157c99675

This node creates a force to be applied with the Pulga Physics Solver node.

The node will apply a random force to each vertex of the defined magnitude that can change every iteration.


Input
-----

- **Strength**: Magnitude of the random force.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/c345e20c-cdfe-464f-81d8-4ba5b4ad52ac
    :target: https://github.com/nortikin/sverchok/assets/14288520/c345e20c-cdfe-464f-81d8-4ba5b4ad52ac

- **Variation**: Variation on every iteration. 0= no variation, 1= 100% variation.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/f84759f8-5002-4aef-81ca-ef3a65413711
    :target: https://github.com/nortikin/sverchok/assets/14288520/f84759f8-5002-4aef-81ca-ef3a65413711

- **Seed**: Random seed. Evert number will produce different forces.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/5e490b21-2de1-4ec1-b3d9-a8bf049ca762
    :target: https://github.com/nortikin/sverchok/assets/14288520/5e490b21-2de1-4ec1-b3d9-a8bf049ca762

Examples
--------

Trajectories of vertices of NGon.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/89102504-d80e-44f1-9f40-dbda784e585a
  :target: https://github.com/nortikin/sverchok/assets/14288520/89102504-d80e-44f1-9f40-dbda784e585a

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/1605073d-6577-4f31-a5e6-2faf22c64e69
  :target: https://github.com/nortikin/sverchok/assets/14288520/1605073d-6577-4f31-a5e6-2faf22c64e69