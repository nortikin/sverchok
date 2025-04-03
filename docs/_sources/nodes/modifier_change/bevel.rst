Bevel
=====

.. image:: https://user-images.githubusercontent.com/14288520/197881511-44a2a2d4-b5a1-496c-bdf4-9242d0fe7e89.png
  :target: https://user-images.githubusercontent.com/14288520/197881511-44a2a2d4-b5a1-496c-bdf4-9242d0fe7e89.png

Functionality
-------------

This node applies Bevel operator to the input mesh. You can specify edges to be beveled.

.. image:: https://user-images.githubusercontent.com/14288520/197888952-7b24fc4f-37a0-474d-bc4b-692c544a2447.png
  :target: https://user-images.githubusercontent.com/14288520/197888952-7b24fc4f-37a0-474d-bc4b-692c544a2447.png

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Polygons**
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.
- **BevelFaceData**. Face data to be assigned to bevel faces. This input is
  expected to contain one item per input objects. If this input is not
  connected, then bevel faces will be assigned with face data from adjacent
  faces.
- **BevelEdges / VerticesMask**.  Edges or vertices to be beveled. If this
  input is not connected, then by default all will be beveled. This parameter
  changes when ``Vertex mode`` flag is modified.  On vertex mode it will expect
  a list of True/False (or 0/1) values indicating the selected vertices
  (`[[0,1,0,..]]`).  Otherwise it will expect a list of Edges
  (`[[2,6],[3,4]...]`).
- **Amount**. Amount to offset beveled edge.
- **Segments**. Number of segments in bevel.
- **Profile**. Profile shape.
- **Spread**. Controls how far the new vertices are from the meeting point.
  This input is visible only when one of **Miter Type** parameters is set to
  value different from **Sharp**. The default value is 0.0.

Parameters
----------

This node has the following parameters:

+-------------------+---------------+-------------+----------------------------------------------------+
| Parameter         | Type          | Default     | Description                                        |
+===================+===============+=============+====================================================+
| **Amount type**   | Offset or     | Offset      | * Offset - Amount is offset of new edges from      |
|                   |               |             |                                                    |
|                   |               |             |   original.                                        |
|                   |               |             |                                                    |
|                   | Width or      |             | * Width - Amount is width of new face.             |
|                   |               |             |                                                    |
|                   | Depth or      |             | * Depth - Amount is perpendicular distance from    |
|                   |               |             |                                                    |
|                   |               |             |   original edge to bevel face.                     |
|                   |               |             |                                                    |
|                   | Percent       |             | * Percent - Amount is percent of adjacent edge     |
|                   |               |             |                                                    |
|                   |               |             |   length.                                          |
+-------------------+---------------+-------------+----------------------------------------------------+
| **Vertex mode**   | Boolean       | False       | Bevel edges or only vertex. When activated the mask|
|                   |               |             |                                                    |
|                   |               |             | will switch from 'Bevel Edges' to 'MaskVertices'   |
+-------------------+---------------+-------------+----------------------------------------------------+
| **Clamp Overlap** | Boolean       | False       | If checked, do not allow beveled edges/vertices to |
|                   |               |             |                                                    |
|                   |               |             | overlap each other                                 |
+-------------------+---------------+-------------+----------------------------------------------------+
| **Amount**        | Float         | 0.0         | Amount to offset beveled edge. Exact               |
|                   |               |             |                                                    |
|                   |               |             | interpretation of this parameter depends on        |
|                   |               |             |                                                    |
|                   |               |             | ``Amount type`` parameter. Default value of zero   |
|                   |               |             |                                                    |
|                   |               |             | means do not bevel. This parameter can also be     |
|                   |               |             |                                                    |
|                   |               |             | specified via corresponding input.                 |
+-------------------+---------------+-------------+----------------------------------------------------+
| **Segments**      | Int           | 1           | Number of segments in bevel. This parameter can    |
|                   |               |             |                                                    |
|                   |               |             | also be specified via corresponding input.         |
+-------------------+---------------+-------------+----------------------------------------------------+
| **Profile**       | Float         | 0.5         | Profile shape - a float number from 0 to 1;        |
|                   |               |             |                                                    |
|                   |               |             | default value of 0.5 means round shape.  This      |
|                   |               |             |                                                    |
|                   |               |             | parameter can also be specified via corresponding  |
|                   |               |             |                                                    |
|                   |               |             | input.                                             |
+-------------------+---------------+-------------+----------------------------------------------------+
| **Spread**        | Float         | 0.0         | See corresponding input description above.         |
+-------------------+---------------+-------------+----------------------------------------------------+
| **Loop Slide**    | Boolean       | True        | If checked, prefer to slide along edges to having  |
|                   |               |             |                                                    |
|                   |               |             | even widths. This parameter is available in the    |
|                   |               |             |                                                    |
|                   |               |             | N panel only.                                      |
+-------------------+---------------+-------------+----------------------------------------------------+
| **Miter type** /  | Sharp or      | Sharp       | Inner miter type. See Blender documentation for    |
|                   |               |             |                                                    |
| **Inner**         | Patch or      |             | the details. This parameter is available in the N  |
|                   |               |             |                                                    |
|                   | Arc           |             | panel only.                                        |
+-------------------+---------------+-------------+----------------------------------------------------+
| **Miter type** /  | Sharp or      | Sharp       | Outer miter type. See Blender documentation for    |
|                   |               |             |                                                    |
| **Outer**         | Patch or      |             | the details. This parameter is available in the N  |
|                   |               |             |                                                    |
|                   | Arc           |             | panel only.                                        |
+-------------------+---------------+-------------+----------------------------------------------------+

