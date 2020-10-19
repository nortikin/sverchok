Pulga Vector Force
==================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.
The force applies the inputted vector as a force to each vertex.
The force direction will be the same as the inputted vertex.
The force magnitude will be:  Inputted Vector Magnitude * Force Strength

Input
-----

**Force**: Force as vector value. It will also accept a vector Field as input, if multiple values are given the will be use as force per particle.

**Strength**: Multiplier of the force, if multiple values are given the will be use as strength per particle.

Options
-------

**Proportional to Mass**: multiply the Vector Force by the mass of the particle.


Examples
--------

Constant vector force:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_vector_force/blender_sverchok_pulga_vector_force_example_01.png


Noise Vector Field as vector force:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_vector_force/blender_sverchok_pulga_vector_force_example_01.png
