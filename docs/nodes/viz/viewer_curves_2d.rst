Viewer curves 2d
================

Functionality
-------------

Making 2d curves from edges inside blender

Inputs
------

- **vertices**. Line vertices
- **edges**. Line edges
- **Matrix**. Matrix for object placement in scene

Parameters & Features 
--------------------- 

+-------------+-----------------------------------------------------------------------------------+
| Feature     | info                                                                              |
+=============+===================================================================================+
| UPD         | Ability to update objects                                                         |
+-------------+-----------------------------------------------------------------------------------+
| eye/sel/rnd | show/hide, selectable/nope, render/nope object in scene                           |
+-------------+-----------------------------------------------------------------------------------+
| Group       | Group object in scene r not                                                       |
+-------------+-----------------------------------------------------------------------------------+
| M/D/U       | Merge object/duplicate same for matrices or make unique every object              |
+-------------+-----------------------------------------------------------------------------------+
| Name        | Name of object in scene. When rename it will leave old named objects in scene     |
|             | also, when inserting new viewer it automatically choose new name                  |
+-------------+-----------------------------------------------------------------------------------+
| Select      | You can select/deselect objects in scene                                          |
+-------------+-----------------------------------------------------------------------------------+
| Material    | Choose material for node's objects                                                |
+-------------+-----------------------------------------------------------------------------------+
| depth radius| Radius for your curve, default 0.2                                                |
+-------------+-----------------------------------------------------------------------------------+
| Sresolution | Surface resolution (0 - square section), default 3                                |
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


