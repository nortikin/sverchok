**********************************
Introduction to modular components
**********************************

**prerequisites**

Same as lesson 01.


Lesson 02 - A Circle
--------------------

This lesson will introduce the following nodes: ``List Length, List Shift, List Zip, Formula``, and use nodes seen in Lesson 01.

This will continue from the previous lesson where we made a plane from 4 vectors. We can reuse some of these nodes in order to make a Circle. If you saved it as suggested load it up or recreate it from scratch by cross referencing this image.

|former_final_image|

**A Circle**

Blender has a Circle primitive, Sverchok also has its own Circle primitive called the `Circle Generator`. We will avoid using the primitives until we've covered more of the fundamental nodes and how they interact.

**Dynamic Polygons**

In the collection of nodes we have in the Node View at the moment, we have manually entered the polygon indices. As mentioned earlier, as soon as you need to link many vertices instead of the current 4, you will want to make this *list creation* generative/automatic. You will probably also want to make it respond dynamically by adding new segments automatically if the vertex count changes. 

Because this is a common task, there's a dedicated node for it called ``UV Connect``, but just like the `Circle` generator node we will avoid using the ``UV Connect`` node until the basics are covered. Learning how to build these things yourself will teach you how to use the fundamental nodes and their place in **Visual Programming**. This is about the journey.

**Generating an index list for the polygon**

In order to make the list automatically, we should know how many vertices there are at any given moment.

- ``Add -> List Main -> List Length``

The `List Length` node lets you output the length of incoming data. Because data is passed through Sverchok as lists and lists of lists, it also lets you pick what ``nested-level`` of the data you want to inspect. It's worth reading the **reference** of this node for a comprehensive tour of its capabilities.

1) hook the ``Vector In`` output into the ``Data`` input of ``List Length`` node
2) hook a new ``Stethoscope`` up to the output of the ``List Length`` node.
3) notice the *Level* slider is set to ``1`` by default, you should see Stethoscope shows output.

|show_stethoscope_with_listlength|

Notice that, besides all the square brackets, you see the length of the incoming data is `4`, as expected. We want to generate a sequence (list) that goes something like ``[0,1,2,...n]`` where n is the index of that last vertex. In Python you might write something like this this::

  n = 4
  range(start=0, end=n, step=1)
  >> [0, 1, 2, 3]

To generate the index list for the polygon we need a node that outputs a sequential list of integers, Sverchok has exactly such a node and it accepts values for `start`, `step` and `count` as parameters. This is what the ``Number Range`` node does (in *Step* mode).

- ``Add -> Numbers -> Number Range``

1) Set the mode of the newly added ``Number Range`` node to *Int* and submode to *Step*.
2) Make sure ``start = 0`` and ``step = 1``
3) Hook the output of ``List Length`` into the ``count`` socket of ``Number Range``
4) Remove the ``Simple Topology`` node.

before we go to point ``5``, you need to understand a thing called *Nesting*. we'll have to explain a few things. Read the :doc:`Nesting <../nesting>`, page if you haven't already.

 *Note* View the output of the ``Number Range`` socket using stethoscope. you'll see::

  [[0,1,2,3]]

|not_nested_enough|

If you have gone through the notes on nesting, then you'll understand why we need another set of *Square Brackets* to produce a structure that the ``Viewer Draw`` node will understand ``as one object with one face``, it needs to be ``[[[0,1,2,3]]]``. 

5) Connect the output of ``Number Range`` into a ``Formula`` node to add Brackets (an extra level of nesting), 

- type in ``x`` into the formula field
- the node will make one socket available
- press the ``Wrap`` toggle

6) Hook the output of ``Formula`` to the ``Faces`` socket of ``Viewer Draw``.

  *Note*: connect a Stethoscope also to the output of ``Number Range`` in order to see the generated list for yourself

|using_range_node_one|

**Generating the set of circular verts**

The above takes care of automatically generating the face indices for any number of incoming vertices. Now we want to automate the creation of Vertices. The 4 verts we've had from the very beginning are already points on a circular path, we can make a change to ``Number Range`` node to finally see this Circle emerge.

- Set the ``mode`` of the ``Number Range`` node to ``Range``
- Set the ``stop`` parameter to ``2.0``
- Set the ``step`` to ``0.2`` for example.

``2.0 / 0.2 = 10``, this means the Float Series node will now output ten values ``[0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8]``. Notice that it does not output 2.0 at the end, because this mode excludes the terminating value. (called non inclusive)

|automatic_circle_from_plane|

You can see the beginnings of a circle.

**Forcing an even spread of Vertices**

Above we manually set the step to ``0.2``, if you are as lazy as we are, then you'll want to automate that. We will add nodes to do the calculation for us. Think about how you might do that. The formula is::

  2.0 / n = step_distance

where ``n`` is how many vertices you want, and the 2 here is `2 PI`. This calls for a ``Scalar Math`` node and a ``Number`` node.

- ``Add -> Numbers -> Scalar Math``
- ``Add -> Numbers -> A Number``

.. Note::
   Get in the habbit of adding the core nodes via the Node View's ``Right Click`` menu, it is a quick route to most of these nodes.

   |right_click_menu|

1) Set the ``Scalar Math`` node mode to *Reciprocal* which is ``1 / x``
2) Set the ``Number`` node to *Int* mode and slide the number to ``10``, and connect the output into the *reciprocal* ``Scalar Math`` node.
3) In the image below I've connected a Stethoscope to the output of the ``Number Range`` node to see the value of this computation
4) Finally, ``2 PI`` is the same as ``1 Tau``, set the ``Pi * x`` *Scalar Math* node to ``Tau * x`` and hook up the output of the Reciprocal *Scalar Math* node into the *step* socket of Number Range

