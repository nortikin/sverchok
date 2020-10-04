Pulga Physics Solver
====================

Functionality
-------------

This node creates simulations from input parameters, it is meant to be used in form-finding purposes.
It creates the simulation using the inputted vertices as spherical particles that react to applied forces.

The node is a basic NumPy implementation of basic physics system heavily inspired in "The Nature of Code" by Daniel Shiffman
and the Kangoroo Plug-in for Grasshopper. Due the nature of the algorithm it can get very intensive, handle with responsibility

Input & Output
--------------


+------------------------+---------------+-----------------------------------------------+
| Input                  | Type          |  Description                                  |
+========================+===============+===============================================+
| **Initial_Pos**        | Vertices      | Vertices in original state                    |
+------------------------+---------------+-----------------------------------------------+
| **Iterations**         | Integer       | Number of iterations of the process           |
+------------------------+---------------+-----------------------------------------------+
| **Radius**             | Float         | Radius of virtual sphere, used to             |
|                        |               | calculate intersections, mass and surface     |
+------------------------+---------------+-----------------------------------------------+
| **Initial Velocity**   | Vertices      | Initial vertices velocity                     |
+------------------------+---------------+-----------------------------------------------+
| **Max Velocity**       | Float         | Maximum vertices velocity                     |
+------------------------+---------------+-----------------------------------------------+
| **Density**            | Float         | Particles Density                             |
+------------------------+---------------+-----------------------------------------------+
| **Forces**             | Force         | System forces                                 |
+------------------------+---------------+-----------------------------------------------+

+------------------------+---------------+-----------------------------------------------+
| Output                 | Type          |  Description                                  |
+========================+===============+===============================================+
| **Vertices**           | Vertices      | Vertices in original state                    |
+------------------------+---------------+-----------------------------------------------+
| **Radius**             | Strings       | Radius of virtual sphere, used to             |
|                        |               | calculate intersections, mass and surface     |
+------------------------+---------------+-----------------------------------------------+
| **Velocity**           | Vertices      | Velocity at the end of iterations             |
+------------------------+---------------+-----------------------------------------------+
| **Pin Reactions**       | Strings      | Reactions at Pinned Vertices                  |
+------------------------+---------------+-----------------------------------------------+

Accumulative:
-------------

When activated every nodeTree update will use the previous update as the starting point. The update can be triggered by the Update button or by any other event that triggers regular updates (like playing animation or changing any value).

It offers some options:

**Reset**: Takes back the system to the initial state.

**Update**: Runs one Node-Tree update.

**Pause**: Pauses nodes calculations and ignores ui changes.


Examples
--------

Arranging circles with attraction and collision.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_fit_force/blender_sverchok_pulga_fit_force_example_02.png
  :alt: circle_fitting_pulga_physics_procedural_design.png

Inflating a cube simulating a pillow.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_inflate_force/blender_sverchok_pulga_inflate_force_example_02.png

Tensile structures can be studied with collisions and pinned points.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_pin_force/blender_sverchok_pulga_pin_force_example_01.png
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
