Pulga Timed Force
=================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.
The inputted force will only be applied between the defined iterations range.


Input
-----

**Force**: Force to apply the time restriction to.

**Start**: Start iteration when the force will be applied.

**End**: End iteration when the force will stop being applied.


Examples
--------

In the following example a Random force will be applied on the first 50 iterations, after a Fit force will be applied.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_timed_force/blender_sverchok_pulga_timed_force_example_01.png
