Spyrrow Nester
==============

Dependencies
------------

This node requires Spyrrow_ library to function.

.. _Spyrrow: https://github.com/PaulDL-RS/spyrrow

Functionality
-------------

This node is intended for solving 2D strip packing (nesting) problems_.

.. _problems: https://en.wikipedia.org/wiki/Strip_packing_problem

The user provides a number of 2D objects and the height of the strip; the node
will try to pack objects into strip as densely as possible.

The node can rotate objects in order to pack them more densely, if it is allowed.

It is possible to generate several copies of each input object.

**Warning**: Unfortunately, Spyrrow library has not very good errors handling.
Sometimes, if it does not like your input objects or settings, it will print
error to console and stop. What is worse, as a consequence whole processing of
Sverchok will stop, until you restart Blender. This node does some preliminary
checks for most common situations which Spyrrow does not like, but some more
tricky situations can still be handled badly.

Inputs
------

This node has the following inputs:

* **Vertices**. Vertices of objects to be packed. This input is mandatory.
* **Edges**. Edges of objects to be packed.
* **Faces**. Faces of objects to be packed. If neither **Edges** or **Faces**
  inputs are connected, then it will be assumed that input objects have trivial
  topology: just a polygon consisting of one face, and the order of points in
  the **Vertices** input defines the order of polygon vertices.
* **Count**. Number of copies of each input object which has to be generated.
  This input can consume a separate value for each input object; for example,
  you may instruct the node to generate one copy of the first object, two
  copies of the second object, and so on. The default value is 1.
* **Strip Height**. Height of the strip where the objects are to be placed. The
  default value is 4.0.
* **Separation**. Minimum distance which must be left between the objects when
  they are packed. The default value is 0, meaning that the objects are allowed
  to touch each other.
* **Angle**. This defines possible values of rotation angles (in degrees),
  which the node is allowed to use. This input is available only when the
  **Rotations** parameter is set to **Restrict by step** or **Only specified
  angles**. The default value is 90 degrees.
* **Seed**. Random seed. The packing algorithm being used has some random
  component in it. Different values of Seed input will produce different
  placements of objects. The default value is 0.

Parameters
----------

This node has the following parameters:

* **Activate**. If this button is not pressed, the node will just generate
  empty output without actual processing. It sometimes makes sense to disable
  the node while rearranging things in the tree, because calculation of new
  packing on each tree change can take time. Checked by default.
* **Plane**. Coordinate plane where all objects lie. The available options are
  **XY**, **XZ** and **YZ**. The default option is **XY**.
* **Rotations**. This defines whether the node is allowed to rotate objects
  while placing them. The available options are:

  * **No rotations**. The node will never rotate objects. This is the default option.
  * **Arbitrary rotation**. The node is allowed to rotate objects arbitrarily.
  * **Resrtict by step**. The node is allowed to rotate objects, but only by
    angles which are multiples of the angle provided in the **Angle** input.
    For example, if **Angle** input is set to 45, then the node is allowed to
    rotate objects by 0, 45, 90, 135, and so on degrees.
  * **Only specified angles**. If this option is selected, it usually makes
    sense to connect some node which is producing numbers to the **Angle**
    input. It is expected that the **Angle** input will contain a list of
    allowed rotation angles for each input objects. For example, you may
    instruct the node that it is allowed to rotate the first object by 0 or 180
    degrees, but the second object can be rotated by 0, 90, 180 or 270 degrees.
    If the **Angles** input is not connected, then only one rotation angle will
    be allowed for all objects.

* **Total time**. Total computation time the packing algorithm is allowed to
  spend, in seconds. Usually the more time you give it, the better result you
  will have; but in many cases even with small values like 1 or 2 seconds you
  will have good enough results. The default value is 10 seconds.
* **Use all CPU cores**. If checked, then the node will be allowed to use as
  many CPU cores as it finds possible. Checked by default.
* **Threads**. This parameter is visible only when the **Use all CPU cores**
  parameter is not checked. This defines the number of CPU cores the node is
  allowed to use.
* **Flat output**. Numeric input of this node (**Strip Height**, **Separation**
  and so on) can consume lists of nesting 2 (lists of lists of numbers), as
  usually used in Sverchok; this means that the node can consume a separate
  list of objects for each of those numeric values; which in turn means, that a
  list of lists of lists of objects will be produced. Usually you do not need
  such deep nesting. If this parameter is checked, the node will generate just
  a plain list of lists of objects. Checked by default.
* **Allow early termination**. This parameter is available in the N panel only.
  It defines whether to allow early termination of the algorithm. Checked by
  default.
* **Support non-trivial topology**. This parameter is available in the N panel only.
  If checked, then the node can process objects which consist of several faces.
  It is usable in many cases, so this parameter is checked by default. However
  it takes some additional time to find outer boundary of each object in such
  case; so to save some time if all your objects consist of one face (n-gon)
  only, you may disable this parameter.
* **Quadtree depth**. This parameter is available in the N panel only. Maximum
  depth of the quadtree used by the collision detection engine. Must be
  positive, common values are 3,4,5. Defaults to 4.

Outputs
-------

This node has the following outputs:

* **Vertices**. Vertices of the packed objects.
* **Edges**. Edges of the packed objects.
* **Faces**. Faces of the packed objects.
* **Indices**. For each generated object, this output contains the index of
  input object this output object is copy of. If **Count** input is set to 1
  (by default), the **Indices** output will just contain ``[[0, 1, 2, ...]]``.
* **Matrices**. For each generated object, this output contains a matrix which
  was used to place the original object to it's place in packing. Note that if
  **Count** input is not just set to 1, but some list of counts is provided,
  then in order to use the **Matrices** output you have to use it together with
  **Indices** output and "List item" node, in order to understand which exactly
  original object do you have to apply the matrix to.
* **StripWidth**. Resulting width of the strip.
* **Density**. Resulting packing density. Values closer to 1.0 mean more dense
  packing.
* **StripVertices**. Vertices of the rectangle which represents the resulting
  strip, on which all objects are packed.
* **StripEdges**. Edges of the rectangle which represents the resulting strip.
* **StripFaces**. Faces of the rectangle which represents the resulting strip.

Examples of Usage
-----------------

.. image:: https://github.com/user-attachments/assets/5a5aa63e-015e-4b50-bf30-52f7f56ca2bc
  :target: https://github.com/user-attachments/assets/5a5aa63e-015e-4b50-bf30-52f7f56ca2bc

