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

Tensile structures can be studied with pinned points.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_physics_solver/blender_sverchok_pulga_physics_solver_example_01.png
  :alt: textile_structures_pulga_physics_procedural_design.png


Using the caternary as a structural modeling tool:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_physics_solver/blender_sverchok_pulga_physics_solver_example_02.png
  :alt: catenary_cover_pulga_physics_procedural_design.png

Variable spring stiffness can be used to simulate sewing springs inflatable structures.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_physics_solver/blender_sverchok_pulga_physics_solver_example_03.png
  :alt: inflateble_structures_pulga_physics_procedural_design.png

Shooting particles to a attractors field.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_physics_solver/blender_sverchok_pulga_physics_solver_example_04.png
  :alt: shooting partcles_pulga_physics_procedural_design.PNG

The "Pins Reactions" output supply the resultant force on the pins. It can be use to model auxiliary structures.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_physics_solver/blender_sverchok_pulga_physics_solver_example_05.png
  :alt: pin_reactions_pulga_physics_procedural_design.png
