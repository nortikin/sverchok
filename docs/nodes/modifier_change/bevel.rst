Bevel
=====

.. image:: https://github.com/user-attachments/assets/90a21d18-8f0d-4f7a-9f4e-e0e1ec1db1e2
  :target: https://github.com/user-attachments/assets/90a21d18-8f0d-4f7a-9f4e-e0e1ec1db1e2

Functionality
-------------

This node applies Bevel operator to the input mesh with multilevel. You can specify vertices or edges to be beveled.

.. image:: https://github.com/user-attachments/assets/8b8b053f-bb0d-44d0-a498-051b8cab96ed
  :target: https://github.com/user-attachments/assets/8b8b053f-bb0d-44d0-a498-051b8cab96ed

As **multibevel**
-----------------

One can assign bevel size on every vertex separately:

.. image:: https://github.com/user-attachments/assets/d88a0f2f-78a5-48cf-9ec1-0b82501cb794
  :target: https://github.com/user-attachments/assets/d88a0f2f-78a5-48cf-9ec1-0b82501cb794

.. raw:: html

    <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/1d043328-31f5-4cc2-9f71-54a21535fa2d" type="video/mp4">
    Your browser does not support the video tag.
    </video>

`BevelMK2.example.004.06.multibevel.blend.zip <https://github.com/user-attachments/files/20104204/BevelMK2.example.004.06.multibevel.blend.zip>`_

Inputs
------

This node has the following inputs:

- **Vertices**, **Edges**, **Polygons** - Source mesh to bevel.
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.
- **BevelFaceData**. Face data to be assigned to bevel faces. This input is
  expected to contain one item per input objects. If this input is not
  connected, then bevel faces will be assigned with face data from adjacent
  faces. It is a **multibevel** property!
- **BevelEdges / VerticesMask**.  Edges or vertices to be beveled. If this
  input is not connected, then by default all will be beveled. This parameter
  changes when ``Vertex mode`` flag is modified.  On vertex mode it will expect
  a list of True/False (or 0/1) values indicating the selected vertices
  (`[[0,1,0,..]]`).  Otherwise it will expect a list of Edges
  (`[[2,6],[3,4]...]`).
- **Masks elements mode** (boolean, indexes). - What a method you can use to select elements [[0,0,1,1,0],[1,0,0,0,0],...] or [[1,2], [6,3,8], ...]. You can set indexes as sublists for every object. Ex.:

    [
      [[9,7], [6,3,8],], - first object. [9,7] - indexes of first layer, [6,10] - indexes of second layer

      [[1],[7,3],] - second object. [1] - indexes of first layer, [7,3] - indexes of second layer
      
    ]

    .. image:: https://github.com/user-attachments/assets/eab81c21-29ef-4766-af34-cc8102c4bccf
      :target: https://github.com/user-attachments/assets/eab81c21-29ef-4766-af34-cc8102c4bccf

    If edges or vertices selected are not connected then all vertices or edges will be beveled.

- **Offset mode** One bevel for all vertices **per object** or use a number **per every layer** of **Masks elements mode**.
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

---------

Examples of usage
-----------------

Update node
-----------

.. image:: https://github.com/user-attachments/assets/774e8660-8e48-4603-8e90-9d2ed142cdab
  :target: https://github.com/user-attachments/assets/774e8660-8e48-4603-8e90-9d2ed142cdab

`Bevel.Example.006.blend.zip <https://github.com/user-attachments/files/20140784/Bevel.Example.006.blend.zip>`_

Beveled cube
------------

.. image:: https://user-images.githubusercontent.com/14288520/198134853-c65d807f-586b-4d63-b42a-e830fa9ba7b0.png
  :target: https://user-images.githubusercontent.com/14288520/198134853-c65d807f-586b-4d63-b42a-e830fa9ba7b0.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Only three edges of cube beveled
--------------------------------

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

Another sort of cage
--------------------

.. image:: https://user-images.githubusercontent.com/14288520/198138428-54d3a271-f363-4e6a-9f9b-277af95faa41.png
  :target: https://user-images.githubusercontent.com/14288520/198138428-54d3a271-f363-4e6a-9f9b-277af95faa41.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

See also:

* CAD-> :doc:`Offset </nodes/modifier_change/offset>` (Outpols)

---------

You can work with multiple objects in per object mode (one bevel per whole object):

.. image:: https://github.com/user-attachments/assets/eec4dfb7-bc24-4a83-922c-364ce269b66c
  :target: https://github.com/user-attachments/assets/eec4dfb7-bc24-4a83-922c-364ce269b66c

bevel 1 for object 1, bevel 2 for object 2, bevel 3 for object 3, bevel 3 for object 4 (replay last value of bevel)

.. raw:: html

    <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/fd21d13d-c4cd-4198-bd42-42f341a21e05" type="video/mp4">
    Your browser does not support the video tag.
    </video>

`BevelMK2.example.004.Bevel.edges.per.objects.blend.zip <https://github.com/user-attachments/files/20106741/BevelMK2.example.004.Bevel.edges.per.objects.blend.zip>`_

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Generate multiple bevel in one object
-------------------------------------

.. raw:: html

    <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/a95dacfe-2150-441b-8496-1f42cb13afa1" type="video/mp4">
    Your browser does not support the video tag.
    </video>

.. image:: https://github.com/user-attachments/assets/f38c0835-5514-4304-80a1-9648c203f2d4
  :target: https://github.com/user-attachments/assets/f38c0835-5514-4304-80a1-9648c203f2d4

* Number-> :doc:`List Input </nodes/number/list_input>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`
* Script-> :doc:`Formula </nodes/script/formula_mk5>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

`BevelMK2.example.005.multibevel.edges.blend.zip <https://github.com/user-attachments/files/20107471/BevelMK2.example.005.multibevel.edges.blend.zip>`_

---------

Generate bevel in several objects
---------------------------------

.. raw:: html

    <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/cfebf3c2-0e4f-47b9-9f35-7ab11bf4656b" type="video/mp4">
    Your browser does not support the video tag.
    </video>

.. image:: https://github.com/user-attachments/assets/5d2873d4-5870-4ff7-818a-fc50184c7172
  :target: https://github.com/user-attachments/assets/5d2873d4-5870-4ff7-818a-fc50184c7172

* Number-> :doc:`List Input </nodes/number/list_input>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`
* Script-> :doc:`Formula </nodes/script/formula_mk5>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

blend file: `BevelMK2.example.003.multibevel.per.object.blend.zip <https://github.com/user-attachments/files/20048703/BevelMK2.example.003.multibevel.per.object.blend.zip>`_

---------

Vertex mode and multiple radius
-------------------------------

.. image:: https://github.com/user-attachments/assets/b60b94e6-2f84-4484-80ed-de99243f49b2
  :target: https://github.com/user-attachments/assets/b60b94e6-2f84-4484-80ed-de99243f49b2

blend file: `BevelMK2.example.002.bevel.per.object.blend.zip <https://github.com/user-attachments/files/20048755/BevelMK2.example.002.bevel.per.object.blend.zip>`_

---------

An example of "FaceData" sockets usage
--------------------------------------

.. image:: https://user-images.githubusercontent.com/284644/70852164-0682a200-1ec0-11ea-8b65-75b0bced3659.png
  :target: https://user-images.githubusercontent.com/284644/70852164-0682a200-1ec0-11ea-8b65-75b0bced3659.png

