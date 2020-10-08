Nesting
*******

    Come back to this document when you get confused about how data is stored in sockets.

Sverchok sockets can contain the elements of any number of objects. The number of objects is shown by the number beside the socket name. If you look at all the previous images, you'll notice most sockets have been outputting ``socketname. 1`` (a collection, containing one thing).

Each collection is a list of objects and these objects are themselves lists down to the most basic level which is the list of coordinates of each vertex.

A vertex is also a list of coordinates (X,Y,Z): 

``v0 = (1.0, 3.8, 2.5) v1 = (0.0, 0.0,0.0) v2 = (2.1, 3.1, 4.1)`` 

A list of vertexes is made of several lists of coordinates per vertex: 

``vertices = [(1.0, 3.8, 2.5), (0.0,0.0,0.0), (2.1,3.1,4.1)]``

Each list element has an index starting by "0" and ending in "n", from left to right.

In the above vertices list the indices for each vertex are:

``v0 = 0, v1 = 1, v2 = 2``

If, for example, you want to use the vertices to generate edges, you'll need to call upon their indexes to generate each edge. If we want to generate "edge 0" based on vertices v1 and v2 we will call them using index 1 and index 2 from that list, we will be creating an edge list like this: 

``edge = (1 ,2)``

If we want to generate an object composed by 3 edges from the above vertices indices we will need to figure out to retrieve the indices of the vertices we need and to create a list that might look like this:

``edges_list = [(0, 1), (1, 2), (2, 3)]``

At a fundamental level sverchok works by using nodes to creat lists of values, then using other nodes to evaluate those lists and generate new lists. Eventually the results of the final list will be used to generate the output that will be passed to the viewport with a viewer node.

This is why the nesting concept is fundamental in order to use Sverchok.

Let's look at some examples, (not necessarily outputting just one thing): 

NOTE to zeffii, what do you mean with this: (not necessarily outputting just one thing)?

|image_two_lines|


The image represents a set of nodes and the leftmost node output reads ``Vertices. 2``

Here the number ``2`` means that the ``Vertices`` socket contains two lists (*the vertex lists of two objects*). You'll see the ``Edges`` also has a 2 beside it, it also contains the ``edge_index`` lists of two objects.
 
  - the ``Vertices`` socket contains 2 collections (The first line has 4 vertices, the next line has 6)
  - the ``Edges`` socket contains 2 collections (The first line has 3 edges, the next line has 5 edges)

To know how many elements are in each socket's sublist, we can attach a ``List Length`` node. Each sublist represents a Level and it's values depends on how nested the level is. The default ``Level`` param of 1 will be sufficient for now.

Two Perpendicular Lines
=======================

verts
-----

Let's entertain the scenario above where a Node outputs two perpendicular "PolyLines", each with a different vertex and edge count. The data in that **vertex-socket** looks like.

- ``A``. (abstract top level) ``vertices. 2`` is a ``list`` with 2 items
- ``B``. zoom in, what's inside the "vertex_lists" data?::

  [vertex_list_1, vertex_list_2]

- ``C``. one level down, you can count the number of verts per object::

  [[v1, v2, v3, v4], [v1, v2, v3, v4, v5, v6]]

- ``D`` the literal data, you can see the coordinates::

  [ [(0,0,0),(1,0,0),(2,0,0),(3,0,0)], [(0,-1,0),(0.6,-1,0),(1.2,-1,0),(1.8,-1,0),(2.4,-1,0),(3,-1,0)] ]

- ``A, B, C and D`` are all different ways of thinking about the same data in the socket

this is the same as D, with different formatting, and a comment::

  [
    [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)],                                         # the vertices for object 1
    [(0, -1, 0), (0.6, -1, 0), (1.2, -1, 0), (1.8, -1, 0), (2.4, -1, 0), (3, -1, 0)]      # the vertices for object 2
  ]

here with some highlighting of the syntax

|socket_template_HL|

- The (orange) ``comma`` is what syntactically separates the objects.
- The inner (green)``Square Brackets`` are what encapsulate the vertices associated with one object.
- The outer most (blue) ``Square Brackets`` are what collect all sublists into something that we can pass through a socket  
- The parentheses enclose coordinates of each Vertex. In sverchok can also use square brackets to enclose a Vertex. The following are functionally equivalent in sverchok::

    vertex_1 = [x, y ,z]
    vertex_2 = (x, y, z)


- *Note*: We will use parentheses ``()`` and brackets ``[]`` interchangably in these lessons. There are real differences between ``[]`` and ``()``, and we'll ignore those for now.

edges
-----

