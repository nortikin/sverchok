Plane
=====

Functionality
-------------

Plane generator creates a grid in the plane XY, based on the number of vertices and the length between them in X and Y directions. It works in a similar way than Line, but creating a grid instead of a line.

Inputs
------

Just like in Line Node, all inputs are vectorized and they will accept single or multiple values.
There is two basic inputs **N Vert** and **Step**, but referenced to both X and Y directions, so it results in 4 inputs:

- **N Vert X**
- **N Vert Y**
- **Step X**
- **Step Y**

Same as Line, all inputs will accept a single number or an array of them or even an array of arrays::

    [2]
    [2, 4, 6]
    [[2], [4]]

Parameters
----------

All parameters except **Separate** can be given by the node or an external input.


+--------------+---------------+-------------+----------------------------------------------------+
| Param        | Type          | Default     | Description                                        |  
+==============+===============+=============+====================================================+
| **N Vert X** | Int           | 2           | number of vertices in X. The minimum is 2.         | 
+--------------+---------------+-------------+----------------------------------------------------+
| **N Vert Y** | Int           | 2           | number of vertices in X. The minimum is 2.         |
+--------------+---------------+-------------+----------------------------------------------------+
| **Step X**   | Float         | 1.00        | length between vertices in X axis                  |
+--------------+---------------+-------------+----------------------------------------------------+
| **Step Y**   | Float         | 1.00        | length between vertices in Y axis                  |
+--------------+---------------+-------------+----------------------------------------------------+
| **Separate** | Bolean        | False       | grouping vertices by V direction                   |
+--------------+---------------+-------------+----------------------------------------------------+

Outputs
-------

**Vertices**, **Edges** and **Polygons**. 
All outputs will be generated. Depending on the type of the inputs, the node will generate only one or multiples independant grids.
If **Separate** is True, the output is totally different. The grid disappear (no more **polygons** are generated) and instead it generates a series of lines repeated along Y axis. See examples below to a better understanding.

Example of usage
----------------

.. image:: https://cloud.githubusercontent.com/assets/5990821/4186862/981724fa-3764-11e4-9ead-3e7eecc0433a.png
  :alt: PlaneDemo1.PNG

The first example shows a grid with 6 vertices in X direction and 4 in Y. The distance between them is base on the next serie of floats::

    [0.5, 1.0 , 1.5, 2.0, 2.5]

.. image:: https://cloud.githubusercontent.com/assets/5990821/4186863/98178f94-3764-11e4-8796-2076df9136c1.png
  :alt: PlaneDemo2.PNG

The second example is just like the first, but with **Separate** option activated, so the output is a series of lines unconnected instead of a complete grid.
