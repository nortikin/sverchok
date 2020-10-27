Vector Out
==========

Functionality
-------------

Outputs values/numbers from vertices.

The node will accept regular lists or lists of NumPy arrays if the arrays have two axis arrays with shape [n,3]

It can also output Numpy arrays (flat arrays) when using the activating the "Output NumPy" parameter.
(See advanced parameters)

Inputs
-------

**Vector** - Vertex or series of vertices

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Simplify Output**: Method to keep output data suitable for most of the rest of the Sverchok nodes
  - None: Do not perform any change on the data. Only for advanced users
  - Flat: It will flat the output to keep vectors list in Level 3 (regular vector list)

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster if you input NumPy arrays).

Outputs
-------

**x** - velue or series of values
**y** - velue or series of values
**z** - velue or series of values

Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4905358/0a4e7df4-644f-11e4-8ff1-1530c7aac8dc.png
  :alt: with vector in
