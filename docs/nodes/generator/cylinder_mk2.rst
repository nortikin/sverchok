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

The **Separate**, **Cap T**, **Cap B** and **Center** can be given by the node only.
The *

+-----------------------+---------+---------+-------------------------------------------------------+
| Param                 | Type    | Default | Description                                           |
+=======================+=========+=========+=======================================================+
| **Radius Top**        | Float   | 1.00    | The radius of the top parallel.                       |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Radius Bottom**     | Float   | 1.00    | The radius of the bottom parallel                     |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Parallels**         | Int     | 2       | The number of parallel lines.                         |
|                       |         |         | This is also the number of points in a meridian.      |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Meridians**         | Int     | 32      | The number of meridian lines.                         |
|                       |         |         | This is also the number of points in a parallel.      |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Height**            | Float   | 2.00    | The height of the cylinder.                           |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Twist**             | Float   | 0.0     | The amount of twist of the parallel lines around the  |
|                       |         |         | z-axis from the bottom parallel to the top parallel.  |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Phase**             | Float   | 0.0     | The amount of rotation around the z-axis of all the   |
|                       |         |         | vertices in the mesh.                                 |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Parallels Profile** | [Float] | [1,1]   | The scale modulating the radius of the parallel lines.|
+-----------------------+---------+---------+-------------------------------------------------------+
| **Meridians Profile** | [Float] | [1,1]   | The scale modulating the radius of the meridian lines.|
+-----------------------+---------+---------+-------------------------------------------------------+
| **Caps T**            | Boolean | True    | Generate the top cap or not.                          |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Caps B**            | Boolean | True    | Generate the bottom cap or not.                       |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Separate**          | Boolean | False   | Separate the parallels into separate lists.           |
+-----------------------+---------+---------+-------------------------------------------------------+
| **Center**            | Boolean | True    | Center the cylinder around origin.                    |
+-----------------------+---------+---------+-------------------------------------------------------+


Extended Parameters
----------
The Property Panel provides additional parameters.

**Cyclic**
This parameter is used for treating the connected **Parallels Profile** as a cyclic spline curve and it is useful to ensure smooth parallel curves whenever there's discontinuity in the value and the tangent of the starting/ending points of the profile.


Outputs
-------

**Vertices**, **Edges** and **Polygons**.
All outputs will be generated when the output sockets are connected.
Depending on the type of the inputs the node will generate only one or multiples independant cylinders.
If **Separate** is True, the node will output the parallels as separate lists.


