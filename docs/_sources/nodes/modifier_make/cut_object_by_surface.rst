Cut Object by Surface
=====================

.. image:: https://user-images.githubusercontent.com/14288520/198824817-a8729120-16f4-4c9c-baa5-6dec7dd049a7.png
  :target: https://user-images.githubusercontent.com/14288520/198824817-a8729120-16f4-4c9c-baa5-6dec7dd049a7.png

Functionality
-------------

This node cuts **edges** of one mesh ("object") by intersecting them with faces
of another mesh ("surface"). It can connect the new vertices by creating new
faces, to produce a cut surface. It can also output the pieces of the object,
that are the result of cutting. This is similar to "Cross Section" and "Bisect"
nodes, but it operates with any surface, not just with plane. In a sense, this
operation can be considered as a very simple analog of Boolean operations, but
it finds intersections of **edges**, not intersections of volumes.

**Implementation restriction**: when generating cut surface or making cut pieces,
the node requires that of each face of "object" mesh, only two edges intersect 
the "surface" mesh. So, each face can be cut only in two pieces, not in three or more.
The node will not crash, just ignore these options and simply output intersection points.

.. image:: https://user-images.githubusercontent.com/14288520/198825816-dc69dab6-36fa-40a5-9ad5-481d9b43d17e.gif
  :target: https://user-images.githubusercontent.com/14288520/198825816-dc69dab6-36fa-40a5-9ad5-481d9b43d17e.gif

**Developer notes** : for those interested in removing this limitation, a general idea
on how to proceed, with its limitations, is included in the code as comments.
If multiple points are detected for a single real intersection point,
see comments in the code for a solution on how to solve it. 

Faces made by this node at places of cut will be usually NGons, so they may be
non-planar. It may be good idea to pass the output of this node through the
**Split faces** node (in **split non-planar faces** mode), or maybe through
**Make faces planar** node. Furthermore, the cut surface do not follow the surface
mesh, it just connects the intersection points (the aforementioned limitation-solving
idea would solve this too).


Note that this node outputs "cut pieces" mesh always as one merged object (not
split into pieces). If you need these pieces in separate, you can pass the
output of this node through the **Separate Loose Parts** node.

Inputs
------

This node has the following inputs:

* **ObjVertices**. Vertices of the "object" mesh (the mesh which is to be cut).
* **ObjEdges**. Edges of the "object" mesh.
* **ObjFaces**. Faces of the "object" mesh.
* **SurfVertices**. Vertices of the "surface" mesh (the mesh which cuts the "object").
* **SurfEdges**. Edges of the "surface" mesh.
* **SurfFaces**. Faces of the "surface" mesh.
* **FillSides**. Maximum number of sides of polygons that the node makes to
  fill the cuts. This input can also be provided as a parameter. This input is
  only available when **Make cut pieces** parameter is checked. The default
  value is 12.

Parameters
----------

This node has the following parameters:

* **Make cut faces**. If checked, the node will fill the holes made by cut
  edges, by creating new faces. Maximum number of sides of such faces is
  controlled by **FillSides** input parameter. If not checked, then such holes
  will not be filled. Unchecked by default.
* **Make cut pieces**. If checked, the node will calculate piece meshes, which
  are formed by cutting the "object" mesh. If not checked, the node will
  calculate only cut surfaces - the surfaces of intersection of the "object"
  and the "surface". Unchecked by default.

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **All triangles**. Boolean to work with triangularized surface mesh (makes the node faster).
* **Block**. Boolean to define whether or not the node should raise an error when more than
  two intersections by face are found

Outputs
-------

This node has the following outputs:

* **CutVertices**. The vertices of "cut surface" mesh - the area of the
  "surface" mesh which intersects the "object" mesh.
* **CutEdges**. The edges of "cut surface" mesh.
* **CutFaces**. The faces of "cut surface" mesh. This output is only available
  when **Make cut faces** parameter is checked.
* **ObjVertices**. The vertices of the "cut pieces" mesh - the mesh formed by
  cutting the "object" mesh. This output is only available if the **Make cut
  pieces** parameter is checked.
* **ObjEdges**. The edges of the "cut pieces" mesh. This output is only
  available if the **Make cut pieces** parameter is checked.
* **ObjFaces**. The faces of the "cut pieces" mesh. If **Make cut faces**
  parameter is not checked, then this output will not contain faces in places
  where the "object" is cut by "surface" (i.e. there will be holes). This
  output is only available if the **Make cut pieces** parameter is checked.

.. image:: https://user-images.githubusercontent.com/14288520/198872895-229c30cb-3e5b-4f3a-b456-b16b27fcf96a.png
  :target: https://user-images.githubusercontent.com/14288520/198872895-229c30cb-3e5b-4f3a-b456-b16b27fcf96a.png

Examples of usage
-----------------

Sphere cut by the box. Here we intersect edges of the sphere with the box, and
connect resulting vertices. Note that in this case the number of box's
subdivisions does not have any meaning, because the places of intersections of
sphere's edges with the box are always the same.

.. image:: https://user-images.githubusercontent.com/14288520/198826268-d9f35b1a-0838-4247-89d7-2902a335e4f5.png
  :target: https://user-images.githubusercontent.com/14288520/198826268-d9f35b1a-0838-4247-89d7-2902a335e4f5.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Box cut by sphere. Here we intersect edges of the box with the sphere, and then
connect resulting vertices. Note that if we specify number of box's
subdivisions = 1, we would get nothing at all.

.. image:: https://user-images.githubusercontent.com/14288520/198826493-2f2b97bd-3fd1-415d-935b-737ad30d01f4.png
  :target: https://user-images.githubusercontent.com/14288520/198826493-2f2b97bd-3fd1-415d-935b-737ad30d01f4.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/198826593-e906e059-d88b-413b-add3-07c96b45051e.gif
  :target: https://user-images.githubusercontent.com/14288520/198826593-e906e059-d88b-413b-add3-07c96b45051e.gif

---------

Intersection of eight cubes (green edges) with the icosphere (yellowish edges):

.. image:: https://user-images.githubusercontent.com/14288520/198827326-1735070e-8862-42f3-9524-7eb317572fcc.png
  :target: https://user-images.githubusercontent.com/14288520/198827326-1735070e-8862-42f3-9524-7eb317572fcc.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/198827251-28890723-1762-4265-85be-5e8f033f4253.gif
  :target: https://user-images.githubusercontent.com/14288520/198827251-28890723-1762-4265-85be-5e8f033f4253.gif

---------

The same cut surface passed through the "split faces" node:

.. image:: https://user-images.githubusercontent.com/14288520/198828991-37f88604-6cea-4cee-a980-11dbe8465a60.png
  :target: https://user-images.githubusercontent.com/14288520/198828991-37f88604-6cea-4cee-a980-11dbe8465a60.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Modifiers->Modifier Change-> :doc:`Split Faces </nodes/modifier_change/split_faces>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`


Here you can see this node is not at all the boolean operation — it makes one
big face where the boolean operation would make a part of sphere.

The output of **Make cut pieces**:

.. image:: https://user-images.githubusercontent.com/284644/72451364-9f694d80-37dd-11ea-854d-565a16132a03.png

