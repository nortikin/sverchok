Mesh Join
=========

  .. image:: https://github.com/user-attachments/assets/84889e38-c24c-4197-aeb1-fa04224166fb
    :target: https://github.com/user-attachments/assets/84889e38-c24c-4197-aeb1-fa04224166fb

Functionality
-------------

Combines several polygonal mesh objects. Node contains dynamic groups of input sockets Vertices, Edges, Faces and Matrix,
allows you to regroup the input objects, set their order of processing, and manage their position with the help of matrices.
In Join mode, each group’s objects are merged into one mesh with the correct cross-section of edges and borders.

  .. image:: https://github.com/user-attachments/assets/a1a41b45-955d-41ef-b512-ab356503697a
    :target: https://github.com/user-attachments/assets/a1a41b45-955d-41ef-b512-ab356503697a

Options
-------

  .. image:: https://github.com/user-attachments/assets/4222cd70-a219-4539-a032-1d204825ef02
    :target: https://github.com/user-attachments/assets/4222cd70-a219-4539-a032-1d204825ef02

- **Join** - Join Meshes into firts object of the group
- **Apply Matrix** - Apply Matrixes to every object or to every group of objects.

Options in side panel
---------------------

- **Last Group Empty** - If ON Automatically add a bucket group for the new sockets. If Off then last empty socket removed.

If no input socket connected then empty group always exists:

  .. image:: https://github.com/user-attachments/assets/d7080985-9b74-4255-9edc-0c83f3844639
    :target: https://github.com/user-attachments/assets/d7080985-9b74-4255-9edc-0c83f3844639

If some socket of the first group are connected then next empty group created:

  .. image:: https://github.com/user-attachments/assets/6cbd970f-01af-481b-9808-affc1522e494
    :target: https://github.com/user-attachments/assets/6cbd970f-01af-481b-9808-affc1522e494

If some socket of the second group are connected then next empty group created:

  .. image:: https://github.com/user-attachments/assets/7ef96307-9097-4046-8ecb-c5062fbc59c7
    :target: https://github.com/user-attachments/assets/7ef96307-9097-4046-8ecb-c5062fbc59c7

If Last Empty Groupp is OFF then no last group:

  .. image:: https://github.com/user-attachments/assets/9bad7315-7fba-48e9-a03a-736455f16075
    :target: https://github.com/user-attachments/assets/9bad7315-7fba-48e9-a03a-736455f16075

Inputs
------

- **Join Groups** - If connected, you have to specify a combination sequence in the format [[group1, group2],[group3, group0]]. If no sequence is specified, then the object-to-socket connection sequence will be used [[0,1,2,...]]

If Join Groups connected

  .. image:: https://github.com/user-attachments/assets/4e1153c0-9169-42f9-8577-6e4e7e5ecdcc
    :target: https://github.com/user-attachments/assets/4e1153c0-9169-42f9-8577-6e4e7e5ecdcc

If Join Groups is not connected:

  .. image:: https://github.com/user-attachments/assets/3a358ae0-ce41-4b59-8a3b-bffa0c00167a
    :target: https://github.com/user-attachments/assets/3a358ae0-ce41-4b59-8a3b-bffa0c00167a

- **Vertices** N, **Edges**, **Polygons**, **Matrices** - Object group. Numbering groups starts with 0.

  .. image:: https://github.com/user-attachments/assets/16874326-46c5-4ad6-9ad1-9b8def00f1eb
    :target: https://github.com/user-attachments/assets/16874326-46c5-4ad6-9ad1-9b8def00f1eb

Outputs
----------------

The outputs are **Vertices**, **Edges**, **Polygons**, **Matrices**, **Original Ids** and **Ids**.

**Original Ids** is a id of Join Groups socket data:

If Join Groups is not connected:

  .. image:: https://github.com/user-attachments/assets/47e72cb2-786b-42a2-a9f6-74911d585ab7
    :target: https://github.com/user-attachments/assets/47e72cb2-786b-42a2-a9f6-74911d585ab7

If Join Groups is connected (if not object with index then no index in result, skipped):

  .. image:: https://github.com/user-attachments/assets/d0143286-ca98-49e1-a21b-3caba227730f
    :target: https://github.com/user-attachments/assets/d0143286-ca98-49e1-a21b-3caba227730f

Expects a nested collection of vertex lists. Each nested list represents an object which can itself have many vertices and key lists.

See also
--------

* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>` (param Join On/Off)

Examples
--------

Combination of objects
----------------------

  .. image:: https://github.com/user-attachments/assets/36437ec4-7d38-4a3d-ac62-1e966208c63f
    :target: https://github.com/user-attachments/assets/36437ec4-7d38-4a3d-ac62-1e966208c63f

Join Groups
-----------

  .. image:: https://github.com/user-attachments/assets/7ed79182-ae70-4e6c-b364-ac58a4b6c835
    :target: https://github.com/user-attachments/assets/7ed79182-ae70-4e6c-b364-ac58a4b6c835

Old Examples
------------

.. image:: https://user-images.githubusercontent.com/14288520/200021156-1a575bae-42c8-43a8-b95e-5d0c112fb283.png
  :target: https://user-images.githubusercontent.com/14288520/200021156-1a575bae-42c8-43a8-b95e-5d0c112fb283.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/200025633-d89e4b61-e303-4afa-ab2f-0df2c6e21ff9.png
  :target: https://user-images.githubusercontent.com/14288520/200025633-d89e4b61-e303-4afa-ab2f-0df2c6e21ff9.png

* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Notes
-----
