Pulga Align Force
=================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.
The force applies part of the velocity of the near particles (vertices) to each particle.
The force direction will be the velocity of the near vertex
The force magnitude will be:  1/(Distance to the power of Decay) * 1/(number of vertices of the system) * Force Strength

Input
-----

**Strength**: Multiplier of the force, if multiple values are given the will be use as strength per particle.

**Decay**: How the force decays with distance.

**Max Distance**: Distance under the force will be applied.

Options
-------

**Mode**: Algorithm used to calculate attractions. Offers 'Brute Force' and 'Kd-tree'

- Kd-tree: this is the fastest mode but in order to work it needs 'Scipy' and 'Cython' dependencies to be installed. In this mode the attraction continues even if the vertices are colliding

- Brute-Force: This mode is much slower but does not need any dependencies to work.

Examples
--------

Arranging circles with attraction and collision.

.. image:: https://user-images.githubusercontent.com/10011941/55254066-3d902500-5257-11e9-9a28-46d3deffcf0b.png
  :alt: circle_fitting_pulga_physics_procedural_design.png

Tensile structures can be studied with collisions and pinned points.

.. image:: https://user-images.githubusercontent.com/10011941/55254067-3e28bb80-5257-11e9-8988-7e19e8a2462b.png
  :alt: textile_structures_pulga_physics_procedural_design.png

.. image:: https://user-images.githubusercontent.com/10011941/56082937-23da0a80-5e1f-11e9-9b50-611629574cef.png
  :alt: textile_cover_pulga_physics_procedural_design.png


Traction structures can be converted to compression structures with inverted gravity.

.. image:: https://user-images.githubusercontent.com/10011941/55254068-3e28bb80-5257-11e9-86b3-2243b4e7ac4e.png
  :alt: compression_structures_pulga_physics_procedural_design.png

Using the caternary  as a structural modeling tool:

.. image:: https://user-images.githubusercontent.com/10011941/56082943-305e6300-5e1f-11e9-811b-c20df2a7a4d2.png
  :alt: catenary_cover_pulga_physics_procedural_design.png

Variable spring stiffness can be used to simulate sewing springs inflatable structures.

.. image:: https://user-images.githubusercontent.com/10011941/55256836-69fb6f80-525e-11e9-9a1b-21a6eafd0a4e.png
  :alt: inflateble_structures_pulga_physics_procedural_design.png

Trajectories can be traced by supplying the desired iterations as a list.

.. image:: https://user-images.githubusercontent.com/10011941/55313009-14de7a00-5467-11e9-887e-781d7b4dc025.png
  :alt: physics_modeling_pulga_physics_procedural_design.png

Shooting particles to a attractors field.

.. image:: https://user-images.githubusercontent.com/10011941/56082940-2b011880-5e1f-11e9-8124-90da02ab7cf5.png
  :alt: shooting partcles_pulga_physics_procedural_design.PNG

The "Pins Reactions" output supply the resultant force on the pins. It can be use to model auxiliary structures.

.. image:: https://user-images.githubusercontent.com/10011941/56082950-479d5080-5e1f-11e9-87ed-19b9247c07b5.png
  :alt: pin_reactions_pulga_physics_procedural_design.png


Notes
-------

When using accumulative mode the node uses one text-block (called pulga_memory + NodeTree name + Node name .txt) to save the current state when you hit pause in order to be maintained in case of closing the program.
