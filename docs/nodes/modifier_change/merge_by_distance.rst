Merge by Distance
=================

Functionality
-------------

This merges vertices that are closer that a defined threshold, as do same-named command in blender

Inputs
------

- **Distance**
- **Vertices**
- **PolyEdge**
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.
  - **Mask**. Vector mask to select the affected vertices


Parameters
----------

+-----------+-----------+-----------+-------------------------------------------+
| Param     | Type      | Default   | Description                               |
+===========+===========+===========+===========================================+    
| Distance  | Float     | 0.001     | Maximum distance to weld vertices         |
+-----------+-----------+-----------+-------------------------------------------+

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Polygons**
- **Doubles**. Vertices, that were deleted.
- **FaceData**. List containing data items from the **FaceData** input, which
  contains one item for each output mesh face.
- **Mask** The mask after the merge

Examples of usage
-----------------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/modifier_change/merge_by_distance/sverchok_blender_merge_by_distance_example_01.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/modifier_change/merge_by_distance/sverchok_blender_merge_by_distance_example_02.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/modifier_change/merge_by_distance/sverchok_blender_merge_by_distance_example_03.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/modifier_change/merge_by_distance/sverchok_blender_merge_by_distance_example_04.png
