**********************************
Introduction to modular components
**********************************

Lesson 03 - A Grid
------------------

Grids are another common geometric primitive. A Grid can be thought of as a Plane subdivided over its *x* and *y* axes. Sverchok's ``Plane`` generator makes grids, and includes the associated edges and polygons. Instead of using the ``Plane`` node we're going to build a node tree to make a grid procedurally from scratch. Once you grasp how this works then you have understood the essentials, and they will hold true even in much more complex projects. We will cover several important concepts of parametric design, and dynamic topology.

**What do we know about Grids?**

For simplicity let's take a subdivided ``Plane`` as our template. We know it's flat and therefore the 3rd dimension (``z``) will be constant. We will allow for ``x`` and ``y`` to be divided separately, this is a little bit more interesting.

.. image:: https://cloud.githubusercontent.com/assets/619340/5506680/c59524c6-879c-11e4-8f64-53e4b83b05a8.png

**Where to start?**

Starting out we often use a notepad (yes, actual paper -- or blender Greasepencil etc) to draw a simplified version of what we want to accomplish. On a drawing we can easily name and point to properties, see relationships, and even solve problems in advance of writing code or adding nodes to the node tree.

I chose a Grid because it has only a few properties:

- X Side Length
- Y Side Length
- X num subdivs
- Y num subdivs

These properies can be exposed in several ways. You could expose the number of divisions (edges) per side, or the amount of vertices per side. 1 geometric property, but two ways of looking at it.

.. image:: https://cloud.githubusercontent.com/assets/619340/5514705/5b6766a8-8847-11e4-8812-76916faece52.png

**Decide which variables you want to expose**

The upside of building generators from scratch is that you can make decisions based on what is most convenient for you. Here I'll pick what I think is the most convenient, it can always be changed later. Think of names that mean exactly what they're attempting to describe.

- Side X total length
- Side Y total length
- Number Vertices on side X
- Number Vertices on side Y

**Think in Whole numbers (integers, ints) if you can**

Reduce the problem to something that is mathematically uncomplicated. Here's a grid drawn on an ``xy`` graph to illustrate the coordinates. The ``z-dimension`` could be ignored but it's included for completeness.

.. image:: https://cloud.githubusercontent.com/assets/619340/5505509/ef999dd4-8791-11e4-8892-b46ab9688ad2.png

The reason I pick ``4 * 3`` verts, is because that's one of the smallest forms of this problem, and only minor tweaks will be needed to turn it into grids of arbitrary dimensions. The reason i'm not picking ``3 * 3`` or ``4 * 4`` is because using different vertex counts for ``x`` and ``y`` makes it clearer that the ``X`` axis might have some relation to 4 and ``Y`` to 3.

If you consider the sequence just by looking at the first *component* of each vertex, it goes::

  [0,1,2,3,0,1,2,3,0,1,2,3]

We can generate sequences like that easily. When we look at the second *component* of these vertices that sequence is::

  [0,0,0,0,1,1,1,1,2,2,2,2]

this also is easy to generate. 


Using `modulo` and `integer division` to get grid coordinates
-------------------------------------------------------------

The next section will cover two mathematical concepts (operations), which tend to always join the party when we talk about periodic functions and stepwise increases.

- modulo, or the symbol ``%``
- integer division, or the symbol ``//``

**Operands**

We introduced the ``Scalar Math`` node in lesson 01 and 02, the ``Scalar Math`` node (from the Number menu) has many operations called operands. We'll focus on these to get the vertex components.

+----------------------+---------+--------------------------------------------------------+
| Operand              |  Symbol | Behaviour                                              |  
+======================+=========+========================================================+
| Modulo (mod)         | %       | ``i % 4`` returns the division remainder of ``i / 4``, | 
|                      |         | rounded down to the nearest whole number               |
+----------------------+---------+--------------------------------------------------------+
| Integer Division     | //      | ``i // 4`` returns the result of ``i / 4``,            |
|                      |         | rounded down to the nearest whole number.              |
+----------------------+---------+--------------------------------------------------------+

We can use: 

