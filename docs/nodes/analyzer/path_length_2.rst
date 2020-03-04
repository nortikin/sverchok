Path Length
===========

Functionality
-------------

This node calculates lengths of edges, or length of a path composed from edges.
It is not actually required that the edges provided form one-way path (like
`1--2--3--4`), the node can work with arbitrary graph of edges; however,
"cumulative sum" output will work predictable only for path-like meshes.

Inputs
------

This node has the following inputs:

* **Vertices**. Path (mesh) vertices. This input is mandatory.
* **Edges**. Edges of the path. If this input is not connected, the node will
  assume that the vertices provided are connected by consequent edges in the
  same order in which the vertices are provided in the **Vertices** input; for
  example, if there are vertices "1", "2", "3" (in this order), it will be
  assumed that there are edges `(1,2)`, `(2,3)`.

Parameters
----------

This node has no parameters.

Outputs
-------

This node has the following outputs:

* **SegmentLength**. This output contains lengths of separate segments (i.e.,
  edges). The values are in the same order as the edges in the **Edges** input.
* **TotalLength**. Total length of all segments (edges) - i.e., total length of
  the path. This is equal to sum of all values in **SegmentLength** output.
* **CumulativeSum**. This output contains cumulative (running) sum of segment
  lengths in the same order in which they are present in the **SegmentLength**
  output. The first value in this output is always zero (total length of zero
  edges). The last value in this output is always equal to total length of the
  path. Since the length of any segment is not less than zero, this output
  always contains a non-decreasing sequence. For example, if **SegmentLength**
  output contains `[1.1, 1.2, 1.3]`, then **CumulativeSum** output will contain
  `[0.0, 1.1, 2.3, 3.6]`.
* **CumulativeSum1**. The same as **CumulativeSum**, but divided by the total
  length of the path. The first value in this output is always zero. The last
  value is always `1.0`. This output always contains a non-decreasing sequence.
  For example, if **SegmentLength** output contains `[1, 2, 3, 4]`, then
  **CumulativeSum1** output contains `[0.0, 0.1, 0.3, 0.6, 1.0]`.

This node calculates values only for those outputs which are connected to somewhere.

Examples of usage
-----------------

Calculating all values for a curve:

.. image:: https://user-images.githubusercontent.com/284644/75791140-f3c88c80-5d8d-11ea-8d43-5a53965f0fe0.png

Measuring an icosphere:

.. image:: https://user-images.githubusercontent.com/284644/75791456-69ccf380-5d8e-11ea-98b4-9332ec743be7.png

Using the Path Length node to place circles of one meter of diameter along a given curve:

.. image:: https://user-images.githubusercontent.com/284644/75792097-4bb3c300-5d8f-11ea-8d88-5e6f75a427de.png

