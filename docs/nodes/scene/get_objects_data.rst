Get Objects Data
================

.. image:: https://github.com/user-attachments/assets/63ffe714-6aec-4d23-b575-c0519abd7298
  :target: https://github.com/user-attachments/assets/63ffe714-6aec-4d23-b575-c0519abd7298

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
- add selected objects from scene into the list individually:

  .. image:: https://github.com/user-attachments/assets/827589d4-13ca-4523-b0eb-0380932d8260
    :target: https://github.com/user-attachments/assets/827589d4-13ca-4523-b0eb-0380932d8260

- move objects in list up and down:

  .. image:: https://github.com/user-attachments/assets/7e1c2fee-e757-4523-a0b4-3659e5d3a851
    :target: https://github.com/user-attachments/assets/7e1c2fee-e757-4523-a0b4-3659e5d3a851

- enable/disable objects in list to exclude some objects from process:

  .. image:: https://github.com/user-attachments/assets/1daefd0b-bda2-46b7-930f-41457873684f
    :target: https://github.com/user-attachments/assets/1daefd0b-bda2-46b7-930f-41457873684f

  This work for collections too:

    .. image:: https://github.com/user-attachments/assets/32446a11-cffe-4e75-9b27-da7e2791b8fb
      :target: https://github.com/user-attachments/assets/32446a11-cffe-4e75-9b27-da7e2791b8fb

- select objects or collections in scene by operator in list. Use Shift key to append object into selection set

  .. raw:: html

    <video width="700" controls>
      <source src="https://github.com/user-attachments/assets/d4bd813f-a9c2-488e-b7fc-e9251ac61af5" type="video/mp4">
      Your browser does not support the video tag.
    </video>

- Find active object in list. If object is in collection then active position will be switched on duplicates or collections that has this object

  .. raw:: html

    <video width="700" controls>
      <source src="https://github.com/user-attachments/assets/2e43c672-93f5-4bdf-bf31-8da6720ffafe" type="video/mp4">
      Your browser does not support the video tag.
    </video>

- duplicates objects can be marked with a sign (for active object in list):

  .. image:: https://github.com/user-attachments/assets/41b112c4-4688-4214-9cff-f5191e8a456f
    :target: https://github.com/user-attachments/assets/41b112c4-4688-4214-9cff-f5191e8a456f

- add collections into the list (1-add empty pointer, 2-open list of collections in this scene, 3-select collection):

  .. image:: https://github.com/user-attachments/assets/8a026341-8ec3-48ce-98aa-06e339cabce5
    :target: https://github.com/user-attachments/assets/8a026341-8ec3-48ce-98aa-06e339cabce5

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

Simplify node view
------------------

This node can be very large. If you have no plans to use all sockets then you can hide unused socket:

  .. image:: https://github.com/user-attachments/assets/55a8b530-b822-41f4-8ed7-4260ef455be9
    :target: https://github.com/user-attachments/assets/55a8b530-b822-41f4-8ed7-4260ef455be9

Also you can simplify table view ob objects:

  .. image:: https://github.com/user-attachments/assets/9ebe3a1f-783b-4a07-a4cf-aa121db8115c
    :target: https://github.com/user-attachments/assets/9ebe3a1f-783b-4a07-a4cf-aa121db8115c

Additionally
------------

- You can see objects info in description of elements on mouse hover:

  .. image:: https://github.com/user-attachments/assets/5afb43b4-7651-4d03-9dc8-14b291bf7ca3
    :target: https://github.com/user-attachments/assets/5afb43b4-7651-4d03-9dc8-14b291bf7ca3

- Added Metaball and Point Cloud

Inputs
------

Objects Socket. You can select object or link to Collection picker node to select a collection:

  .. image:: https://github.com/user-attachments/assets/f3c654c2-51c1-4d06-aee8-e02ec88bc747
    :target: https://github.com/user-attachments/assets/f3c654c2-51c1-4d06-aee8-e02ec88bc747

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
| Material Names        | Material names per object face.                                          |
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

About Material Idx and Material Names
-------------------------------------

Initially, these parameters produce results according to the materials in the corresponding material sockets of the object.
When the node parameters “Mesh Join” and “Post” are enabled, the material indices are combined, duplicate materials are removed,
the Material Names are sorted alphabetically, and the Material Idx values are renumbered according to each material name’s
position after sorting. If a material is not assigned but is used by some Faces, this material is treated as None, and during
the sorting of Material Names, the value None is placed at the end of the sorted list.

Before Mesh Join:

  .. image:: https://github.com/user-attachments/assets/fca3b1de-9e39-4bae-91ba-e688643a9dcd
    :target: https://github.com/user-attachments/assets/fca3b1de-9e39-4bae-91ba-e688643a9dcd

After Mesh Join:

  .. image:: https://github.com/user-attachments/assets/2ade627a-a965-478e-9ee6-e3b6b3c6964b
    :target: https://github.com/user-attachments/assets/2ade627a-a965-478e-9ee6-e3b6b3c6964b

Material Idx can be used to calculate the area of materials.

Custom Properties out to the sockets
------------------------------------

