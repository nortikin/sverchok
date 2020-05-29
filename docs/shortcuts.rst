*********
Shortcuts
*********

This is a collection of shortcuts useful in the Sverchok node tree, some are Blenders defaults and some are customized for Sverchok use.

**G** - Move selected nodes.

**Shift + A** - Add node menu

**Alt + Space** - Add node search menu

**Shift + D** - Duplicate selected nodes

**Ctrl + Shift + D** - Duplicate selected nodes keeping links

**X** - Delete selected nodes.

**Ctrl + F** - Search existing node menu.

**Home** - View All

**Numpad .** - Frame selected

**F** - Links (connects) the selected nodes from left to right using the first output socket with the first empty input socket.

**V** - Vectors - Edges - Faces connector: the same of the F key but connecting vertices to vertices, edges to edges and faces (or polygons) to faces (or polygons) if possible.

.. image:: https://user-images.githubusercontent.com/10011941/78379176-4508ad80-75d2-11ea-8421-c3cd950bb9f0.gif


**Ctrl + Right Click** - Connects a temporal Stethoscope to the active node. If the node was already connected to it than the connection will move to the next output socket.

.. image:: https://user-images.githubusercontent.com/10011941/78380794-b9dce700-75d4-11ea-8b98-bff3fa9d9446.gif

**Ctrl + Left Click** - Connects a temporal Viewer to the active node. If the node produces visible geometry it will connect a Viewer Draw Node if not a Stethoscope node.

.. image:: https://user-images.githubusercontent.com/10011941/78453089-ceca8080-768f-11ea-8726-d2c2ffaa5cb4.gif

**Ctrl + Shit + Click** -  Connects a temporal Viewer to the active node. If the node produces visible geometry it will connect a Viewer Draw Node if not a Stethoscope node. (Cuts the links first).

.. image:: https://user-images.githubusercontent.com/10011941/78453090-d4c06180-768f-11ea-8631-422fe63f994e.gif

**F5** - Updates current node tree only if node-tree processing is enabled

**Ctrl + F5** - Updates current node tree even if node-tree processing is disabled

**Ctrl + Shift + F5** in 3D View window - Enables/Disables "Live Update" mode

**F6** - Enables/Disables the processing of the current node-tree

**F7** - Enables/Disables the Draft mode of the current node-tree

**Ctrl + G** - Create Monad (Group) and re-link.

**Ctrl + Shift + G** - Create Monad (Group).

**L** - Select Nodes that link to the previously selected nodes

**Shift + L** - Select Nodes that are linked from the previously selected nodes

**Shift + Right Click** - Add Re-route

**Ctrl + Right Click** - Cut Links

**Right Click** - Access to Sverchok Right Click Menu
