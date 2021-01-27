Pulga Vortex Force
==================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.
The vortex force is defined with a "Line" with Location and Direction.
It has three components, rotation around the line, attraction towards the line (Inflow) and a movement in the line direction (Forward).


Input
-----

**Location**: A point of the line.

**Direction**: Direction of the line.

**Rotation Strength**: Multiplier of the rotation force.

**Inflow Strength**: Multiplier of the inflow force (towards the line).

**Forward Strength**: Multiplier of the forward force (in the direction of the line).

**Max. Distance**: Distance under the force will be applied.

**Decay**: How the force will decay with distance. 0= no decay, 1= linear, 2= cubic, 4= quadratic...


Examples
--------

Constant vector force:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_vortex_force/blender_sverchok_pulga_vortex_force_example_01.png


Noise Vector Field as vector force:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_vortex_force/blender_sverchok_pulga_vortex_force_example_02.png
