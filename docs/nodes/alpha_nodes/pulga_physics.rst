Pulga Physics
=============

Functionality
-------------

This node creates simulations from input parameters, it is meant to be used in form-finding purposes.
It creates the simulation using the inputed vertices as spheric particles that react to applied forces.


Input & Output
--------------


+------------------------+---------------+-------------+-----------------------------------------------+
| Input                  | Type          | Default     | Description                                   |
+========================+===============+=============+===============================================+
| **Initial_Pos**        | Vertices      | None        | Vertices in original state                    |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Iterations**         | Vertices      | None        | Number of iterations of the process           |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Springs**            | Strings       | None        | Edges referenced to vertices                  |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Springs Length**     | Strings       | None        | Specify spring rest length,                   |
|                        |               |             | 0 to calculate it from initial position       |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Springs Stiffness**  | Strings       | None        | Springs stiffness constant                    |
+------------------------+---------------+-------------+-----------------------------------------------+
| **pins**               | Strings       | None        | Indexes of vertices with fixed position,      |
|                        |               |             | accepts a vertices mask and index number      |
+------------------------+---------------+-------------+-----------------------------------------------+
| **pins_gola_pos        | Vertices      | None        | Final position of pinned vertices             |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Radius**             | Strings       | None        | Radius of virtual sphere, used to             |
|                        |               |             | calculate intersections, mass and surface     |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Self Collision**     | Strings       | None        | collision force.                              |
|                        |               |             | Applied when vertex distance < sum Radius     |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Self Attract**       | Strings       | None        | attract force magnitude                       |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Self Attract Decay** | Strings       | None        | attract force decay with distance (power)     |
|                        |               |             | 0 = no decay, 1 = linear, 2 = quadratic...    |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Grow**               | Strings       | None        | Radius variance factor.                       |
|                        |               |             | Shrink when they intersect, Grow when don't.  |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Min Radius**         | Strings       | None        | Minimum radius limit                          |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Max Radius**         | Strings       | None        | Maximum radius limit                          |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Pols**               | Strings       | None        | Pols referenced to vertices                   |
|                        |               |             |(used to calculate inflate force)              |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Inflate**            | Strings       | None        | Inflate force magnitude (per surface unit)    |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Initial Velocity**   | Vertices      | None        | Initial vertices velocity                     |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Max Velocity**       | Strings       | None        | Maximum vertices velocity                     |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Drag Force**         | Strings       | None        | Movement resistance from environment          |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Attractors**         | Vertices      | None        | Attractors origins                            |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Attractors Force**   | Strings       | None        | Attractors Force magnitude                    |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Attractors Clamp**   | Strings       | None        | Attractors maximum influence distance         |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Attractors Decay**   | Strings       | None        | Decay with distance                           |
|                        |               |             | 0 = no decay, 1 = linear, 2 = quadratic...    |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Random Seed          | Strings       | None        | Random seed number                            |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Random Force**       | Strings       | None        | Random force magnitude                        |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Random Variation**   | Strings       | None        | Random force variation                        |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Density**            | Strings       | None        | Particles Density                             |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Gravity**            | Vectors       | None        | Constant forces that are mass independent     |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Wind**               | Vertices      | None        | constant forces that are mass dependent       |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Bounding Box**       | Vertices      | None        | Limits of the system. It will work with the   | 
|                        |               |             | bounding box of the given vectors (min. two)  |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Obstacles**          | Vertices      | None        | Obstacles vertices                            |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Obstacles Pols**     | Strings       | None        | Pols referenced to obstacles vertices.        |
|                        |               |             |(they must be triangles)                       |
+------------------------+---------------+-------------+-----------------------------------------------+
| **Obstacles Bounce**   | Strings       | None        | Obstacles Bounce force                        |
+------------------------+---------------+-------------+-----------------------------------------------+
Examples
--------


Notes
-------

