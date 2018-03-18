Select vertices of mesh Node
==============

Functionality
-------------

This node can select vertices of mesh objects in the scene using different parameters.

Inputs
------

This node has the following inputs:

- **Objects**. Node can work with mesh type objects.
- **Vert_Index**. Select vertices using their indices. Not automaticaly deselect vertices which is not indexed. Use **clear_selection** checkbox.
- **Vert_Mask**. Select and deselect vertices using bool mask.
- **Edges_Polys**. Select verts by feeding in Sverchok edges or polygons lists.
- **Floattoboolexpr**. Use float values and textbox to create bool mask which will be used to select vertices.

Parameters
----------

This node has the following parameters:

- **Clear selections**. Deselect all verts before doing anything.
- **expression text-box**. Visible only when **floattoboolexpr** socket is connected.

Outputs
-------

This node has the following outputs:

- **Selected_Index**. Indices of selected vertices.
- **Selected_Mask**. Bool values represent selected and unselected vertices.
- **Objects**. Same objects as from input objects socket. To control dataflow in nodetree.

**Note**: This node will work only when object is in **Object Mode**. Not working while object is in **Edit Mode**.

Examples of usage
-----------------
.. image:: https://user-images.githubusercontent.com/22656834/37565314-e7a2cc6c-2ac8-11e8-8f5a-2cb4935dcab3.png
