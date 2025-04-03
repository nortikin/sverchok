Mesh Viewer
===========

.. image:: https://user-images.githubusercontent.com/14288520/190240580-873e87cf-17e4-4e19-9e49-2ca4e02b8a6d.png
  :target: https://user-images.githubusercontent.com/14288520/190240580-873e87cf-17e4-4e19-9e49-2ca4e02b8a6d.png

.. image:: https://user-images.githubusercontent.com/14288520/190859387-573095d4-9731-4e81-82b2-94f1d9c63a3b.png
  :target: https://user-images.githubusercontent.com/14288520/190859387-573095d4-9731-4e81-82b2-94f1d9c63a3b.png

* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`

Functionality
-------------


Similar to (Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`) but instead of using OpenGL calls to display geometry this Node *writes* or *updates* Blender Meshes on every geometry update. The bonus is that this geometry is renderable without an extra bake step. We can use Blender's Modifier stack to affect the mesh. The only exception to the modifiers is the Skin Modifier but we aren't entirely sure why, maybe because BMview invalidates the BMesh between updates.

*Note:* The performance of the node can be increased significantly by putting vertices in `numpy.float32` format
in case if topology of the mesh remains unchanged.

Category
--------

Viz -> Mesh Viewer

Inputs
------

- Verts
- Edges
- Faces
- material_idx - material indexes per object face.
- Matrix

Parameters & Features
---------------------

+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Param                             | Description                                                                                                             |
+===================================+=========================================================================================================================+
| Live                              | Processing only happens if *update* is ticked                                                                           |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Show/Hide objects in viewport     | Hides current meshes from view                                                                                          |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Make objects selectable           | Disables the ability to select these meshes                                                                             |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Show/Hide objects for render      | Disables the renderability of these meshes                                                                              |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Mesh Name                         | Base name for Objects and Meshes made by this node                                                                      |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Random name generator             | Generates random name with random letters                                                                               |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Select generated objects          | Select every object in 3dview that was created by this Node                                                             |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Collection's name                 | Pick collection where to put objects                                                                                    |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Material                          | Assign materials to Objects made by this node                                                                           |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Create new material               | It creates new material and assigns to generated objects                                                                |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Origin                            | If it disabled then origins of generated objects can be set manually                                                    |
|                                   |                                                                                                                         |
|                                   | in viewport                                                                                                             |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Merge                             | On by default, join all meshes produced by incoming geometry                                                            |
|                                   |                                                                                                                         |
|                                   | into one                                                                                                                |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Show edges                        | Show edges in viewport                                                                                                  |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Apply matrices to                 | Matrix can be assigned either to objects or mesh. It will effect only                                                   |
|                                   |                                                                                                                         |
|                                   | onto position of origin. Also if matrix is applying to objects                                                          |
|                                   |                                                                                                                         |
|                                   | `lock origin` will be always True                                                                                       |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Fast mesh update                  | It tries to update mesh in fast way. It can not update mesh at all in                                                   |
|                                   |                                                                                                                         |
|                                   | some conner cases. So it should be disabled                                                                             |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| Smooth shade                      | Automatically sets *shade* type to smooth when ticked.                                                                  |
|                                   |                                                                                                                         |
|                                   | .. image:: https://user-images.githubusercontent.com/14288520/190247399-6bf5b088-7245-4cec-ba57-827fcef12044.png        |
|                                   |                                                                                                                         |
|                                   | * Generator-> :doc:`Sphere </nodes/generator/sphere>`                                                                   |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+
| To 3D panel                       | Show the properties in 3D panel                                                                                         |
|                                   |                                                                                                                         |
|                                   | .. image:: https://user-images.githubusercontent.com/14288520/190246622-79240593-dd93-49ba-9a4e-a408c096602f.png        |
|                                   |                                                                                                                         |
|                                   | * Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`                                                             |
+-----------------------------------+-------------------------------------------------------------------------------------------------------------------------+


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

.. image:: https://user-images.githubusercontent.com/14288520/190243948-1b0919a8-5e69-4491-8479-fc68916a344b.png
  :target: https://user-images.githubusercontent.com/14288520/190243948-1b0919a8-5e69-4491-8479-fc68916a344b.png


**Unlock origin feature:**

.. image:: https://user-images.githubusercontent.com/28003269/91182715-93425880-e6fb-11ea-9ff5-393bbcb41490.gif
    :target: https://user-images.githubusercontent.com/28003269/91182715-93425880-e6fb-11ea-9ff5-393bbcb41490.gif