:orphan:

Get Objects Data
================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b24e7fbc-3383-49ca-bc96-ae5ff823fee3
  :target: https://github.com/nortikin/sverchok/assets/14288520/b24e7fbc-3383-49ca-bc96-ae5ff823fee3

Functionality
-------------
Get objects from the Blender ``Scene`` and output them into Sverchok's node tree. This node supports most object types. All are converted to a Sverchok representation of ``Mesh`` where possible. 

A few points worth stating explicitly.

- Empties, Cameras, and Lamps produce only matrix data. 
- The order of the selected Objects can be sorted by name. 
- It supports Object collections.
- It understands also ``vertex groups``, when activated, showing additional socket representing indices, that you can use for further processing. All groups are cached in one list _without_weights_.
- When you ``Get`` objects from the Scene that have modifiers on them, you can import the final mesh by enabling the ``Post`` button.
- Importing Objects with a lot of geometry will decrease Sverchok tree update speed, be careful with any modifiers that produce a lot of extra geometry (like subdivision modifier)
- The Matrix socket lets you ignore or acquire the Object's ``World Matrix``, by default the Object data is untransformed. Use a matrix-apply node if you want to explicitly transform the vertex data.

limitations:

- When you use the ``Post`` mode Sverchok/Blender expect Objects to be visible. If you want to "hide" the original Objects in the scene to avoid visual clutter, you can place them into a Collection and hide the collection. This is a current Blender API limitation.
- We have Bezier-in and NURBS-in nodes if you want to get Curve data from Scene objects, instead of Mesh. 

Inputs
------

Objects Socket


Parameters
----------

+-----------------+---------------+--------------------------------------------------------------------------+
| Param           | Type          | Description                                                              |
+=================+===============+==========================================================================+
| **G E T**       | Button        | Button to get selected objects from scene.                               |
+-----------------+---------------+--------------------------------------------------------------------------+
| **sorting**     | Bool, toggle  | Sorting inserted objects by name                                         |
+-----------------+---------------+--------------------------------------------------------------------------+
| **post**        | Bool, toggle  | Postprocessing, if activated, modifiers applied to mesh before importing |
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

+------------------+--------------------------------------------------------------------------+
| Output           | Description                                                              |
+==================+==========================================================================+
| Vertices         | Vertices of objects                                                      |
+------------------+--------------------------------------------------------------------------+
| Edges            | Edges of objects                                                         |
+------------------+--------------------------------------------------------------------------+
| Polygons         | Polygons of objects                                                      |
+------------------+--------------------------------------------------------------------------+
| Vertex Normals   | Vertex Normals                                                           |
+------------------+--------------------------------------------------------------------------+
| Material Idx     | Material indexes per object face.                                        |
+------------------+--------------------------------------------------------------------------+
| Polygons Areas   | Polygons of objects.                                                     |
+------------------+--------------------------------------------------------------------------+
| Polygons Centers | Polygons Center of objects.                                              |
+------------------+--------------------------------------------------------------------------+
| Polygons Normal  | Polygons Normal of objects.                                              |
+------------------+--------------------------------------------------------------------------+
| Matrix           | Matrices of objects                                                      |
+------------------+--------------------------------------------------------------------------+
| Vers grouped     | Vertex groups' indices from all vertex groups                            |
+------------------+--------------------------------------------------------------------------+

It can output Numpy arrays of vertices and edges if enabled on N-panel properties (makes node faster)

Examples
--------

.. image:: https://user-images.githubusercontent.com/619340/126961901-4c300e39-6cbe-456f-a132-104f7b3827ca.png

Importing an object with two array modifiers applied and showing indices.