- ``i % 4`` to turn ``[0,1,2,3,4,5,6,7,8,9,10,11]`` into ``[0,1,2,3,0,1,2,3,0,1,2,3]``
- ``i // 4`` to turn ``[0,1,2,3,4,5,6,7,8,9,10,11]`` into ``[0,0,0,0,1,1,1,1,2,2,2,2]``

Here's a table that shows the effect of ``modulo`` and ``int.division`` on a range of numbers.

+------------------+---+---+---+---+---+---+---+---+---+---+----+----+----+----+----+
| number range (n) | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
+==================+===+===+===+===+===+===+===+===+===+===+====+====+====+====+====+
| n % 4            | 0 | 1 | 2 | 3 | 0 | 1 | 2 | 3 | 0 | 1 | 2  | 3  | 0  | 1  | 2  | 
+------------------+---+---+---+---+---+---+---+---+---+---+----+----+----+----+----+
| n // 4           | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 2 | 2 | 2  | 2  | 3  | 3  | 3  |
+------------------+---+---+---+---+---+---+---+---+---+---+----+----+----+----+----+
| n % 6            | 0 | 1 | 2 | 3 | 4 | 5 | 0 | 1 | 2 | 3 | 4  | 5  | 0  | 1  | 2  |
+------------------+---+---+---+---+---+---+---+---+---+---+----+----+----+----+----+
| n // 6           | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1  | 1  | 2  | 2  | 2  |
+------------------+---+---+---+---+---+---+---+---+---+---+----+----+----+----+----+

A table of numbers isn't going to give you a sense of repetions or progression. I've added a few colours intended to make the emerging patterns visible.

|color_coded|


You come here to learn visual programming in Sverchok. You will internalize the underlying math and algorithms more thoroughly by looking at the concept of programming from several angles. I want to show a few lines of code (python) that use ``%`` and ``//`` to calculate the Vertices of the grid. This code generates the x and y components of the vertices based purely on how many vertices are needed (``12 = 4 * 3``); Which is exactly what we want to do in the node tree shortly.

Below are two snippets of Python that calculate the same list of vertices. I'm showing both because it's an analogy to what you'll experience in any node tree. There is generally more than one way to achieve a result, there is almost never a "best" way. Some ways are faster in terms of processing speed, but they may be more difficult to understand by looking at the tree / code.

the ``for-loop`` version::

    num_verts_x = 4
    num_verts_y = 3
    j = num_verts_x * num_verts_y      # the * symbol means multiplication
    
    final_list = []
    for i in range(j):                 # passes: 0 1 2 3 4 5 6 7 8 9 10 11
       x = i % 4                       #  makes: 0 1 2 3 0 1 2 3 0 1 2 3
       y = i // 4                      #  makes: 0 0 0 0 1 1 1 1 2 2 2 2
       final_list.append((x, y, 0))

