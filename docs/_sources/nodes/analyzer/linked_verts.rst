Linked Verts
============

.. image:: https://user-images.githubusercontent.com/14288520/197250471-debee68f-310e-4a7e-9675-96bc6e827f0a.png
  :target: https://user-images.githubusercontent.com/14288520/197250471-debee68f-310e-4a7e-9675-96bc6e827f0a.png

Functionality
-------------

Linked Verts node is one of the analyzer type. It is used  to get the vertices that are connected to a vertex. It can also get the vertices that are separated by N edges allowing the creation of complex selection patterns.

Inputs
------

- **Vertices**: Vertex list (optional).
- **Edge_Pol**: Edge or Polygon data.
- **Selection**: Desired index list or mask list.
- **Distance**: Distance to input (measured in number of edges/polygons in between).

Parameters
----------

**Selection Type**: choose if you input a index list or a mask list in the **Selection** input


Outputs
-------

- **Verts Id**: Index of the linked vertices, referring to the **Vertices** input list.
- **Verts**: Linked verts list.
- **Mask**: mask of the linked vertices, referring to the **Vertices** input list.

Linked Verts by index:

.. image:: https://user-images.githubusercontent.com/14288520/197256974-fd154900-91e1-4f09-8137-053d4f95204e.png
  :target: https://user-images.githubusercontent.com/14288520/197256974-fd154900-91e1-4f09-8137-053d4f95204e.png

---------

.. image:: https://user-images.githubusercontent.com/14288520/197257643-c6605b4f-3c3f-4b78-ab55-b95166ba459c.png
  :target: https://user-images.githubusercontent.com/14288520/197257643-c6605b4f-3c3f-4b78-ab55-b95166ba459c.png

---------

Linked Verts by Mask:

.. image:: https://user-images.githubusercontent.com/14288520/197260740-aa447ff4-00c9-43ce-901e-92c9dab6cc7f.png
  :target: https://user-images.githubusercontent.com/14288520/197260740-aa447ff4-00c9-43ce-901e-92c9dab6cc7f.png

Example of usage
----------------

In this example you get the white vertex when asking for the vertex that are connected to the green dot.

.. image:: https://user-images.githubusercontent.com/14288520/197261597-4046ec57-cc29-4319-ab42-8801067450e7.png
  :target: https://user-images.githubusercontent.com/14288520/197261597-4046ec57-cc29-4319-ab42-8801067450e7.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Using a range of integers as Distance input will expand the selection or the creation of patterns.

.. image:: https://user-images.githubusercontent.com/14288520/197262608-7ed093ed-3aff-44e8-93b3-a4202f70b702.png
  :target: https://user-images.githubusercontent.com/14288520/197262608-7ed093ed-3aff-44e8-93b3-a4202f70b702.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/197264661-f8325b67-59c0-43c7-b6e1-3bf0a9455a46.png
  :target: https://user-images.githubusercontent.com/14288520/197264661-f8325b67-59c0-43c7-b6e1-3bf0a9455a46.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* List->List Struct-> :doc:`List Item Insert </nodes/list_struct/item_insert>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/197265589-6c2e1976-7e47-42a3-b95d-a9e0a802a692.png
  :target: https://user-images.githubusercontent.com/14288520/197265589-6c2e1976-7e47-42a3-b95d-a9e0a802a692.png

* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/197267040-8d782eb2-457b-4418-9a24-6b3842b73ccc.gif
  :target: https://user-images.githubusercontent.com/14288520/197267040-8d782eb2-457b-4418-9a24-6b3842b73ccc.gif