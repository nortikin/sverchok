Select vertices of mesh Node
==============

Functionality
-------------

This node can select vertices of mesh objects in the scene using different parameters.

Inputs
------

This node has the following inputs:

- **Objects**. Node can work with mesh type objects.
- **Element_Index**. Select mesh elements using their indices. Not automaticaly deselect elements which is not indexed. Use **clear_selection** checkbox.
- **Element_Mask**. Select and deselect elements using bool mask.
- **Edges_Polys**. Select verts by feeding in Sverchok edges or polygons lists.
- **Floattoboolexpr**. Use float values and textbox to create bool mask which will be used to select elements.

Parameters
----------

This node has the following parameters:

- **Clear selections**. Deselect all verts, edges and faces before doing anything. If selected vertices formed edge or face shape, then Blender consider it as if edge or face element was selected. So you must have this checkbox activated in most cases when you want to use input selection sockets, but always keep it deactivated if you want to use output selection sockets.
- **Elements Mode**. Chose out of **Verts**, **Polygons** or **Edges** as elements to be selected.
- **expression text-box**. Visible only when **floattoboolexpr** socket is connected.

Outputs
-------

This node has the following outputs:

- **Selected_Index**. Indices of selected elements.
- **Selected_Mask**. Bool values represent selected and unselected elements.
- **Objects**. Same objects as from input objects socket. To control dataflow in nodetree.

**Note**: This node will work only when object is in **Object Mode**. Not working while object is in **Edit Mode**.

Examples of usage
-----------------
.. image:: https://user-images.githubusercontent.com/22656834/37565314-e7a2cc6c-2ac8-11e8-8f5a-2cb4935dcab3.png
