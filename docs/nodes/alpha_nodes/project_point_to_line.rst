Project points to line
======================

.. image:: https://user-images.githubusercontent.com/28003269/57965425-316e3d00-7955-11e9-9d2b-016f9ebce9aa.png

Functionality
-------------
This node allows to find closest point, that belongs to line, to input point. Also the node gives information where the
point located on line. If there are several projected points it possible to sort them in order of vectors of input line.

Information about working of the algorithm: #2376

Inputs
------

- **Vectors_line** - sorted points in order from start line to end
- **Project_points** - bunch of points that should be projected
- **resolution** - parameter that can be revealed from N panel

+----------------+-------+------+--------------------------------------------------------------------------------+
| Parameters     | Type  | min  | Description                                                                    |
+================+=======+======+================================================================================+
| Cyclic         | Bool  |  -   | In this mode the node considers the input line is close                        |
+----------------+-------+------+--------------------------------------------------------------------------------+
| Set resolution | Bool  |  -   | This parameter located on N panel makes resolution parameter available         |
+----------------+-------+------+--------------------------------------------------------------------------------+
| resolution     | float | 0.01 | It is expected in most cases this can remain with default value. Details below |
+----------------+-------+------+--------------------------------------------------------------------------------+

**resolution:**
Feature of the algorithm makes necessary to have this parameter. Unfortunately the algorithm can give quite rough
result. The less resolution the more accurate and expensive result. By default resolution is equal to length of
smallest edge of input line. If there is line that have edges and one of them is very small it can slow down the
calculation of the node. If you does not satisfied by result with default value, enabled parameter resolution and
try to decreasing value.

Outputs
-------

- **Points_projected** - projected points from input points to input line
- **Belonging** - this socket keeps values which relates projected points with line. This values says where projected point hit the line. Projected point can lay on an edge or coincide with existing point of the line. In first case the value will be in such format [index of first point of edge, index of last point of the edge]. In second case [index of coincided point]
- **Sorting_mask** - also is quite powerful output. This output gives indexes of projected points in order from start input line to end. For example if you have three projected points to a line and they hit line in edges in next order [edge 2, edge 3, edge 1] then sorting mask will have a look like this [2, 0, 1]. It means that for sorting we should take last edge then first edge and then middle edge, so we get list like this [edge 1, edge 2, edge 3]. Benefits of using such sorthing mask is that this mask possible to apply not only to output data of the node but also to input data and other data with the same length and related with project points.

Examples
--------
**Project random points to sine:**

.. image:: https://user-images.githubusercontent.com/28003269/57971033-c7c45200-7999-11e9-85df-d271412cc0f1.png
.. image:: https://user-images.githubusercontent.com/28003269/57971035-c8f57f00-7999-11e9-8d86-2ed2ea6d64aa.png

**Sort projected points according direction of input line:**

- green - indexes of points of input line
- redish - indexes of input points from which projection should be done
- blue - indexes of projected points

.. image:: https://user-images.githubusercontent.com/28003269/57965469-b35e6600-7955-11e9-9325-29362c86eb09.png
.. image:: https://user-images.githubusercontent.com/28003269/57965472-b8bbb080-7955-11e9-8975-0635c9d77230.png

**Similar to previous example but input points for projection are sorted:**

.. image:: https://user-images.githubusercontent.com/28003269/57952374-0b697e00-78fe-11e9-942a-69800a947943.png
.. image:: https://user-images.githubusercontent.com/28003269/57952406-2c31d380-78fe-11e9-8f49-31ae0a40c9ba.png

**Projection one line to another:**

.. image:: https://user-images.githubusercontent.com/28003269/57965586-464bd000-7957-11e9-9298-5c004bd16442.png
.. image:: https://user-images.githubusercontent.com/28003269/57965649-15b86600-7958-11e9-97ec-cee8d105ba3d.gif
.. image:: https://user-images.githubusercontent.com/28003269/57971245-77022880-799c-11e9-8711-bb6a0bf959fb.png
.. image:: https://user-images.githubusercontent.com/28003269/57965688-924b4480-7958-11e9-9340-95ccec11de3d.png