.. Note::
   You should see something like this, if not you can by now probably figure out what to do.
   |use_reciprocal|

.. Caution::
   This is starting to get crowded, let's minimize nodes.

Before going any further it's time to draw attention to the fact that you can make nodes smaller. This minimizing feature is called ``hide``, we can argue about how good or badly that option is named. With Any node selected press ``H``, to *minimize/hide*.

|minimized|

In Sverchok we added special functionality to certain nodes to draw information about themselves into their header area. This allows you to see what the node is supposed to be doing even when the UI is minimized. Currently the ``A number``, ``Scalar and Vector Math``, and ``List Length`` nodes have this behaviour because they are common and will compete for screen real-estate. Other nodes have been added to that list over time.

In future lessons you will often see minimized/hidden nodes

Polygon was easy, what about Edges?
-----------------------------------

Remember, there are nodes that can take an incoming set of vertices and generate the required Edges ``index lists``. Because we're exploring the modular features of Sverchok we'll build our own ``Edges`` generator.

The edge index list of the square looked like::

  [[0,1],[1,2],[2,3],[3,0]].

For the Circle of a variable number of vertices that list will look like::

  [[0,1],[1,2],...,[n-1,n],[n,0]]

Notice I'm just showing the start of the list and the end, to indicate that there is a formula for it based purely on how many verts you want to chain together. As usual ``n`` represents the number of vertices in question.

In python that formula can be expressed using a ``for-loop`` or a ``list comprehension``.

the `for-loop`::

  n = 5
  for i in range(n):
      print(i, (i+1) % n)
  
  >>> 0 1
  >>> 1 2
  >>> 2 3
  >>> 3 4
  >>> 4 0

the `list comprehension`::

  n = 5
  edges = [[i, (i+1) % n] for i in range(n)]
  print(edges)
  
  >>> [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]]

In Sverchok the end result will be the same, but we'll arrive at the result in a different way.

The second index of each edge is one higher than the first index, except for the last edge. The last edge closes the ring of edges and meets back up with the first vertex. In essenence this is a wrap-around. Or, you can think of it as two lists, one of which is shifted by one with respect the other list::

  indices                = [0, 1, 2, 3, 4]
  indices_shifted_by_one = [1, 2, 3, 4, 0]
  
  for a, b in zip(indices, indices_shifted_by_one):
      print([a, b])
  
  >>> [0, 1]
  >>> [1, 2]
  >>> [2, 3]
  >>> [3, 4]
  >>> [4, 0]

Sverchok has a node for this called `List Shift`. We'll zip the two lists together using `List Zip` node.

- ``add -> List Struct -> List Shift``
- ``add -> List Main -> List Zip``

.. HINT::
   Seriously; Instead of trawling through menus and submenus, use the ``alt+space`` search. type in Shift and Zip and navigate down with the cursor keys, then hit Enter to add the node to the tree.

1) Hook the output of ``Number Range`` into the first *Data* socket of the ``List Zip`` node.
2) Hook the output of ``Number Range`` also into the *Data* socket of the ``List Shift`` node.
3) To make the wrap-around, simply set the *Shift slider* to ``-1``.
4) connect the output of ``List Shift`` to the second *Data* input of ``List Zip`` (this node creates new sockets on the fly).
5) Make sure the level parameter on ``List Zip`` is set to ``1``.
6) Hook up a Stethoscope to the output of ``List Zip`` to verify

Notice in this image I have minimized/hidden (shortcut H) a few nodes to keep the node view from getting claustrophobic. 

|current_pre_final| 

7) hook up the output of ``List Zip`` straight into the *Edges* socket of``Viewer Draw``.

|current_final|

**End of lesson 02**

Save this .blend you’ve been working on as Sverchok_Unit_01_Lesson_02 for future tutorials or as reference if you want to look something up later.

You now know how to create basic shapes programmatically using Sverchok nodes. In Lesson 03 a dynamic grid will be generated, but first relax and reiterate what has been learned so far.

.. NOTE::
   ``Viewer Draw`` automatically generates Edges when you pass one or more Vertices and Polygons. This means in practice when you already have the Polygons for an object then you don't need to also pass in the Edges, they are inferred purely from the indices of the incoming Polygons.

.. |former_final_image| image:: https://user-images.githubusercontent.com/619340/82145036-31df3380-9848-11ea-84a7-1ed761c00e84.png
.. |show_stethoscope_with_listlength| image:: https://user-images.githubusercontent.com/619340/82145112-cd70a400-9848-11ea-9905-3824f7e92e8c.png
.. |not_nested_enough| image:: https://user-images.githubusercontent.com/619340/82303630-7dfeb500-99bb-11ea-9ea3-bf695d2537a6.png
.. |using_range_node_one| image:: https://user-images.githubusercontent.com/619340/82150782-4f68c900-9859-11ea-9caf-7dec0e35a54e.png
.. |automatic_circle_from_plane| image:: https://user-images.githubusercontent.com/619340/82462057-64dd2d80-9abb-11ea-9b6b-4f3663a32451.png
.. |use_reciprocal| image:: https://user-images.githubusercontent.com/619340/82474432-57c83a80-9acb-11ea-983f-6960822ee2aa.png
.. |right_click_menu| image:: https://user-images.githubusercontent.com/619340/82489407-e1830280-9ae1-11ea-97ef-e43d1d9914f8.png
.. |minimized| image:: https://user-images.githubusercontent.com/619340/82501213-2fedcc80-9af5-11ea-94ca-39ef089b7756.png
.. |current_final| image:: https://user-images.githubusercontent.com/619340/82545240-b090e500-9b56-11ea-9655-3647f59ce854.png
.. |current_pre_final| image:: https://user-images.githubusercontent.com/619340/82545480-09f91400-9b57-11ea-8fcb-88392597d7cb.png