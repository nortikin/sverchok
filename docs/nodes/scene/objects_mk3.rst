Object In
=========

Functionality
-------------
Takes object from scene to sverchok. Support meshed, empties, curves, NURBS, but all converting to mesh. Empties has only matrix data. Than sorting by name. If you write group of objects to group field, all object in signed group will be imported. It understands also vertes groups, when activated, showing additional socket representing indexes, that you can use to sort or mask edges/polygons. or do any you want with vertex groups. All groups cached in one list, but without weight.

Inputs
------

None


Parameters
----------

+-----------------+---------------+--------------------------------------------------------------------------+
| Param           | Type          | Description                                                              |  
+=================+===============+==========================================================================+
| **G E T**       | Button        | Button to get selected objects from scene.                               | 
+-----------------+---------------+--------------------------------------------------------------------------+
| **group**       | String        | Name of group to import every object from group to Sverchok              |  
+-----------------+---------------+--------------------------------------------------------------------------+
| **sorting**     | Bool, toggle  | Sorting inserted objects by name                                         | 
+-----------------+---------------+--------------------------------------------------------------------------+
| **post**        | Bool, toggle  | Postprocessing, if activated, modifiers applyed to mesh before importing |
+-----------------+---------------+--------------------------------------------------------------------------+
| **vert groups** | Bool, toggle  | Import all vertex groups that in object's data. just import indexes      |
+-----------------+---------------+--------------------------------------------------------------------------+

3D panel
--------

The node can show its properties on 3D panel. 
For this parameter `to 3d` should be enabled, output should be linked.
After that you can press `scan for props` button on 3D panel for showing the node properties on 3D panel.

Outputs
-------

+-----------------+--------------------------------------------------------------------------+
| Output          | Description                                                              |
+=================+==========================================================================+
| Vertices        | Vertices of objects                                                      | 
+-----------------+--------------------------------------------------------------------------+
| Edges           | Edges of objects                                                         |
+-----------------+--------------------------------------------------------------------------+
| Polygons        | Polygons of objects                                                      |
+-----------------+--------------------------------------------------------------------------+
| MaterialIdx     | Material indexes per object face.                                        |
+-----------------+--------------------------------------------------------------------------+
| Matrixes        | Matrices of objects                                                      |
+-----------------+--------------------------------------------------------------------------+
| _Vers_grouped_  | Vertex groups' indeces from all vertex groups                            |
+-----------------+--------------------------------------------------------------------------+

Examples
--------
.. image:: https://cloud.githubusercontent.com/assets/5783432/4328096/bd8b274e-3f80-11e4-8582-6b2ae9743431.png

Importing cobe and look to indeces.
