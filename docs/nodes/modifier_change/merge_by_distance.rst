Merge by Distance
=================

.. image:: https://user-images.githubusercontent.com/14288520/199111364-34353398-2bc8-4d95-a8d5-db937f99fba2.png
  :target: https://user-images.githubusercontent.com/14288520/199111364-34353398-2bc8-4d95-a8d5-db937f99fba2.png

Functionality
-------------

This merges vertices that are closer that a defined threshold, as do same-named command in blender.

Inputs
------

- **Distance**. Remove distance
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
- **Mask** The inputted mask after the merge. (Removed the mask indexes of the deleted vertices)

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/14288520/199113153-05fa7f2d-8ddb-4308-9a9b-ebb20e16f980.png
  :target: https://user-images.githubusercontent.com/14288520/199113153-05fa7f2d-8ddb-4308-9a9b-ebb20e16f980.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List-> :doc:`Index To Mask </nodes/list_masks/index_to_mask>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/199118735-68850597-cf13-439a-a0fa-221d104ce55a.png
  :target: https://user-images.githubusercontent.com/14288520/199118735-68850597-cf13-439a-a0fa-221d104ce55a.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/199118461-f9ce665f-e012-4b72-ba1d-e5c0af6bc165.png
  :target: https://user-images.githubusercontent.com/14288520/199118461-f9ce665f-e012-4b72-ba1d-e5c0af6bc165.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzers-> :doc:`Select Mesh Elements </nodes/analyzer/mesh_select_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/199121377-5085556a-483f-422a-87ed-dea854ac8ec6.png
  :target: https://user-images.githubusercontent.com/14288520/199121377-5085556a-483f-422a-87ed-dea854ac8ec6.png

* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Analyzers-> :doc:`Select Mesh Elements </nodes/analyzer/mesh_select_mk2>`
* Analyzers-> :doc:`Proportional Edit Falloff </nodes/analyzer/proportional>`
* Modifiers->Modifier Change-> :doc:`Smooth Vertices </nodes/modifier_change/smooth>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector Lerp </nodes/vector/lerp>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* NOT: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/199122167-9458221d-5946-443b-9801-095806253764.gif
  :target: https://user-images.githubusercontent.com/14288520/199122167-9458221d-5946-443b-9801-095806253764.gif