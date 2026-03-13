Cylinder MK2
============

.. image:: https://user-images.githubusercontent.com/14288520/188698444-3c371e60-6887-4359-86e2-47bfc66568e5.png
  :target: https://user-images.githubusercontent.com/14288520/188698444-3c371e60-6887-4359-86e2-47bfc66568e5.png

Functionality
-------------

This node generates primarily cylindrical shapes, but its settings allow to create a wide variety of tube like shapes.

.. image:: https://user-images.githubusercontent.com/14288520/191251147-947ec5e5-d7db-4d6d-9d9a-122c261295c9.png
  :target: https://user-images.githubusercontent.com/14288520/191251147-947ec5e5-d7db-4d6d-9d9a-122c261295c9.png

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Radius T** - Top Radius
- **Radius B** - Bottom Radius
- **Parallels** - Number of Parallels
- **Meridians** - Number of meridians
- **Height** - The height of the cylinder
- **Twist** - Rotate parallel verts by this angle around Z from bottom to top
- **Phase** - Rotate all verts by this angle around Z axis
- **Scale** - scale the entire mesh (radii & height)
- **Parallels Profile** - parallels profile [1]
- **Meridians Profile** - meridians profile [1]

[1] : The profiles inputs do not take input values from the node, but can take multiple values form the outside nodes.

Parameters
----------

The **Separate**, **Cap T**, **Cap B**, **Center** and the **Angle Units** can be given by the node only. The other parameters can take values either from the node or the external nodes.

+-----------------------+---------+---------+-----------------------------------------------------------+
| Param                 | Type    | Default | Description                                               |
+=======================+=========+=========+===========================================================+
| **Radius Top**        | Float   | 1.00    | The radius of the top parallel.                           |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Radius Bottom**     | Float   | 1.00    | The radius of the bottom parallel.                        |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Parallels**         | Int     | 2       | The number of parallel lines.                             |
|                       |         |         |                                                           |
|                       |         |         | This is also the number of points in a meridian.          |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Meridians**         | Int     | 32      | The number of meridian lines.                             |
|                       |         |         |                                                           |
|                       |         |         | This is also the number of points in a parallel.          |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Height**            | Float   | 2.00    | The height of the cylinder.                               |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Twist**             | Float   | 0.0     | The amount of rotation around the z-axis of the           |
|                       |         |         |                                                           |
|                       |         |         | parallel lines from the bottom to the top parallel.       |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Phase**             | Float   | 0.0     | The amount of rotation around the z-axis of all the       |
|                       |         |         |                                                           |
|                       |         |         | vertices in the mesh.                                     |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Parallels Profile** | [Float] | [ ]     | The scale modulating the radius of the parallels. **[1]** |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Meridians Profile** | [Float] | [ ]     | The scale modulating the radius of the meridians. **[1]** |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Caps T**            | Boolean | True    | Generate the top cap or not.                              |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Caps B**            | Boolean | True    | Generate the bottom cap or not.                           |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Separate**          | Boolean | False   | Separate the parallels into separate lists. **[2]**       |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Center**            | Boolean | True    | Center the cylinder around the origin.                    |
+-----------------------+---------+---------+-----------------------------------------------------------+
| **Angle Units**       | Enum    | RAD     | The **Twist** and **Phase** angles are interpreted as     |
|                       |         |         |                                                           |
|                       | * RAD   |         | * RAD : Radians [0.0, 2*pi]                               |
|                       | * DEG   |         | * DEG : Degrees [0.0, 360.0]                              |
|                       | * UNI   |         | * UNI : Unities [0.0, 1.0]                                |
+-----------------------+---------+---------+-----------------------------------------------------------+

Notes:

* **[1]** : If connected the profiles need to have lists of at least 2 values.
* **[2]** : This splits the verts, edges, and polys into separate parallel sections.


Extended Parameters
-------------------
The Property Panel provides additional parameters.

* **Cyclic** This parameter is used for treating the connected **Parallels Profile** as a cyclic spline curve and it is useful to ensure smooth parallel curves whenever there's discontinuity in the value and/or in the tangent of the starting/ending points of the profile.


Outputs
-------

**Vertices**, **Edges** and **Polygons**.
All outputs will be generated when the output sockets are connected.
Depending on the type of the inputs the node will generate only one or multiples independent cylinder shapes.

If **Separate** is True, the node will output the parallel sections as separate lists (verts, edges and polys).

.. image:: https://user-images.githubusercontent.com/14288520/189488345-2daba527-0aa0-463d-bd0d-4dfbbc0d59af.png
  :target: https://user-images.githubusercontent.com/14288520/189488345-2daba527-0aa0-463d-bd0d-4dfbbc0d59af.png

**Examples**

.. image:: https://user-images.githubusercontent.com/14288520/188701121-947eabdc-b13d-45f6-9ea5-4204162a0c97.png
  :target: https://user-images.githubusercontent.com/14288520/188701121-947eabdc-b13d-45f6-9ea5-4204162a0c97.png

.. image:: https://user-images.githubusercontent.com/14288520/188700994-0a9c858e-0a6f-49c3-8215-16681c7802f8.gif
  :target: https://user-images.githubusercontent.com/14288520/188700994-0a9c858e-0a6f-49c3-8215-16681c7802f8.gif

* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

See also
--------

Example of a manual meridian profile:

* Number-> :doc:`Curve Mapper </nodes/number/curve_mapper>`