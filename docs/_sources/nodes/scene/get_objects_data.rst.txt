Get Objects Data
================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d2b29188-e471-4821-80fa-ea0da9e8403e
  :target: https://github.com/nortikin/sverchok/assets/14288520/d2b29188-e471-4821-80fa-ea0da9e8403e

Functionality
-------------
Get objects from the Blender ``Scene`` and output them into Sverchok's node tree. This node supports most object types. All are converted to a Sverchok representation of ``Mesh`` where possible.
Sockets for the selected mesh elements or creases on weights can be used for quck masking.

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
- Another method to work with objects - select wireframe mode and hide objects in Render by buttons:

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/30158800-3cd8-483d-a162-2d13ddfdc289
    :target: https://github.com/nortikin/sverchok/assets/14288520/30158800-3cd8-483d-a162-2d13ddfdc289

.. raw:: html

   <video width="700" controls>
     <source src="https://github.com/nortikin/sverchok/assets/14288520/7a158c33-814a-43be-9a9c-929096495354" type="video/mp4">
    Your browser does not support the video tag.
   </video>

- We have Bezier-in and NURBS-in nodes if you want to get Curve data from Scene objects, instead of Mesh. 

Inputs
------

Objects Socket


Parameters
----------

+----------------------+---------------+--------------------------------------------------------------------------+
| Param                | Type          | Description                                                              |
+======================+===============+==========================================================================+
| **G E T**            | Button        | Button to get selected objects from scene.                               |
+----------------------+---------------+--------------------------------------------------------------------------+
| **Apply_Matrix**     | Bool,toggle   | Apply object Matrix to output sockets (Vertices, Vertex Normals,         |
|                      |               | Poligon Centers, Polygon Normals). Has no infuence for Matrix and Object |
+----------------------+---------------+--------------------------------------------------------------------------+
| **Merge**            | Bool,toggle   | Merge Meshes into one mesh                                               |
+----------------------+---------------+--------------------------------------------------------------------------+
| **sorting**          | Bool,toggle   | Sorting inserted objects by name                                         |
+----------------------+---------------+--------------------------------------------------------------------------+
| **post**             | Bool,toggle   | Postprocessing, if activated, modifiers applied to mesh before importing |
+----------------------+---------------+--------------------------------------------------------------------------+
| **vert groups**      | Bool,toggle   | Import all vertex groups that in object's data. just import indexes      |
+----------------------+---------------+--------------------------------------------------------------------------+

3D panel
--------

The node can show its properties on 3D panel.
For this parameter `to 3d` should be enabled, output should be linked.
After that you can press `scan for props` button on 3D panel for showing the node properties on 3D panel.

Outputs
-------

+-----------------------+--------------------------------------------------------------------------+
| Output                | Description                                                              |
+=======================+==========================================================================+
| Vertices              | Vertices of objects                                                      |
+-----------------------+--------------------------------------------------------------------------+
| Edges                 | Edges of objects                                                         |
+-----------------------+--------------------------------------------------------------------------+
| Polygons              | Polygons of objects                                                      |
+-----------------------+--------------------------------------------------------------------------+
| Vertices Select       | Mask of vertices selected in the edit mode                               |
+-----------------------+--------------------------------------------------------------------------+
| Vertices Crease       | Vertices crease values                                                   |
+-----------------------+--------------------------------------------------------------------------+
| Vertices Bevel Weight | Vertices Bevel Weight values                                             |
+-----------------------+--------------------------------------------------------------------------+
| Edges Select          | Mask of Edges selected in the edit mode                                  |
+-----------------------+--------------------------------------------------------------------------+
| Edges Crease          | Edges crease values                                                      |
+-----------------------+--------------------------------------------------------------------------+
| Edges Seam            | Edges seam values                                                        |
+-----------------------+--------------------------------------------------------------------------+
| Edges Sharp           | Edges sharp values                                                       |
+-----------------------+--------------------------------------------------------------------------+
| Edges Bevel Weight    | Edges Bevel Weight values                                                |
+-----------------------+--------------------------------------------------------------------------+
| Polygon Selected      | Mask of Polygons selected in the edit mode                               |
+-----------------------+--------------------------------------------------------------------------+
| Polygon Smooth        | Smooth of Polygons                                                       |
+-----------------------+--------------------------------------------------------------------------+
| Vertex Normals        | Vertex Normals                                                           |
+-----------------------+--------------------------------------------------------------------------+
| Material Idx          | Material indexes per object face.                                        |
+-----------------------+--------------------------------------------------------------------------+
| Polygons Areas        | Area of Polygons of objects.                                             |
+-----------------------+--------------------------------------------------------------------------+
| Polygons Centers      | Polygons Center of objects.                                              |
+-----------------------+--------------------------------------------------------------------------+
| Polygons Normal       | Polygons Normal of objects.                                              |
+-----------------------+--------------------------------------------------------------------------+
| Matrix                | Matrices of objects                                                      |
+-----------------------+--------------------------------------------------------------------------+
| Vers grouped          | Vertex groups' indices from all vertex groups                            |
+-----------------------+--------------------------------------------------------------------------+

It can output Numpy arrays of vertices and edges if enabled on N-panel properties (makes node faster)

Examples
--------

.. image:: https://user-images.githubusercontent.com/619340/126961901-4c300e39-6cbe-456f-a132-104f7b3827ca.png

Importing an object with two array modifiers applied and showing indices.

Mask sites of Voronoi node with selection of faces:

.. raw:: html

   <video width="700" controls>
     <source src="https://github.com/nortikin/sverchok/assets/14288520/e08f226e-f13b-4fff-bdb1-aa4db06ac0a6" type="video/mp4">
    Your browser does not support the video tag.
   </video>

* Spatial-> :doc:`Voronoi on Mesh </nodes/spatial/voronoi_on_mesh>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Mask edges of Grid with selection of edges:

.. raw:: html

   <video width="700" controls>
     <source src="https://github.com/nortikin/sverchok/assets/14288520/280c72f7-8b51-44cc-9e63-75c9a97f5739" type="video/mp4">
    Your browser does not support the video tag.
   </video>

* Modifiers->Modifier Change-> :doc:`Extrude Edges </nodes/modifier_change/extrude_edges_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`