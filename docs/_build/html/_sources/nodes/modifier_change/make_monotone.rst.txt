Make monotone
=============

.. image:: https://user-images.githubusercontent.com/28003269/67477849-eb3ba900-f66b-11e9-9892-392d5fb9a0c3.png

Functionality
-------------
The node split polygon into monotone pieces.

What is monotone polygon look here: https://en.wikipedia.org/wiki/Monotone_polygon

Prefix 2D means that the node expects from input any kind of flatten mesh
but it does not mean that the mesh should only lay on XY surface.
Input mesh can below or above XY surface or even can be tilted relative one.

**Note: input points of the polygon should be in ordered order either you will get an error**

Polygon optionally can have holes. Holes should be inside the polygon or you can get an error
according that the node does not make any tests like is hole inside polygon or not

Category
--------

Modifiers -> Modifier change -> Make monotone

Inputs
------

- **Polygon** - vertices of polygon (should be ordered)
- **Hole vectors** (optionally) - vertices of hole(s)
- **Hole polygons** (optionally) - faces of hole(s)

Outputs
-------

- **Vertices** - vertices of main polygon and its holes
- **Polygons** - monotone polygons

N panel
-------

+--------------------+-------+--------------------------------------------------------------------------------+
| Parameters         | Type  | Description                                                                    |
+====================+=======+================================================================================+
| Accuracy           | int   | Number of figures of decimal part of a number for comparing float values       |
+--------------------+-------+--------------------------------------------------------------------------------+

**Accuracy** - In most cases there is no need in touching this parameter
but there is some cases when the node can stuck in error and playing with the parameter can resolve the error.
This parameter does not have any affect to performance in spite of its name.

Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/62184789-93451d00-b370-11e9-8d2c-839fae4b8f5c.gif

.. image:: https://user-images.githubusercontent.com/28003269/66397537-162bc900-e9ed-11e9-9935-11eeab63cc40.png

.. image:: https://user-images.githubusercontent.com/28003269/62115051-d77ce280-b2c8-11e9-8121-ab8af75090d5.gif

**Tricky variant of creating holes in holes**

.. image:: https://user-images.githubusercontent.com/28003269/66452478-aad80a80-ea71-11e9-8c24-c8d01a65c9cc.png