`Bevel Bevel Modifier Documentation <https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/bevel.html>`_

Profile
-------

.. image:: https://user-images.githubusercontent.com/14288520/197985396-d661c052-4678-440a-819a-4758f1b627d9.png
  :target: https://user-images.githubusercontent.com/14288520/197985396-d661c052-4678-440a-819a-4758f1b627d9.png

Spread
------

.. image:: https://user-images.githubusercontent.com/14288520/197967980-f01b33bc-8cb1-462c-a65b-2f68e83858dd.png
  :target: https://user-images.githubusercontent.com/14288520/197967980-f01b33bc-8cb1-462c-a65b-2f68e83858dd.png

Loop Slide
----------

.. image:: https://user-images.githubusercontent.com/14288520/197971748-568283ee-5834-491d-a909-79afb8947a87.gif
  :target: https://user-images.githubusercontent.com/14288520/197971748-568283ee-5834-491d-a909-79afb8947a87.gif

Miter type
----------

.. image:: https://user-images.githubusercontent.com/14288520/197964779-a9439e7d-d0ae-47a8-8717-af82660a445a.png
  :target: https://user-images.githubusercontent.com/14288520/197964779-a9439e7d-d0ae-47a8-8717-af82660a445a.png

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Polygons**
- **FaceData**. List containing data items from the **FaceData** input, which
  contains one item for each output mesh face.
- **NewPolys** - only bevel faces.

Examples of usage
-----------------

Beveled cube:

.. image:: https://user-images.githubusercontent.com/14288520/198134853-c65d807f-586b-4d63-b42a-e830fa9ba7b0.png
  :target: https://user-images.githubusercontent.com/14288520/198134853-c65d807f-586b-4d63-b42a-e830fa9ba7b0.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Only three edges of cube beveled:

.. image:: https://user-images.githubusercontent.com/14288520/198137479-17935dcc-d2f6-4a0f-8cef-f6a5cecb0e8a.png
  :target: https://user-images.githubusercontent.com/14288520/198137479-17935dcc-d2f6-4a0f-8cef-f6a5cecb0e8a.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List-> :doc:`Index To Mask </nodes/list_masks/index_to_mask>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

---------

Another sort of cage:

.. image:: https://user-images.githubusercontent.com/14288520/198138428-54d3a271-f363-4e6a-9f9b-277af95faa41.png
  :target: https://user-images.githubusercontent.com/14288520/198138428-54d3a271-f363-4e6a-9f9b-277af95faa41.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

See also:

* CAD-> :doc:`Offset </nodes/modifier_change/offset>` (Outpols)

---------

You can work with multiple objects:

.. image:: https://user-images.githubusercontent.com/14288520/198144631-e56529ea-e679-4b45-b0be-35dfad4358f4.png
  :target: https://user-images.githubusercontent.com/14288520/198144631-e56529ea-e679-4b45-b0be-35dfad4358f4.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Vertex mode and multiple radius:

.. image:: https://user-images.githubusercontent.com/14288520/198154647-36db9675-c302-498c-ba80-f9405682de69.png
  :target: https://user-images.githubusercontent.com/14288520/198154647-36db9675-c302-498c-ba80-f9405682de69.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator->Generators Extended-> :doc:`Triangle </nodes/generators_extended/triangle>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

An example of "FaceData" sockets usage:

.. image:: https://user-images.githubusercontent.com/284644/70852164-0682a200-1ec0-11ea-8b65-75b0bced3659.png
  :target: https://user-images.githubusercontent.com/284644/70852164-0682a200-1ec0-11ea-8b65-75b0bced3659.png

