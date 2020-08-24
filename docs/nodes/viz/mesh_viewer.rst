Mesh viewer
===========

.. image:: https://user-images.githubusercontent.com/28003269/91057173-ec48b880-e637-11ea-9933-b9cef83aac65.png

Functionality
-------------

Similar to ViewerDraw but instead of using OpenGL calls to display geometry this Node *writes* or *updates* Blender Meshes on every geometry update. The bonus is that this geometry is renderable without an extra bake step. We can use Blender's Modifier stack to affect the mesh. The only exception to the modifiers is the Skin Modifier but we aren't entirely sure why, maybe because BMview invalidates the BMesh between updates.

Category
--------

Viz -> Mesh viewer

Inputs
------

- Verts
- Edges
- Faces
- material_idx - material indexes per object face.
- Matrix

Parameters & Features
---------------------

+-------------------+---------------------------------------------------------------------------------------+
| Param             | Description                                                                           |
+===================+=======================================================================================+
| Live              | Processing only happens if *update* is ticked                                         |
+-------------------+---------------------------------------------------------------------------------------+
| Hide View         | Hides current meshes from view                                                        |
+-------------------+---------------------------------------------------------------------------------------+
| Hide Select       | Disables the ability to select these meshes                                           |
+-------------------+---------------------------------------------------------------------------------------+
| Hide Render       | Disables the renderability of these meshes                                            |
+-------------------+---------------------------------------------------------------------------------------+
| Base Name         | Base name for Objects and Meshes made by this node                                    |
+-------------------+---------------------------------------------------------------------------------------+
| Random name       | Generates random name with random letters                                             |
+-------------------+---------------------------------------------------------------------------------------+
| Select            | Select every object in 3dview that was created by this Node                           |
+-------------------+---------------------------------------------------------------------------------------+
| Collection        | Pick collection where to put objects                                                  |
+-------------------+---------------------------------------------------------------------------------------+
| Material Select   | Assign materials to Objects made by this node                                         |
+-------------------+---------------------------------------------------------------------------------------+
| Add material      | It creates new material and assigns to generated objects                              |
+-------------------+---------------------------------------------------------------------------------------+
| Lock origin       | If it disabled then origins of generated objects can be set manually in viewport      |
+-------------------+---------------------------------------------------------------------------------------+
| Merge             | On by default, join all meshes produced by incoming geometry into one                 |
+-------------------+---------------------------------------------------------------------------------------+
| Show edges        | Show edges in viewport                                                                |
+-------------------+---------------------------------------------------------------------------------------+
| Assign matrix to  | Matrix can be assigned either to objects or mesh. It will effect only onto position   |
|                   | of origin. Also if matrix is applying to objects `lock origin` will be always True    |
+-------------------+---------------------------------------------------------------------------------------+
| Fast mesh update  | It tries to update mesh in fast way. It can not update mesh at all in some conner     |
|                   | cases. So it should be disabled                                                       |
+-------------------+---------------------------------------------------------------------------------------+
| Smooth shade      | Automatically sets *shade* type to smooth when ticked.                                |
+-------------------+---------------------------------------------------------------------------------------+
| Show in 3D panel  | Show the properties in 3D panel                      .                                |
+-------------------+---------------------------------------------------------------------------------------+


*Note: Some features are placed in the `N-Panel` / `Properties Panel`.*

Outputs
-------

- Objects

3D panel
--------

The node can show its properties on 3D panel. 
For this parameter `Show in 3D panel` should be enabled.
After that you can press `scan for props` button on 3D panel for showing the node properties on 3D panel.


Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/91072892-4141fa00-e64b-11ea-8f6a-0a59e9c1b61e.png