Nesting
*******

    Come back to this document when you get confused about how data is stored in sockets.

Sverchok sockets can contain the elements of any number of objects. The number of objects is shown by the number beside the socket name. If you look at all the previous images, you'll notice most sockets have been outputting ``socketname. 1`` (one "thing")

Let's look at some examples, (not necessarily outputting just one thing):

|image_two_lines|

Here the number ``2`` means that the ``Vertices`` socket contains two lists (*the vertex lists of two objects*). You'll see the ``Edges`` also has a 2 beside it, it also contains the ``edge_index`` lists of two objects.
 
  - the ``Vertices`` socket contains 2 collections (of 4 vertices each.)
  - the ``Edges`` socket contains 2 collections (of 3 edges each.)

To know how many elements is in each socket's sublist, we can attach a ``List Length`` node. You'll see the number of elements corresponds with the number of vertices and edges of each object.

|ListLengthShowOne|

Two Perpendicular Lines
-----------------------

Let's entertain the scenario where a Node outputs two perpendicular lines, each has 4 vertices. The data in that **vertex-socket** looks like::

  # A -- "vertices. 2" (abstract top level)
  vertex_lists

  # B -- zoom in, what's inside the "vertex_lists" data?
  [vertex_list_1, vertex_list_2]

  # C -- one level down, you can count the number of verts per object
  [[v1, v2, v3, v4], [v1, v2, v3, v4]]

  # D -- literal data (either using parenthesis () or square brackets [] ) , you can see the coordinates.
  [[(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)], [(0, 0, 1), (1, 0, 1), (2, 0, 1), (3, 0, 1)]]

`A, B, C and D` are all different ways of thinking about the same data in the socket::

  # this is the same as D, with different formatting, and a comment. The ``comma`` is what syntactically separates the objects.
  [
    [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)],    # the vertices for object 1
    [(0, 0, 1), (1, 0, 1), (2, 0, 1), (3, 0, 1)]     # the vertices for object 2
  ]

Then here is the data associated with the ``Edges`` socket in the example::

  # A -- the "edges. 2" (abstract top level)
  edge_index_lists

  # B -- zoom in, what's inside the "edge_index_lists" ?
  [edge_indices_1, edge_indices_2]

  # C -- one level down
  [[edge_1, edge_2, edge_3], [edge_1, edge_2, edge_3]]

  # D -- literal data, yes..there's a lot of brackets..
  [[[0, 1], [1, 2], [2, 3]], [[0, 1], [1, 2], [2, 3]]]

  # or with some formatting and a comment
  [
    [[0, 1], [1, 2], [2, 3]],      # the edge indices of object 1
    [[0, 1], [1, 2], [2, 3]]       # the edge indices of object 2
  ]

And that's structurally the same as what the stethoschope will show us

|showing_stethoscope_2obj|

A Circle and a Cube
-------------------

Let's say we have two mesh objects
  - a crude circle with 6 verts and 1 face, and
  - a Cube (with 8 verts and 6 faces)

let's describe them formally in code::

  verts = [vertex_list_circle, vertex_list_cube]           # two vertex lists
  faces =  [face_index_list_circle, face_index_list_cube]  # two face_index lists
  
  # or ..zoomed in again
  verts = [
    [v1, v2, v3, v4, v5, v6],          # the circle
    [v1, v2, v3, v4, v5, v6, v7, v8]   # the cube
  ]
  faces = [
    [face_1],                                          # the circle's face, only one face!
    [face_1, face_2, face_3, face_4, face_5, face_6]   # a cube has 6 faces
  ]

  # viewing all data



.. |image_two_lines| image:: https://user-images.githubusercontent.com/619340/82310757-1188b380-99c5-11ea-99e6-af9b61120934.png
.. |showing_stethoscope_2obj| image:: https://user-images.githubusercontent.com/619340/82338934-bfa85380-99ed-11ea-8463-89394bd931c9.png
.. |ListLengthShowOne| image:: https://user-images.githubusercontent.com/619340/82342843-65f65800-99f2-11ea-959b-775070136a07.png