Cut Object by Surface
=====================

Functionality
-------------

This node cuts **edges** of one mesh ("object") by intersecting them with faces
of another mesh ("surface"). It can connect the new vertices by creating new
faces, to produce a cut surface. It can also output the pieces of the object,
that are the result of cutting. This is similar to "Cross Section" and "Bisect"
nodes, but it operates with any surface, not just with plane. In a sense, this
operation can be considered as a very simple analog of Boolean operations, but
it finds intersections of **edges**, not intersections of volumes.

**Implementation restriction**: the node requires that of each face of "object"
mesh, only two edges intersect the "surface" mesh. So, each face can be cut
only in two pieces, not in three or more.

Faces made by this node at places of cut will be usually NGons, so they may be
non-planar. It may be good idea to pass the output of this node through the
**Split faces** node (in **split non-planar faces** mode), or maybe through
**Make faces planar** node.


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
  only available when **Make cut pieces" parameter is checked. The default
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

