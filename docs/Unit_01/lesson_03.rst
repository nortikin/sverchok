**********************************
Introduction to modular components
**********************************

**prerequisites**

Same as lesson 01.

Status: **WIP**
---------------

Lesson 03 - A Grid
------------------

Grids are another common geometric primitive. A Grid can be thought of as a Plane subdivided over its *x* and *y* axes. Sverchok's `Plane` generator makes grids (including edges and polygons), but we will combine the elementary nodes to build one from scratch. Doing this will cover several important concepts of parametric design, and practical tips for the construction of dynamic  topology.

**What do we know about Grids?**

For simplicity let's take a subdivided `Plane` as our template. We know it's flat and therefore the 3rd dimension (z) will be constant. We can either have a uniformly subdivided Plane or allow for x and y to be divided separately. A separate XY division is a little bit more interesting, let's go with that. 

.. image:: https://cloud.githubusercontent.com/assets/619340/5506680/c59524c6-879c-11e4-8f64-53e4b83b05a8.png

**Where to start?**

For non trivial objects we often use a notepad (yes, actual paper -- or blender Greasepencil etc) to draw a simplified version of what we want to accomplish. On a drawing we can easily name and point to properties, and even notice problems in advance.

I chose a Grid because it has only a few properties: `X Side Length, Y Side Length, X num subdivs, Y num subdivs`. These properies can be exposed in several ways. You could expose the number of divisions (edges) per side, or the amount of vertices per side. 1 geometric property, but two ways of looking at it.

.. image:: https://cloud.githubusercontent.com/assets/619340/5514705/5b6766a8-8847-11e4-8812-76916faece52.png

**Decide which variables you want to expose**

The upside of building generators from scratch is that you can make decisions based on what is most convenient for you. Here I'll pick what I think is the most convenient, it can always be changed later.

- Division distance side X
- Division distance side Y
- Number Vertices on side X
- Number Vertices on side Y

**Think in Whole numbers (ints) if you can**

What I mean by this is, reduce the problem to something that is mathematically uncomplicated. Here's a grid drawn on an xy graph to illustrate the coordinates. The z-dimension could be ignored but it's included for completeness.

.. image:: https://cloud.githubusercontent.com/assets/619340/5505509/ef999dd4-8791-11e4-8892-b46ab9688ad2.png

The reason I pick 4 verts for the X axis and 3 for Y, is because that's the smallest useful set of vertices we can use as a reference. The reason i'm not picking 3*3 or 4*4 is because using different vertex counts makes it clear what that `X` axis might have some relation to 4 and to `Y` to 3.

If you consider the sequence just by looking at the first index of each vertex, it goes ``[0,1,2,3,0,1,2,3,0,1,2,3]``. We can generate sequences like that easily. When we look at the second index of these vertices that sequence is ``[0,0,0,0,1,1,1,1,2,2,2,2]``, this also is easy to generate. 

**Using `modulo` and `integer division` to get grid coordinates**

I hope you know Python, or at the very least what `% (modulo)` and `// (int div)` are. The sequences above can be generated using code this way -- If this code doesn't make sense keep reading, it's explained further down::

    for i in range(12):
       print(i % 4)

    # 0 1 2 3 0 1 2 3 0 1 2 3

    for i in range(12):
       print(i // 4)

    # 0 0 0 0 1 1 1 1 2 2 2 2

    # all in one go
    final_list = []
    for i in range(12):
       x = i % 4
       y = i // 4
       z = 0
       final_list.append((x, y, z))

    print(final_list)
    '''
    >> [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), 
    >> (0, 1, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), 
    >> (0, 2, 0), (1, 2, 0), (2, 2, 0), (3, 2, 0)]
    '''

With any luck you aren't lost by all this code, visual programming is very similar except with less typing. The plumbing of an algorithm is still the same whether you are clicking and dragging nodes to create a flow of information or writing code in a text editor.

We can use: 

- ``i % 4`` to turn ``[0,1,2,3,4,5,6,7,8,9,10,11]`` into ``[0,1,2,3,0,1,2,3,0,1,2,3]``
- ``i // 4`` to turn ``[0,1,2,3,4,5,6,7,8,9,10,11]`` into ``[0,0,0,0,1,1,1,1,2,2,2,2]``

**Operands**

+----------------------+---------+--------------------------------------------------------+
| Operand              |  Symbol | Behaviour                                              |  
+======================+=========+========================================================+
| Modulo (mod)         | %       | ``i % 4`` returns the division remainder of ``i / 4``, | 
|                      |         | rounded down to the nearest whole number               |
+----------------------+---------+--------------------------------------------------------+
| Integer Division     | //      | ``i // 4`` returns the result of ``i / 4``,            |
|                      |         | rounded down to the nearest whole number.              |
+----------------------+---------+--------------------------------------------------------+



.. image:: https://cloud.githubusercontent.com/assets/619340/5477351/e15771f0-862a-11e4-8085-289b88d4cb6a.png

// -- TODO





