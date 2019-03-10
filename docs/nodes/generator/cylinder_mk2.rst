Cylinder MK2
============

Functionality
-------------

This node generates primarily cylindrical shapes, but its settings allow to create a wide variety of tube like shapes.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Radius Top**
- **Radius Bottom**
- **Parallels**
- **Meridians**
- **Height**
- **Twist**
- **Phase**
- **Scale**
- **Parallels Profile** [1]
- **Meridians Profile** [1]

[1] : The profiles inputs do not take input values from the node, but can take multiple values form the outside nodes.

Parameters
----------

The **Separate**, **Cap T**, **Cap B**, **Center** and the **Angle Units** can be given by the node only. The other parameters can take values either from the node or the external nodes.

+-----------------------+---------+---------+-------------------------------------------------------+
| Param                 | Type    | Default | Description                                           |
+=======================+=========+=========+=======================================================+
| **Radius Top**        | Float   | 1.00    | The radius of the top parallel.                       |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Radius Bottom**     | Float   | 1.00    | The radius of the bottom parallel.                    |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Parallels**         | Int     | 2       | The number of parallel lines.                         |
|                       |         |         | This is also the number of points in a meridian.      |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Meridians**         | Int     | 32      | The number of meridian lines.                         |
|                       |         |         | This is also the number of points in a parallel.      |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Height**            | Float   | 2.00    | The height of the cylinder.                           |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Twist**             | Float   | 0.0     | The amount of rotation around the z-axis of the       |
|                       |         |         | parallel lines from the bottom to the top parallel.   |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Phase**             | Float   | 0.0     | The amount of rotation around the z-axis of all the   |
|                       |         |         | vertices in the mesh.                                 |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Parallels Profile** | [Float] | [ ]     | The scale modulating the radius of the parallels. [1] |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Meridians Profile** | [Float] | [ ]     | The scale modulating the radius of the meridians. [1] |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Caps T**            | Boolean | True    | Generate the top cap or not.                          |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Caps B**            | Boolean | True    | Generate the bottom cap or not.                       |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Separate**          | Boolean | False   | Separate the parallels into separate lists. [2]       |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Center**            | Boolean | True    | Center the cylinder around the origin.                |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Angle Units**       | Enum    | RAD     | The **Twist** and **Phase** angles are interpreted as |
|                       |  RAD    |         |  RAD : Radians [0, 2*pi]                              |
|                       |  DEG    |         |  DEG : Degrees [0, 360]                               |
|                       |  UNI    |         |  UNI : Unities [0, 1]                                 |
+-----------------------+---------+---------+-------------------------------------------------------+

Notes:
[1] : If connected the profiles need to have lists of at least 2 values.
[2] : This splits the verts, edges, and polys into separate parallel sections.


Extended Parameters
----------
The Property Panel provides additional parameters.

**Cyclic**
This parameter is used for treating the connected **Parallels Profile** as a cyclic spline curve and it is useful to ensure smooth parallel curves whenever there's discontinuity in the value and/or in the tangent of the starting/ending points of the profile.


Outputs
-------

**Vertices**, **Edges** and **Polygons**.
All outputs will be generated when the output sockets are connected.
Depending on the type of the inputs the node will generate only one or multiples independant cylinder shapes.

If **Separate** is True, the node will output the parallel sections as separate lists (verts, edges and polys).


