Make monotone
=============

.. image:: https://user-images.githubusercontent.com/28003269/62114765-5cb3c780-b2c8-11e9-86d4-d10541937284.png

Functionality
-------------
The node split polygon into monotone pieces. 

What is monotone polygon look here: https://en.wikipedia.org/wiki/Monotone_polygon

**Note: input points of the polygon should be in ordered order either you will get an error**

Polygon optionally can have holes. Holes should be inside the polygon or ypu can get an error 
according that the node does not make any tests like is hole inside polygon or not  

Inputs
------

- **Polygon** - vertices of polygon (should be ordered)
- **Hole vectors** (optionally) - vertices of hole(s)
- **Hole polygons** (optionally) - faces of hole(s)

Outputs
-------

- **Vertices** - vertices of main polygon and its holes
- **Polygons** - monotone polygons

Examples
--------

https://gist.github.com/bf2fe89881faa0e847771f2449b09052

.. image:: https://user-images.githubusercontent.com/28003269/62184789-93451d00-b370-11e9-8d2c-839fae4b8f5c.gif

.. image:: https://user-images.githubusercontent.com/28003269/66397537-162bc900-e9ed-11e9-9935-11eeab63cc40.png

https://gist.github.com/eab9b492c2ab1f8fe3e9cebd067ee737

.. image:: https://user-images.githubusercontent.com/28003269/62115051-d77ce280-b2c8-11e9-8121-ab8af75090d5.gif

**Tricky variant of creating holes in holes**

.. image:: https://user-images.githubusercontent.com/28003269/66452478-aad80a80-ea71-11e9-8c24-c8d01a65c9cc.png