Fractal curve
=============

Functionality
-------------

This node generates a fractal curve, by replacing each edge of input curve with a copy of that curve, several times.

NB 1: Number of vertices in the output curve grows exponentially with number of iterations. 

NB 2: Usually you will want to use curves, for which diameter (distance between
to most distant vertices) is less than distance from the first vertex to the
last. Otherwise, the output curve can grow very large.

NB 3: Usually you will want to use curves, edges of which have nearly the same length.

Inputs
------

This node has one input: **Vertices** - vertices of input curve. Vertices
should go in the order in which they appear in the curve.

Parameters
----------

This node has the following parameters:

* **Iterations**. Number of iterations. If zero, then output curve will be
  exactly the same as input one. Default value is 3. 
* **Min. length**. Minimum length of edge to substitute. Fractal substitution
  process will stop for specific edge if it's length became less than specified
  value. Minimal value of zero means that fractal substitution process is
  stopped only when maximum number of iterations is reached.
* **Precision**. Precision of intermediate calculations (number of decimal
  digits). Default value is 8. This parameter is available only in the **N** panel.

Outputs
-------

This node has one output: **Vertices** - vertices of the output curve. Vertices
go in the order in which they appear in the curve. You may want to use **UV
Connector** node to draw edges between these vertices.

Examples of usage
-----------------

