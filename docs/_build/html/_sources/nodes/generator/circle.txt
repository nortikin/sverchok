Circle
======

.. image:: /images/nodes/generator/circle_node.png
    :alt: Node: Plane

Functionality
-------------

Circle generator creates circles based on the radius and the number of vertices. What does that mean? It means that if the number of vertices is too low, ir will stop being a circle and will be a regular polygon, in example::

    - 3 vertices = triangle.
    - 4 vertices = square
    - ...
    - 6 vertices =  hexagon
    - ...
    - Many vertices =  circle

This node will also create sector or semgent of circles using the **Degrees** option. See the examples below to see it working also with the **mode** option.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.
There is three inputs:

- **Radius**
- **N Vertices**
- **Degrees**

Same as other generators, all inputs will accept a single number, an array or even an array of arrays::

    [2]
    [2, 4, 6]
    [[2], [4]]

Parameters
----------

All parameters can be given by the node or an external input.


+----------------+---------------+-------------+----------------------------------------------------+
| Param          | Type          | Default     | Description                                        |  
+================+===============+=============+====================================================+
| **Radius**     | Float         | 1.00        | radius of the circle                               | 
+----------------+---------------+-------------+----------------------------------------------------+
| **N Vertices** | Int           | 24          | number of vertices to generate the circle          |
+----------------+---------------+-------------+----------------------------------------------------+
| **Degrees**    | Float         | 360.0       | angle for a sector/segment circle                  |
+----------------+---------------+-------------+----------------------------------------------------+
| **Mode**       | Bollean       | False       | switch between two sector and segment circle       |
+----------------+---------------+-------------+----------------------------------------------------+

Outputs
-------

**Vertices**, **Edges** and **Polygons**. 
All outputs will be generated. Depending on the type of the inputs, the node will generate only one or multiples independant circles.
If **Degrees** is minor than 0, depending of the **mode** state, will be generated a sector or a segment of a circle with that degrees angle.

Example of usage
----------------

.. image:: /images/nodes/generator/circle_node_example1.png

In this first example we see that circle generator can be a circle but also any regular polygon that you want.

.. image:: /images/nodes/generator/circle_node_example2.png

The second example shows the use of **mode** option and how it generates sector or segment of a circle based on the **degrees** value.