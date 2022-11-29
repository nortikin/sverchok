Extrude Separate Faces Lite
============================

.. image:: https://user-images.githubusercontent.com/14288520/200075092-219db73c-dfcb-42e0-978e-81be26efffe4.png
  :target: https://user-images.githubusercontent.com/14288520/200075092-219db73c-dfcb-42e0-978e-81be26efffe4.png

Functionality
-------------



Inputs
------

- **Vertices**
- **polygons**
- **Mask**
- **Matrix**

Outputs
-------

- **Vertices**.
- **Edges**.
- **Polygons**.
- **ExtrudedPolys**.
- **OtherPolys**.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/200076128-f16074c5-16e1-419c-a8d4-25043571674f.png
  :target: https://user-images.githubusercontent.com/14288520/200076128-f16074c5-16e1-419c-a8d4-25043571674f.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* List-> :doc:`Index To Mask </nodes/list_masks/index_to_mask>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`