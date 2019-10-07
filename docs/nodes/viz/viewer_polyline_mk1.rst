Polyline viewer
===============

Functionality
-------------

Making 2d/3d curves from vertices series

Inputs
------

- **vertices**. Line vertices
- **Matrix**. Matrix for object placement in scene
- **radii**. Radius for your curve, default 0.2
- **twist**. Rotation of every point of polyline
- **bevel object**. Object as profile for bevel

Parameters & Features 
--------------------- 

+-------------+-----------------------------------------------------------------------------------+
| Feature     | info                                                                              |
+=============+===================================================================================+
| UPD         | Ability to update objects                                                         |
+-------------+-----------------------------------------------------------------------------------+
| eye/sel/rnd | show/hide, selectable/nope, render/nope object in scene                           |
+-------------+-----------------------------------------------------------------------------------+
| Name        | Name of object in scene. When rename it will leave old named objects in scene     |
|             | also, when inserting new viewer it automatically choose new name                  |
+-------------+-----------------------------------------------------------------------------------+
| Select      | You can select/deselect objects in scene                                          |
+-------------+-----------------------------------------------------------------------------------+
| Material    | Choose material for node's objects                                                |
+-------------+-----------------------------------------------------------------------------------+
| 3D/2D       | make polyline 2d or 3d                                                            |
+-------------+-----------------------------------------------------------------------------------+
| radius      | Radius for your curve, default 0.2                                                |
+-------------+-----------------------------------------------------------------------------------+
| subdiv      | Surface resolution (0 - square section), default 3                                |
+-------------+-----------------------------------------------------------------------------------+
| bspline     | Make bspline line with controlling points                                         |
+-------------+-----------------------------------------------------------------------------------+
| close       | Close polyline                                                                    |
+-------------+-----------------------------------------------------------------------------------+
| wire        | Wire representation                                                               |
+-------------+-----------------------------------------------------------------------------------+
| smooth      | Smooth vertices normals                                                           |
+-------------+-----------------------------------------------------------------------------------+
| Multi/Single| Usually many objects, but you can merge them to single                            |
+-------------+-----------------------------------------------------------------------------------+

Parameters extended 
------------------- 

+-------------+-----------------------------------------------------------------------------------+
| Feature     | info                                                                              |
+=============+===================================================================================+
| RND name    | Force to choose random name for objects                                           |
+-------------+-----------------------------------------------------------------------------------+
| +Material   | Make new material for objects                                                     |
+-------------+-----------------------------------------------------------------------------------+



Outputs
-------

- **Objects**, simply new objects