Custom properties can be out to the output sockets:

  .. image:: https://github.com/user-attachments/assets/10bffb4a-2ea8-48a1-a149-323a260c42e4
    :target: https://github.com/user-attachments/assets/10bffb4a-2ea8-48a1-a149-323a260c42e4

Description custom properties
-----------------------------

Blender has several kinds of custom properties, associated with different parts of an object:

- directly with the object in the scene
- with the object’s data (the Data section)
- with materials

.. image:: https://github.com/user-attachments/assets/749d639d-ae29-47d6-965a-1645d11af777
  :target: https://github.com/user-attachments/assets/749d639d-ae29-47d6-965a-1645d11af777

Some objects may be different. Lamp has no materials, Empty has no Data and Materials, Point Cloud has no Mesh (only verts), but has all types of Custom Properties.

  .. image:: https://github.com/user-attachments/assets/98510555-106a-4632-b3c0-ad6da160de80
    :target: https://github.com/user-attachments/assets/98510555-106a-4632-b3c0-ad6da160de80


Lets create prices for every material. Create two object: a Suzanne and a Sphere with materials. As you can see there are no custom property in materials:

  .. image:: https://github.com/user-attachments/assets/4bb81e03-bdb9-470b-8a18-54b0b81bc44f
    :target: https://github.com/user-attachments/assets/4bb81e03-bdb9-470b-8a18-54b0b81bc44f

Create a Price custom attribute for one material. For example for an Icosphere:

  .. image:: https://github.com/user-attachments/assets/16b9e511-1d8f-48b2-91ac-737e5f2ced4d
    :target: https://github.com/user-attachments/assets/16b9e511-1d8f-48b2-91ac-737e5f2ced4d

As you can see no "Price" custom attribute in another materials for a while. Add Suzanne and Icosphere into "Get Object Data". Select Icosphere only after:

  .. image:: https://github.com/user-attachments/assets/a4172654-c977-4394-8a06-de8066e45508
    :target: https://github.com/user-attachments/assets/a4172654-c977-4394-8a06-de8066e45508

Create new socket:

.. image:: https://github.com/user-attachments/assets/40f5002a-3c29-4571-be61-e5f5e83ae415
  :target: https://github.com/user-attachments/assets/40f5002a-3c29-4571-be61-e5f5e83ae415

This action will copy Price into another materials:

  .. image:: https://github.com/user-attachments/assets/3da07b40-e8dd-4286-8b3c-5ddf4d8d27fd
    :target: https://github.com/user-attachments/assets/3da07b40-e8dd-4286-8b3c-5ddf4d8d27fd

Set different prices for materials:

  .. image:: https://github.com/user-attachments/assets/4bdfa5ca-8f83-41bc-a77b-fbb7ad23e84d
    :target: https://github.com/user-attachments/assets/4bdfa5ca-8f83-41bc-a77b-fbb7ad23e84d

And check prices in the socket:

  .. image:: https://github.com/user-attachments/assets/bee70087-a6e1-4e52-a0ab-ac57eb02e787
    :target: https://github.com/user-attachments/assets/bee70087-a6e1-4e52-a0ab-ac57eb02e787

Calc Areas by materials:

  .. image:: https://github.com/user-attachments/assets/f6e49f48-8b36-4051-b4e3-c1b8a56e2b06
    :target: https://github.com/user-attachments/assets/f6e49f48-8b36-4051-b4e3-c1b8a56e2b06

Calc Price of materials:

  .. image:: https://github.com/user-attachments/assets/dc496857-cd2c-4ab9-8b66-dd51c72ecc84
    :target: https://github.com/user-attachments/assets/dc496857-cd2c-4ab9-8b66-dd51c72ecc84

Now you know that Suzanne's eyes has a price 13.923$. 

Custom property animation
-------------------------

Create Cube and create 2 custom property in Object mode:

  .. image:: https://github.com/user-attachments/assets/1bdf8a21-9eb6-43fb-adcf-e4ae79624693
    :target: https://github.com/user-attachments/assets/1bdf8a21-9eb6-43fb-adcf-e4ae79624693

Create next node scheme and add X and Y custom properties:

  .. image:: https://github.com/user-attachments/assets/6ccd7b82-be4f-4c9f-8216-8afcf8663c2c
    :target: https://github.com/user-attachments/assets/6ccd7b82-be4f-4c9f-8216-8afcf8663c2c

Create F-curve modifier animation:

.. image:: https://github.com/user-attachments/assets/4dad105d-d902-45d5-ae2f-9f9fd66f8ed9
  :target: https://github.com/user-attachments/assets/4dad105d-d902-45d5-ae2f-9f9fd66f8ed9

.. raw:: html

   <video width="700" controls>
     <source src="https://github.com/user-attachments/assets/ce39820a-a789-4776-bd66-e1ff537cf8e2" type="video/mp4">
    Your browser does not support the video tag.
   </video>

Now you can do animation of Sverchok Scheme with custom properties and custom properties animation, animation keys and animation modifiers.
Additionally: The animation of Sverchok Nodes with Blender is not possible.

Animated custom property example: [GetObjectsData.MK5.002.Blender.3.0.0.blend.zip](https://github.com/user-attachments/files/24540889/GetObjectsData.MK5.002.Blender.3.0.0.blend.zip)

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