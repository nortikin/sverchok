Select Solid Elements
=====================

Dependencies
------------

This node requires FreeCAD_ library to work.

.. _FreeCAD: ../../solids.rst

Functionality
-------------

This node allows to select topological elements of Solid object (vertices,
edges, or faces) by different geometrical criteria. The node is similar to
"Select Mesh Elements by Location", but works with elements of Solid objects
instead of meshes.

One has to understand, that edges and faces of Solid objects can be far from
planar, so meanings of "edge direction" and "face normal" are very imprecise in
complex cases. However, since this node knows many ways of selecting things, it
is in most cases possible to select what you want. Also, don't forget that
several masks can be combined with "Logic" node.

The node works in two steps:

1. "Primary" selection. Vertices, edges, or faces (depending on **Select**
   parameter) are selected according to specified criteria. When selecting
   vertices, everything is more or less simple. When selecting edges or faces,
   it can appear that part of edge / face does conform to the condition, while
   other part does not. For example, it can appear that only central part of
   some face does belong to the sphere defined in selection criteria. The node
   has a parameter which defines whether such "partially selected" elements
   should be considered as selected or not.

   When selecting edges or faces at the primary selection step, the node has to
   calculate some number of points on these edges / faces, to check required
   geometrical conditions for these points. The node has a parameter to define
   how many points will be generated (more points leads to more precise
   results, but take more time).

2. "Secondary" selection. The node considers elements adjacent to the elements
   which were selected at the first step. For example, if at first step we
   selected some faces, then let's consider edges of those faces. Elements
   adjacent to "primary selection" are considered as selected. Depending on
   what type of elements were used at the first step, there also can be
   "partially selected" elements:

   * If at first step we selected vertices, then there will be some edges and
     faces, which have only some of their vertices selected;
   * If at first step we selected edges, then there will be some faces, which
     have only some of their edges selected.
   
   The node has a parameter to define whether such "partially selected"
   elements should be considered as selected or not.

For example, if **Select** parameter is set to **Vertices**, then
**VerticesMask** will contain selection mask for vertices selected at "primary
selection" step, while **EdgesMask** and **FacesMask** will contain selection
masks for edges and faces selected at "secondary selection" step.

Inputs
------

This node has the following inputs:

* **Solid**. The solid object to be considered. This input is mandatory.
* **Tool**. The secondary solid object to be used for **By Distance to Solid**,
  **Inside Solid** selection modes. This input is available and mandatory only
  for these values of **Criteria** parameter.
* **Direction**. Exact meaning of this input depends on **Criteria** parameter:

   * For **By Side** mode, this is the vector pointing to the side you want to select;
   * For **By Normal** mode, this is the direction of normals;
   * For **By Plane** mode, this is the normal vector of the plane;
   * For **By Cylinder** mode, this is the directing vector of the cylinder;
   * For **By Direction** mode, this is the direction of the edges.
   
   This input is not available for other modes.  The default value is ``(0, 0, 1)``.

* **Center**. Exact meaning of this input depends on **Criteria** parameter:

  * For **By Center and Radius** mode, this is the center of the selecting sphere;
  * For **By Plane** mode, this is a point on the selecting plane;
  * For **By Cylinder** mode, this is a point on the axis of selecting cylinder.

  This input is not available for other modes. The default value is ``(0, 0, 0)``.

* **Percent**. This defines how many elements are to be selected. Available for
  **By Side**, **By Normal**, **By Direction** modes. The default value is 1.0.
* **Radius**. Radius of the selection area. Exact meaning depends on **Criteria** parameter:

   * For **By Center and Radius** mode, this is the radius of selecting sphere;
   * For **By Plane** mode, this is the maximum distance from the plane for
     element to be selected;
   * For **By Cylinder** mode, this is the radius of selecting cylinder;
   * For **By Distance to Solid**, this is the maximum distance from the "tool"
     solid for element to be selected.

   This input is not available for other modes. The default value is 1.0.
