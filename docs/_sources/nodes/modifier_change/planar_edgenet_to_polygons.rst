Planar Edgenet to Polygons
==========================

.. image:: https://user-images.githubusercontent.com/14288520/198831339-af1c6420-50e2-4733-88b1-461cc544085c.png
  :target: https://user-images.githubusercontent.com/14288520/198831339-af1c6420-50e2-4733-88b1-461cc544085c.png

Functionality
-------------

It fills all closed countors of edge net. Be careful edge net have to be planar otherwise work of node will be broken or even you can receive memory error caused of everlasting cycle.

See here, what planar edge net is - https://en.wikipedia.org/wiki/Planar_graph

Some details is here - https://github.com/nortikin/sverchok/issues/86

.. image:: https://user-images.githubusercontent.com/14288520/198832447-a6664361-0cd8-44ee-8e92-58d42efd3ef9.png
  :target: https://user-images.githubusercontent.com/14288520/198832447-a6664361-0cd8-44ee-8e92-58d42efd3ef9.png

Inputs
------

- **Vertices** Only X and Y coords used
- **Edges**

Outputs
-------

- **Vertices**
- **Polygons**. All faces of resulting mesh.

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/14288520/198833226-242b6102-1f35-4927-8310-d44d1078c7e1.png
  :target: https://user-images.githubusercontent.com/14288520/198833226-242b6102-1f35-4927-8310-d44d1078c7e1.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List-> :doc:`Mask Converter </nodes/list_masks/mask_convert>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

---------

Compare with "Fill holes" node:

.. image:: https://user-images.githubusercontent.com/28003269/37105808-8e29b4f2-2249-11e8-9f36-e1da399153fc.png

https://gist.github.com/b0eb16271d33924457e443d74ac3c8d1

Replay with new nodes:

.. image:: https://user-images.githubusercontent.com/14288520/198833958-e1c3989d-be89-4285-b7c7-cf23ee0d93dd.png
  :target: https://user-images.githubusercontent.com/14288520/198833958-e1c3989d-be89-4285-b7c7-cf23ee0d93dd.png


* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Modifiers->Modifier Change-> :doc:`Viewer Index+ </nodes/modifier_change/holes_fill>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List-> :doc:`Mask Converter </nodes/list_masks/mask_convert>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