Then here are the data associated with the ``Edges`` socket in the example

- ``A``. (abstract top level) ``edges. 2`` is a ``list`` with 2 items
- ``B`` zoom in, what's inside the "edge_index_lists"?::

  [edge_indices_1, edge_indices_2]

- ``C`` one level down::

  [[edge_1, edge_2, edge_3], [edge_1, edge_2, edge_3, edge_4, edge_5]]

- ``D`` literal data, there are a lot of brackets, i'll space them out a bit::

  [ [[0, 1], [1, 2], [2, 3]],  [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]] ]

same as D but with some formatting and a comment::

  [
    [ [0, 1], [1, 2], [2, 3] ],                            # the edge indices of object 1
    [ [0, 1], [1, 2], [2, 3], [3, 4], [4, 5] ]             # the edge indices of object 2
  ]

And that's structurally the same as what the stethoschope will show us

|stethoscope_show_topo|

Notice above that the edges are wrapped by outer *parentheses*, this isn't common, but it's not incorrect.

A Circle and a Cube
===================

Let's say we have two mesh objects that we'll be receiving from a node with ``Vertices`` and ``Edges`` sockets.
  - a crude circle with 6 verts and 1 face, and
  - a Cube (with 8 verts and 6 faces)

|image_of_circle_and_cube|

- Notice that each object is visually transformed away from the world origin, I will be using the untransformed coordinates.

let's describe them formally in psuedo-code::

  verts = [vertex_list_circle, vertex_list_cube]           # two vertex lists
  faces = [face_index_list_circle, face_index_list_cube]   # two face_index lists

zoomed in a level::

  verts = [
    [v1, v2, v3, v4, v5, v6],                              # the circle
    [v1, v2, v3, v4, v5, v6, v7, v8]                       # the cube
  ]

  faces = [
    [face_1],                                              # object 1: the circle's face, only one face!
    [face_1, face_2, face_3, face_4, face_5, face_6]       # object 2: a cube has 6 faces
  ]

This is what the literal data would look like::

  verts = [
    # circle verts
    [(0, 1, 0), (0.866, 0.5, 0), (0.866, -0.5, 0), (0, -1, 0), (-0.866, -0.5, 0), (-0.8660, 0.5, 0)],
    
    # cube verts, there are all  0.5, but because the zero is not considered significant we can ommit it.
    [[-.5, -.5, -.5], [-.5, .5, -.5], [.5, .5, -.5], [.5, -.5, -.5], [-.5, -.5, .5], [-.5, .5, .5], [.5, .5, .5], [.5, -.5, .5]]
  ]

  faces = [
    # the face index list for a circle of 6 vertices
    [[0, 1, 2, 3, 4, 5]], 
    
    # cube of 8 verts has 6 quad faces.
    [[4, 5, 1, 0], [5, 6, 2, 1], [6, 7, 3, 2], [7, 4, 0, 3], [7, 6, 5, 4], [0, 1, 2, 3]]
  ]

The final nail
==============

Let's say we have a node, and it outputs the Face of a single object (a polygon, a quad). so the socket will read something like:

- ``Faces. 1``.

What do you expect the output to look like if the only face is described by 4 vertex indices ``0, 1, 2, 3``, and why?::

  # the face
  face_1 = [0, 1, 2, 3]

  # the object has no more faces, but we wrap the face anyway
  faces_of_obj_1 = [face_1]

  # and we wrap all the objects, here it's just one object
  faces = [faces_of_obj_1]

  # so 0, 1, 2 ,3 becomes
  [[[0, 1, 2, 3]]]

This is going to look weird (and arguably redundant) in the scenario where the socket only describes one object. You'll almost never see sockets outputting a single face, except for the most primitive of geometry nodes.

-----------

.. NOTE::
   It's possible that none of this makes sense to you. In that case I encourage you to hook a stethoscope into any node that isn't outputting what you expect. More about debugging in a later Note.



.. |image_two_lines| image:: https://user-images.githubusercontent.com/619340/82352501-61d03780-99fe-11ea-9051-cb120d753668.png
.. |socket_template_HL| image:: https://user-images.githubusercontent.com/619340/82430084-2761ab80-9a8d-11ea-9ce1-a315b3b46af4.png
.. |stethoscope_show_topo| image:: https://user-images.githubusercontent.com/619340/82446982-e5922e80-9aa7-11ea-9520-7ac0523828c2.png
.. |image_of_circle_and_cube| image:: https://user-images.githubusercontent.com/619340/82449311-525af800-9aab-11ea-9ee8-e5e5cb3db7fa.png
