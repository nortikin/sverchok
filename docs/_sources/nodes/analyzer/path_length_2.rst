Path Length
===========

.. image:: https://user-images.githubusercontent.com/14288520/195679077-a19d806d-1b6f-4400-a690-4ab116be8e88.png
  :target: https://user-images.githubusercontent.com/14288520/195679077-a19d806d-1b6f-4400-a690-4ab116be8e88.png

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

.. image:: https://user-images.githubusercontent.com/14288520/195711286-8a23553c-a479-4a60-bc97-f5d639d0efa7.png
  :target: https://user-images.githubusercontent.com/14288520/195711286-8a23553c-a479-4a60-bc97-f5d639d0efa7.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Examples of usage
-----------------

Calculating all values for a curve:

.. image:: https://user-images.githubusercontent.com/284644/75791140-f3c88c80-5d8d-11ea-8d43-5a53965f0fe0.png
  :target: https://user-images.githubusercontent.com/284644/75791140-f3c88c80-5d8d-11ea-8d43-5a53965f0fe0.png

* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

Measuring an icosphere:

.. image:: https://user-images.githubusercontent.com/14288520/195712427-28089fe6-1cb9-4501-af86-a10a4ec2fd6f.png
  :target: https://user-images.githubusercontent.com/14288520/195712427-28089fe6-1cb9-4501-af86-a10a4ec2fd6f.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

Using the Path Length node to place circles of one meter of diameter along a given curve:

.. image:: https://user-images.githubusercontent.com/14288520/195715465-d75df019-e40e-43b0-8572-f1601d668a1f.png
  :target: https://user-images.githubusercontent.com/14288520/195715465-d75df019-e40e-43b0-8572-f1601d668a1f.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* FLOOR: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Vector-> :doc:`Vector Interpolation </nodes/vector/interpolation_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`