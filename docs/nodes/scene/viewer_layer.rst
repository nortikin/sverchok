Viewer Layer
============

Functionality
-------------

This node helps you manage multiple viewer nodes in a centralized way.

It allows you to create multiple layers (groups) to which you can add any of the supported viewer nodes [1] available in the node tree. Once the viewer nodes are added to the ViewerLayer node you can change their attributes (ON/OFF status, vert/edge/face display status and colors etc) directly from within the ViewerLayer node without having to navigate to each viewer node in the node tree to adjust those settings. Additionally, the ViewerLayer node also allows for various operations to be applied to all layers or all viewers in a layer at once (e.g. hide/show all, turn ON/OFF vert/edge/face display for all, collapse viewers in a layer or collapse all layers).

Notes:
[1] : Currently the supported viewer nodes are the "Viewer Draw" and the "Viewer Index" nodes.

One usefulness of this node is that you can group together various viewer nodes that belong together in rendering some information in the viewport and you can easily turn ON/OFF all those viewers at once with miminal interaction (sometimes with just one click).


Node Operations
---------------
The node level operations that apply to all layers in the node are:
* Collapse/Expand all layers (via mix-status toggle button)
* Turn ON/OFF vert/edge/face display (via corresponding mix-status toggle buttons)
* Turn ON/OFF visibility of layers/viewers (via corresponding mix-status toggle buttons)
* Add Layer to node (via "Add Layer" (plus list) button at the bottom of the node)


Layer Operations
----------------
The layer level operations that apply to all viewers in the layer are:
* Remove Layer from node (via "Remove Layer" (minus) button following the layer name)
* Rename Layer (layers are allowed to have same name)
* Collapse/Expand Layer (via "Expand" button in front of the layer name)
* Turn ON/OFF (visibility status) of all viewers in Layer
* Add Viewer to Layer (via "Add Viewer" (plus) button at the bottom of the layer)

Notes:
- There are no limitations on the number of layers a ViewerLayer node can create.
- Once a layer is created, a "Add Viewer" (plus) button is shown at the bottom of the layer to allow viewer entries to be created for each layer. Once the number of viewer entries is the same as the number of available viewer nodes in the node tree, the "Add Viewer" button is hidden.


Viewer Operations
-----------------
The viewer level operations that apply to each viewer in the layer are:
* Remove Viewer (via "Remove Viewer" (minus) button next to the viewer entry)
* Select Viewer (from drop down of avaialable viewer nodes)
* Update ON/OFF status and vert/edge/face display status and colors (via corresponding UI)

Notes:
- The "Remove Viewer" button is only displayed when the viewer entry is empty.
- The viewer selection options (viewer name drop down list) of a viewer entry is the list of the names of all the available viewer nodes in the node tree, excluding the viewer nodes already added to the layer. This is to ensure no duplicate viewers are added to a layer, and also to facilitate selection by providing a shorter list with only those viewers that have not yet been selected yet for a layer.


ON, OFF and MIX status
----------------------
When the layers in the node or the viewers in a layer have an ON status, the corresponding ON/OFF toggle button will show the "Eye Open" icon, indicating the overall status of its descendants. Tapping on the toggle button will turn all its descendants status to OFF.

When the layers in the node or the viewers in a layer have an OFF status, the ON/OFF toggle button will show the "Eye Close" icon indicating the overall status of its descendants. Tapping on the toggle button will turn all its descendants status to ON.

When the layers in the node or the viewers in a layer have a MIX (ON and OFF) status, the ON/OF toggle button  will show a "Dot" icon, indicating the overall status of its descendants (layers or viewers). Tapping on the toggle button will turn all its descendants status to ON.

Note: If a parent level (node or layer) has a MIX status and you want to turn all descendants OFF, you need to tap the ON/OFF toggle button twice: once to turn all ON and second to turn all OFF.

Similar ON/OFF/MIX behavior holds true for the for the vert/edge/face display toggle buttons, except that the icons stays the same (vert/edge/face icon).


Renaming viewer nodes externally
--------------------------------
When a viewer node is renamed externally the ViewerLayer node will capture the name change and will invalidate all the viewer entries in all layers that reference the older names (those entries will be highlighted in RED, assuming the default Blender color theme). In this case you can either chose to remove that viewer entry from the layers or reselect a new viewer for those entries from the latest list of viewers.

Note: Once SV provides a feature to have a fixed, unique ID assigned to every node created (and saved with the blend file), which could be used as a reference, instead of the viewer nodes name, the ViewerLayer node would be able to capture the external changes to the viewer node names and automatically update the names in the layer entries without needing to invalidate viewer entries. Until then, the manual removal / update of the invalidated viewer entries is necessary. So, keep this in mind when you change the viewer node names externally. For this reason it's best to rename the viewer nodes before adding them to the ViewerLayer nodes, and then resist the temptation to change their names. :)


Extra Viewer settings
---------------------
Based on the width of the ViewerLayer node additional settings for the viewers are shown/hidden. For narrow width, the viewer name and visibility toggle button are shown. For larger (>300px) width the vert/edge/face colors are also shown. And for even larger width (>400px) the vert/edge/face display status toggle buttons are also shown.