* **Precision**. Tessellation precision for selecting edges or faces. Smaller
  values will generate more points on edges / faces, and so give more precise
  results, but will take more time to calculate. This input is available only
  when **Select** parameter is set to **Edges** or **Faces**. The default value
  is 0.01.

Parameters
----------

This node has the following parameters:

* **Select**. This defines the type of elements to be selected at primary
  selection step. The available values are **Vertices**, **Edges** and
  **Faces**. The default value is **Vertices**.
* **Criteria**. This defines the type of geometrical criteria to be used for
  primary selection. Not all types of criteria are available for all types of
  primary elements. The available types are:

   * **By Side**. Selects elements that are located at one side of the object.
     The side is specified by **Direction** input. So, you can select
     "rightmost** vertices by passing ``(1, 0, 0)`` as Direction. Number of
     elements to select is controlled by **Percent** input: 1% means select
     only "most rightmost" elements, 99% means select "all but most leftmost".
     More exactly, this mode selects point V if ``(Direction, V) >= max -
     Percent * (max - min)``, where `max` and `min` are the maximum and minimum
     values of that scalar product amongst all points being considered.
   * **By Normal**. This mode is available only when **Select** parameter is
     set to **Faces**. Selects faces, that have normal vectors pointing in the
     specified **Direction**. So you can select "faces looking to right". More
     exactly, this mode selects face F if ``(Direction, Normal(F)) >= max -
     Percent * (max - min)``, where `max` and `min` are the maximum and minimum
     values of that scalar product amongst all faces. For non-planar face, it's
     normal is calculated by calculating normals at many points of that face,
     and then averaging them.
   * **By Center and Radius**. Selects elements, which are within **Radius**
     from the specified **Center**.
   * **By Plane**. Selects elements, which are within **Radius** from the (infinite)
     plane, defined by **Center** point and **Direction** normal vector.
   * **By Cylinder**. Selects elements, which are within **Radius** from the
     (infinite) straight line, defined by **Center** point and **Direction**
     directing vector.
   * **By Direction**. This mode is available only when **Select** parameter is
     set to **Edges**. Selectsedges, which are nearly parallel to the specified
     **Direction** vector. Note that this mode considers edges as non-directed;
     as a result, you can change sign of all coordinates of **Direction**, and
     this will not affect output. More exactly, this mode selects edge E if
     `Abs(Cos(Angle(E, Direction))) >= max - Percent * (max - min)`, where max
     and min are maximum and minimum values of that cosine. For non-linear
     edges, the direction is caluclated by taking some number of points of this
     edge, and then approximating them by a straight line.
   * **By Distance to Solid**. Selects elements, which are within **Radius**
     from the second Solid object, provided in the **Tool** input.
   * **Inside Solid**. Selects elements, which are inside of the second Solid
     object, provided in the **Tool** input.

* **1. Partially selected edges, faces**. At primary selection step, this
  defines whether the node should consider edges or faces, that have only part
  of their points conforming to the condition, as selected. This parameter is
  not available when the **Select** parameter is set to **Vertices**. Unchecked by default.
* **2. Partially selected edges, faces**. At secondary selection step, this
  defines whether the node should consider edges or faces, that have only part
  of their vertices / edges selected at the primary step, as selected. Unchecked by default.
* **Tolerance**. This parameter is available only when **Criteria** parameter
  is set to **Inside Solid**. This defines the precision of calculation.
  Smaller values give more precise results, but take more time. The default
  value is 0.01.
* **Including shell**. This parameter is available only when **Criteria**
  parameter is set to **Inside Solid**. This defines, whether points lying
  directly on a face of the Tool solid, are to be considered as selected.
  Unchecked by default.

Outputs
-------

This node has the following outputs:

* **VerticesMask**. Mask for selected vertices.
* **EdgesMask**. Mask for selected edges.
* **FacesMask**. Mask for selected faces.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/92938146-a2e4cf80-f465-11ea-9e9b-d938dd9dd629.png

