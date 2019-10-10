Diameter
========

Functionality
-------------

This node calculates the diameter of input set of vertices.

It can calculate diameter in two ways:

* General diameter, i.e. maximum distance between any two vertices from input set.
* Diameter along specified direction (axis), i.e. the length of the projection
  of whole input vertices set to specified direction.

Inputs
------

This node has the following inputs:

* **Vertices** - vertices to calculate diameter of. This input is mandatory for the node to function.
* **Direction** - direction, along which diameter should be calculated. If this
  input is not connected, then the node will calculate "general diameter" of
  input vertices set.

Outputs
-------

This node has one output: **Diameter** - calculated diameter of vertices set.

Examples of usage
-----------------

Suzanne has "general diameter" of 2.73:

.. image:: https://user-images.githubusercontent.com/284644/58649984-03aad000-8327-11e9-90b8-0c39f328402a.png

Diameter of Suzanne along some diagonal direction is 2.44. Here the direction
is drawn as green line, and the projection of Suzanne to that direction is
marked with red dots:

.. image:: https://user-images.githubusercontent.com/284644/58649983-03aad000-8327-11e9-852a-a75d8eb4aad4.png

