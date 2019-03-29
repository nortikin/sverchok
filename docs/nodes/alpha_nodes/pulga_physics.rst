Pulga Physics
=============

Functionality
-------------

This node creates simulations from input parameters, it is meant to be used in form-finding purposes.
It creates the simulation using the inputed vertices as spheric particles that react to applied forces.
Tne node is a basic NumPy implementation of basic physics system heavily inspired in "The Nature of Code" by Daniel Shiffman
and the Kangoroo Plugin for Grasshopper. Due the nature of the algorithm it can get very intensive, handle with responsibility

Input & Output
--------------


+------------------------+---------------+-----------------------------------------------+
| Input                  | Type          |  Description                                  |
+========================+===============+===============================================+
| **Initial_Pos**        | Vertices      | Vertices in original state                    |
+------------------------+---------------+-----------------------------------------------+
| **Iterations**         | Vertices      | Number of iterations of the process           |
+------------------------+---------------+-----------------------------------------------+
| **Springs**            | Strings       | Edges referenced to vertices                  |
+------------------------+---------------+-----------------------------------------------+
| **Springs Length**     | Strings       | Specify spring rest length,                   |
|                        |               | 0 to calculate it from initial position       |
+------------------------+---------------+-----------------------------------------------+
| **Springs Stiffness**  | Strings       | Springs stiffness constant                    |
+------------------------+---------------+-----------------------------------------------+
| **Pins**               | Strings       | Indexes of vertices with fixed position,      |
|                        |               | accepts a vertices mask and index number      |
+------------------------+---------------+-----------------------------------------------+
| **pins_goal_pos        | Vertices      | Final position of pinned vertices             |
+------------------------+---------------+-----------------------------------------------+
| **Radius**             | Strings       | Radius of virtual sphere, used to             |
|                        |               | calculate intersections, mass and surface     |
+------------------------+---------------+-----------------------------------------------+

| **Self Collision**     | Strings       | Collision force.                              |
|                        |               | Applied when vertex distance < sum Radius     |
+------------------------+---------------+-----------------------------------------------+
| **Self Attract**       | Strings       | Attract force magnitude.                      |
|                        |               | Applied when vertex distance > sum Radius     |
+------------------------+---------------+-----------------------------------------------+
| **Self Attract Decay** | Strings       | attract force decay with distance (power)     |
|                        |               | 0 = no decay, 1 = linear, 2 = quadratic...    |
+------------------------+---------------+-----------------------------------------------+
| **Grow**               | Strings       | Radius variance factor.                       |
|                        |               | Shrink when they intersect, Grow when don't.  |
+------------------------+---------------+-----------------------------------------------+
| **Min Radius**         | Strings       | Minimum radius limit                          |
+------------------------+---------------+-----------------------------------------------+
| **Max Radius**         | Strings       | Maximum radius limit                          |
+------------------------+---------------+-----------------------------------------------+
| **Pols**               | Strings       | Pols referenced to vertices                   |
|                        |               |(used to calculate inflate force)              |
+------------------------+---------------+-----------------------------------------------+
| **Inflate**            | Strings       | Inflate force magnitude (per surface unit)    |
+------------------------+---------------+-----------------------------------------------+
| **Initial Velocity**   | Vertices      | Initial vertices velocity                     |
+------------------------+---------------+-----------------------------------------------+
| **Max Velocity**       | Strings       | Maximum vertices velocity                     |
+------------------------+---------------+-----------------------------------------------+
| **Drag Force**         | Strings       | Movement resistance from environment          |
+------------------------+---------------+-----------------------------------------------+
| **Attractors**         | Vertices      | Attractors origins                            |
+------------------------+---------------+-----------------------------------------------+
| **Attractors Force**   | Strings       | Attractors Force magnitude                    |
+------------------------+---------------+-----------------------------------------------+
| **Attractors Clamp**   | Strings       | Attractors maximum influence distance         |
+------------------------+---------------+-----------------------------------------------+
| **Attractors Decay**   | Strings       | Decay with distance                           |
|                        |               | 0 = no decay, 1 = linear, 2 = quadratic...    |
+------------------------+---------------+-----------------------------------------------+
| **Random Seed          | Strings       | Random seed number                            |
+------------------------+---------------+-----------------------------------------------+
| **Random Force**       | Strings       | Random force magnitude                        |
+------------------------+---------------+-----------------------------------------------+
| **Random Variation**   | Strings       | Random force variation                        |
+------------------------+---------------+-----------------------------------------------+
| **Density**            | Strings       | Particles Density                             |
+------------------------+---------------+-----------------------------------------------+
| **Gravity**            | Vectors       | Constant forces that are mass independent     |
+------------------------+---------------+-----------------------------------------------+
| **Wind**               | Vertices      | constant forces that are mass dependent       |
+------------------------+---------------+-----------------------------------------------+
| **Bounding Box**       | Vertices      | Limits of the system. It will work with the   | 
|                        |               | bounding box of the given vectors (min. two)  |
+------------------------+---------------+-----------------------------------------------+
| **Obstacles**          | Vertices      | Obstacles vertices                            |
+------------------------+---------------+-----------------------------------------------+
| **Obstacles Pols**     | Strings       | Pols referenced to obstacles vertices.        |
|                        |               |(they must be triangles)                       |
+------------------------+---------------+-----------------------------------------------+
| **Obstacles Bounce**   | Strings       | Obstacles Bounce force                        |
+------------------------+---------------+-----------------------------------------------+

Accumulative:
-------------

When activated every nodeTree update will use the previous update as the starting point. The update can be triggered by the Upate button or by any other event that triggers regular updates (like playing animation or changing any value)
It offers some options:
**Reset**: Takes back the system to the initial state.
**Update**: Runs one nodetree update
**Pause**: Pauses nodes calculations and ignores ui changes


Examples
--------


Notes
-------
The node uses one text-block to save the current state when you hit pause or freeze in order to be mantained in case of closing the program.
