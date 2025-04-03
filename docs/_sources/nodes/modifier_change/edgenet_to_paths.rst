Edgenet to Paths
================

.. image:: https://user-images.githubusercontent.com/14288520/199553487-7964c2ee-af09-49ea-af7c-5d22c9bafc43.png
  :target: https://user-images.githubusercontent.com/14288520/199553487-7964c2ee-af09-49ea-af7c-5d22c9bafc43.png

Functionality
-------------

Splits each edgenet (mesh composed by verts and edges) in paths (sequences of ordered vertices)

.. image:: https://user-images.githubusercontent.com/14288520/199466874-fd5b984b-d52e-43ae-819f-9c762de29451.png
  :target: https://user-images.githubusercontent.com/14288520/199466874-fd5b984b-d52e-43ae-819f-9c762de29451.png

Inputs
------

- **Vertices**
- **Edges**

Outputs
-------

- **Vertices**
- **Edges**
- **Verts indexes**: the indexes of the original vertices in the created paths
- **Edges indexes**: the indexes of the original edges in the created paths
- **Cyclic**: outputs True if the path is a closed path and False if not (only if close loops is activated)

Options
-------

- **Close Loops**: When checked, if the first and last vertices are identical they will merge; otherwise, this wont be checked
- **Join**: If checked, generate one flat list of paths for all input meshes; otherwise, generate separate list of loose parts for each input mesh


Examples of usage
-----------------


.. image:: https://user-images.githubusercontent.com/14288520/199548730-05e2c86a-4b2e-447e-b75e-cf7999f485dc.png
  :target: https://user-images.githubusercontent.com/14288520/199548730-05e2c86a-4b2e-447e-b75e-cf7999f485dc.png

* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Modifiers->Modifier Change-> :doc:`Mask Vertices </nodes/modifier_change/vertices_mask>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Simple:

.. image:: https://user-images.githubusercontent.com/10011941/105373980-83299900-5c07-11eb-94ea-a90c621f4cb7.png
  :target: https://user-images.githubusercontent.com/10011941/105373980-83299900-5c07-11eb-94ea-a90c621f4cb7.png

* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Viz-> :doc:`Polyline Viewer </nodes/viz/polyline_viewer>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/199551669-06d64622-40dd-4438-b66b-40ff3d86e191.png
  :target: https://user-images.githubusercontent.com/14288520/199551669-06d64622-40dd-4438-b66b-40ff3d86e191.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* CAD-> :doc:`Smooth Lines </nodes/generators_extended/smooth_lines>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
