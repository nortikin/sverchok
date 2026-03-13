Transform Select
================

.. image:: https://user-images.githubusercontent.com/14288520/191537927-f7fd8f0e-600f-4b4f-93c5-e4341bde9dee.png
  :target: https://user-images.githubusercontent.com/14288520/191537927-f7fd8f0e-600f-4b4f-93c5-e4341bde9dee.png

Functionality
-------------

This node splits the vertex data in two groups, applies one different matrix to each group and joins it again.
It would work as a standard transformation of the selected geometry when working on "Edit Mode".

Inputs
------

This node has the following inputs:

- **Mask**: List of boolean or integer flags. If this input is not connected, a True, False, True.. mask will be created.
- **Verts**: Vertex list.
- **PolyEdge** : It can be Polygon or Edge data.
- **Matrix T** : Matrix applied to the vertex flagged as true.
- **Matrix F** : Matrix applied to the vertex flagged as false.

Parameters
----------

This node has the following parameters:

- **Mask Type**: Specifies if the supplied mask refers to the Vertex data or to the PoleEdge data

Outputs
-------

This node has the following outputs:

- **Vertices**. The whole group of vertices
- **PolyEdge**. A copy of the PolyEdge data supplied
- **PolyEdge O**. PolyEdge data with vertices which are true and false (index referred to "Vertices" output)
- **Vertices T**. Only the vertices marked as true
- **PolyEdge T**. PolyEdge data with vertices which are true (index referred to "Vertices T" output)
- **Vertices F**. Only the vertices marked as false
- **PolyEdge F**. PolyEdge data with vertices which are false (index referred to "Vertices F" output)


See also
--------

* List-> :doc:`List Mask Converter </nodes/list_masks/mask_convert>`

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/14288520/191612450-9969c85e-a42e-4687-adc2-01c31a39b8d2.png
  :target: https://user-images.githubusercontent.com/14288520/191612450-9969c85e-a42e-4687-adc2-01c31a39b8d2.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* Modifiers->Modifier Change-> :doc:`Mesh Join </nodes/modifier_change/mesh_join_mk2>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Logic-> :doc:`Switch </nodes/logic/switch_MK2>`
* Text-> :doc:`Simple Text </nodes/text/simple_text>`
* Text-> :doc:`String Tools </nodes/text/string_tools>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

---------

Showing the different edges groups:

.. image:: https://user-images.githubusercontent.com/14288520/191610452-cc661362-17f3-4b1d-91bb-3e1df0e332d6.png
  :target: https://user-images.githubusercontent.com/14288520/191610452-cc661362-17f3-4b1d-91bb-3e1df0e332d6.png

* Analyzers-> :doc:`Bounding Box </nodes/analyzer/bbox_mk3>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List-> :doc:`Index To Mask </nodes/list_masks/index_to_mask>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`


---------

You can input multiple matrices and they will be paired with the verts:
  
.. image:: https://user-images.githubusercontent.com/14288520/191610875-d24c4088-f8f7-47b0-a5ef-f9b53117ed79.png
  :target: https://user-images.githubusercontent.com/14288520/191610875-d24c4088-f8f7-47b0-a5ef-f9b53117ed79.png

* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* SINE X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`