Pulga Vortex Force
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c36e5cee-8557-4e55-ab04-0804c4b7c863
  :target: https://github.com/nortikin/sverchok/assets/14288520/c36e5cee-8557-4e55-ab04-0804c4b7c863

Functionality
-------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f92cc57b-295e-486a-b745-d6fb549781a0
  :target: https://github.com/nortikin/sverchok/assets/14288520/f92cc57b-295e-486a-b745-d6fb549781a0

This node creates a force to be applied with the Pulga Physics Solver node.
The vortex force is defined with a "Line" with Location and Direction.
It has three components, rotation around the line, attraction towards the line (Inflow) and a movement in the line direction (Forward).


Input
-----

- **Location**: A point of the line.
- **Direction**: Direction of the line.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c683f977-27a0-4b4a-86ed-cd0b09b8f087
      :target: https://github.com/nortikin/sverchok/assets/14288520/c683f977-27a0-4b4a-86ed-cd0b09b8f087

- **Rotation Strength**: Multiplier of the rotation force.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/9194caaf-bb91-45f8-93ed-017d7794f2a7
      :target: https://github.com/nortikin/sverchok/assets/14288520/9194caaf-bb91-45f8-93ed-017d7794f2a7

- **Inflow Strength**: Multiplier of the inflow force (towards the line).

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/29a764ce-e612-422c-afc8-71959886d8ff
      :target: https://github.com/nortikin/sverchok/assets/14288520/29a764ce-e612-422c-afc8-71959886d8ff

- **Forward Strength**: Multiplier of the forward force (in the direction of the line).

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/52674c95-dc42-4f9b-b985-706cd8d5ad3c
      :target: https://github.com/nortikin/sverchok/assets/14288520/52674c95-dc42-4f9b-b985-706cd8d5ad3c

- **Max. Distance**: Distance under the force will be applied.
- **Decay**: How the force will decay with distance. 0= no decay, 1= linear, 2= cubic, 4= quadratic...

Animated params overview:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/1882814d-93da-418d-af2e-788f7aa4781f
  :target: https://github.com/nortikin/sverchok/assets/14288520/1882814d-93da-418d-af2e-788f7aa4781f

Examples
--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/bc15cfdd-207c-4f50-8b80-b30c6b12127b
  :target: https://github.com/nortikin/sverchok/assets/14288520/bc15cfdd-207c-4f50-8b80-b30c6b12127b

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