the ``list comprehension`` version::

    num_verts_x = 4
    num_verts_y = 3
    j = num_verts_x * num_verts_y      # the * symbol means multiplication

    final_list = [(i % 4, i // 4, 0) for i in range(j)]

Both bits of code calculate the same end result::

    [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), 
     (0, 1, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), 
     (0, 2, 0), (1, 2, 0), (2, 2, 0), (3, 2, 0)]

and those vertices are going to produce this eventually

|grid_only_test|

With any luck you are still smiling through this code detour, visual programming is very similar except with less typing. The plumbing of an algorithm is still the same whether you are clicking and dragging nodes to create a flow of information or writing code in a text editor.

**Making vertices**

A recipe which you should be able to hook up yourself by seeing the example image.

- ``Vector In``
- ``Sclar Math`` (3x) notice I minimized the Multiplication Node.
- ``A Number`` (2x)
- ``Number Range`` (int)

We multiply ``y=3`` by ``x=4`` to get ``12`` this is the number of vertices. This parameter determines the length of the range ``[0,1..11]`` (12 vertices, remember we start counting indices at 0).

|first_plane_image|

.. Note::
   i've added an Index Viewer node ( use alt+space to search for it) to display the indices of the vertices.

With all nodes hooked up correctly you can hook ``Vector In``'s output to the `vertices` socket of a ViewerDraw node to display the vertices. To test if it works you can use the sliders on the two Integer nodes to see the grid of vertices respond to the two parameters. Remember to put these sliders back to 3 and 4 (as displayed in the image), to continue to the next step.

**Making Polygons**

This might be obvious to some, so this is directed at those who've never done this kind of thing before. Polygons are described using the indices of the vertices that they use. This is where we use a notepad to write out the indexlist for the 6 polygons (two rows of 3 polygons, the result of a ``x=4 * y=3`` grid). The order in which you populate the list of polygon is determined by what you find more convenient.

For my example, I think of the X axis as the Columns, and I go from left to right and upwards

.. image:: https://cloud.githubusercontent.com/assets/619340/5514961/5ef77828-8854-11e4-81b4-4bd30a75d177.png

There are a few patterns to notice here.

- between polygon with index ``2`` and ``3`` there is a break in the pattern. For a grid of ``x=4, y=3`` like ours, the polygon with vertex indices ``[3,7,8,4]`` doesn't exist, if we did make that polygon it would connect one Row to the next like so:

  .. image:: https://cloud.githubusercontent.com/assets/619340/5515010/d58119fc-8856-11e4-837a-44beb57c3fb4.png

There's a relationship in these sequences::

  #    |A   B   C   D|
  #    ---------------
  0  = [0,  4,  5,  1]
  1  = [1,  5,  6,  2]
  2  = [2,  6,  7,  3]
  #  = [3,  7,  8,  4] .. not a valid polygon
  3  = [4,  8,  9,  5]
  4  = [5,  9,  10, 6]
  5  = [6,  10, 11, 7]

Given A we can calculate ``B``, ``C``, and ``D``. The relationship is namely:

.. Note::
  - B is 4 more than A, why 4? what's special about 4?
  - C is 1 more than B
  - D is 1 more than A
  - the magical ``offset`` number here is ``4``, and this is because we set the ``x-dimension`` to **4** for the time being.

the formula pattern for valid polygons can all be calculated from A if you know what the offset is::

  A = A
  B = (A + offset)
  C = (A + offset + 1)
  D = (A + 1)
  ...
  [A, (A + offset), (A + offset + 1), (A + 1)]

- We know how many polygons we need (let's call this number ``j``)
- We know there are interuptions in the polygons, between polygon index 2 and 3. You could already think ahead and consider that if we made a 4*4 grid, that we could encounter another row of polygons, and that there will be another jump in the pattern between polygon index 5 and 6.

it is useful to think of an algorithm that produces these index sequences based on a range from ``0 thru j-1`` or ``[0,1,2,3,4,5]``. We can first ignore the fact that we need to remove every n-th polygon, or avoid creating it in the first place. Whatever you decide will be a choice between convenience and efficiency - I will choose convenience here.

**A polygon Algorithm**

  Sverchok lets you create complex geometry without writing a single line of code, but you will not get the most out of the system by avidly avoiding code. Imagine living a lifetime without ever taking a left turn at a corner, you would miss out on faster more convenient ways to reach your destination.


It's easier for me to explain how an algorithm works, and give you something to test it with, by showing the algorithm as a program, a bit of Python. Programming languages allow you to see without ambiguity how something works by running the code.

**WIP - NOT ELEGANT**

this generates faces from a vertex count for x,y::

  ny = 3
  nx = 4

  faces = []
  add_face = faces.append

  total_range = ((ny-1) * (nx))
  for i in range(total_range):
      if not ((i+1) % nx == 0):  # +1 is the shift
          add_face([i, i+nx, i+nx+1, i+1])  # clockwise

  print(faces)

This is that same algorithm using the elementary nodes, can you see the similarity?

.. image:: https://cloud.githubusercontent.com/assets/619340/5515808/31552e1a-887c-11e4-9c74-0f3af2f193e6.png

.. |color_coded| image:: https://user-images.githubusercontent.com/619340/82607743-a7852f80-9bb9-11ea-8ec8-fee0246af9ba.png
.. |first_plane_image| image:: https://user-images.githubusercontent.com/619340/82651212-257a2280-9c1c-11ea-85f4-f33477fcff3f.png
.. |grid_only_test| image:: https://user-images.githubusercontent.com/619340/82651867-0760f200-9c1d-11ea-967c-cf297559561b.png





