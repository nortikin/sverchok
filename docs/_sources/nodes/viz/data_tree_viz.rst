Data Tree Viz
=============

Functionality
-------------

The node displays the shape of input data in the node editor's window.
The data is represented as a tree; the root of the tree is whole data (root
list). Items of the outer nesting level are level 1 branches of the tree; Items
of level 1 lists are level 2 branches, and so on. The node draws the tree as it
is growing from center to outside; so the outermost nodes of the tree (leaves)
are atomic data items: numbers, curves and so on. Nodes which are not leaves
represent lists and tuples.

This node can be used instead (or together with) Stethoscope node, to quickly
asses the nesting level of data and it's size. Stethoscope is more focused on
displaying data items itself, while Data Tree Viz is more focused on displaying
data structure.

Inputs
------

This node has one input: **Data**. This input can consume any type of input data, with any nesting.

Parameters
----------

This node has the following parameters:

* **Active**. Toggle button which controls whether the node should draw in node
  editor's background. Enabled by default.
* **Simplify**. If checked, then, if node decides that there are too much items
  in a list on some level of nesting, it draws properly only the beginning and
  the end of the list; the middle of the list is replaced with the dotted line,
  and it's internals (if there are any) are not displayed at all. If not
  checked, then the node tries to display all items and branches of data. When
  not checked, if you pass a lot of data (like, hundreds or thousands of
  values) into the node, it can work slow, and the result will be probably not
  insightful. Checked by default.
* **Branching points color**. The color to be used to draw branching points.
  Leave nodes (which represent atomic data items, not lists or tuples) are
  always drawn with a color of a socket corresponding to data type (numbers are
  displayed in green, curves in blueish and so on).
* **Points size**. Displayed size of branching points. The default value is 4.
* **Branch lines color**. The color to be used to draw branch lines.
* **Branch lines thickness**. Thickness of branch lines. The default value is 1.
* **Display circles**. If checked, then circles are displayed which indicate
  where items of the same nesting level lie.
* **Circles color**. The color to be used to draw circles which indicate
  nesting levels.
* **Circles thickness**. Thickness of circles. The default value is 3.
* **Display background**. If checked, then behind data tree a colored square is
  drawn (can be useful in some color themes). Unchecked by default.
* **Background color**. Color of the background square.
* **Size**. Drawing size. The default value is 250, which is slightly bigger
  than average node.

Outputs
-------

This node has no outputs.

Examples of Usage
-----------------

In this example, data is generated in such a way, that the first sub-list has 1
item, the second sub-list has 2 items and so on. Also Graft mode is enabled on
the output socket of "Number Range" node, which creates additional nesting
level - and outer circle of the shape. Here you can see that items are drawn
beginning at the bottom of the circle, counterclockwise.

.. image:: https://github.com/user-attachments/assets/74d95ec8-5de6-4285-8877-1f4b6a055cbe
  :target: https://github.com/user-attachments/assets/74d95ec8-5de6-4285-8877-1f4b6a055cbe

Here structure of Vertices output of a Box node is represented. On the outer
nesting level, there is 1 item (because there is only 1 box) - which is
represented by only one branch growing from the center. That single sub-list
has 8 items (8 vertices of the cube) - hence 8 branches grow on the second
nesting level. And on the third nesting level, each of those 8 branches has 3
sub-branches (because each vertex of the cube is a tuple of 3 numbers).

.. image:: https://github.com/user-attachments/assets/c001e847-addb-46c8-9837-1f31f5c9a08d
  :target: https://github.com/user-attachments/assets/c001e847-addb-46c8-9837-1f31f5c9a08d

Similar, but here 3 cubes are generated, so 3 branches grow from the center;
each of those branches is organized in the same way as for one cube.

.. image:: https://github.com/user-attachments/assets/b98a4f86-faec-4b1c-baa6-15602298e6f3
  :target: https://github.com/user-attachments/assets/b98a4f86-faec-4b1c-baa6-15602298e6f3

An example of using it with Curves. Here original curve (circle) is subdivided in 5 segments, and then each of segments is subdivided in 9 sub-segments. So you can see that 5 branches grow from the center, and from each of them 9 sub-branches grow.

.. image:: https://github.com/user-attachments/assets/bf0a4aa4-2d36-4bac-bbe9-fb4de24582a0
  :target: https://github.com/user-attachments/assets/bf0a4aa4-2d36-4bac-bbe9-fb4de24582a0

