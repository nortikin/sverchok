Contour 2D
==========

.. image:: https://user-images.githubusercontent.com/14288520/200914294-d50fef6e-77cc-465d-92d8-24fc1986e1bc.png
  :target: https://user-images.githubusercontent.com/14288520/200914294-d50fef6e-77cc-465d-92d8-24fc1986e1bc.png

Functionality
-------------

This node creates one or many contours at specified distance.

- It is fed by sets of vertices and edges.
- Every set of vertices needs to share the Z coordinate in order to create a valid contour.

.. image:: https://user-images.githubusercontent.com/14288520/200941341-4713e599-b1e4-4b9c-818d-ae099ca0c7ed.png
  :target: https://user-images.githubusercontent.com/14288520/200941341-4713e599-b1e4-4b9c-818d-ae099ca0c7ed.png

Inputs
------

This node has the following inputs, all of them can accept one or many different values:

- **Distance** - distance to vertex.
- **Nº Vertices** - Number of vertices per vertex
- **Verts_in** - origin vertices.
- **Edgs_in** - edges (pairs of integers).


Parameters
----------


+------------------+---------------+-------------+-------------------------------------------------------------+
| Parameter        | Type          | Default     | Description                                                 |
+==================+===============+=============+=============================================================+
|**Mode**          | Menu          | Constant    |**Constant**: Constant distances on each perimeter.          |
|                  |               |             |                                                             |
|                  |               |             |**Weighted**: Different distances per vertex.                |
+------------------+---------------+-------------+-------------------------------------------------------------+
|**Remove Doubles**| Float         | 1.0         | Remove doubled vertices under this distance.                |
+------------------+---------------+-------------+-------------------------------------------------------------+
|**Distance**      | Float         | 1.0         | Distance to vertex.                                         |
+------------------+---------------+-------------+-------------------------------------------------------------+
|**Nº Vertices**   | Float         | 1.0         | Number of vertices per vertex.                              |
+------------------+---------------+-------------+-------------------------------------------------------------+
| **Verts_in**     | Vector        |(0.0,0.0,0.0)| Origin vectors.                                             |
+------------------+---------------+-------------+-------------------------------------------------------------+
| **Edges_in**     | Int tuples    | []          | Connection between vertices                                 |
+------------------+---------------+-------------+-------------------------------------------------------------+
|In the N-Panel                                                                                                |
+------------------+---------------+-------------+-------------------------------------------------------------+
|**Mask Tolerance**| Float         | 1.0e-5      | Tolerance on masking (for low Nº Vertices                   |
|                  |               |             |                                                             |
|                  |               |             | or small values)                                            |
+------------------+---------------+-------------+-------------------------------------------------------------+
|**Inters. Mode**  | Menu          | Circular    |**Circular**: Intersection based on circles (Slower).        |
|                  |               |             |                                                             |
|                  |               |             |**Polygonal**: Intersection based on polygons (Faster).      |
+------------------+---------------+-------------+-------------------------------------------------------------+
|**List Match**    | Menu          | Long Cycle  |**Long Repeat**: After shortest list repeat last value.      |
|                  |               |             |                                                             |
|                  |               |             |**Long Cycle**: After shortest list got to first last value. |
+------------------+---------------+-------------+-------------------------------------------------------------+
|**Remove Caps**   | Boolean       | False       | Remove arcs in the vertices with only one edge.             |
+------------------+---------------+-------------+-------------------------------------------------------------+


Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/10011941/34644861-37e4c430-f33f-11e7-92e0-d89080effc4b.png
  :target: https://user-images.githubusercontent.com/10011941/34644861-37e4c430-f33f-11e7-92e0-d89080effc4b.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

- When you input different distances:
  In constant mode independent contours will be created (one per distance)
  In Weighted mode will apply each distance to a vertex creating independent contours when there are more distances than vertices

.. image:: https://user-images.githubusercontent.com/10011941/34644863-41eabfde-f33f-11e7-8ed6-6e8fa7a1e6df.png
  :target: https://user-images.githubusercontent.com/10011941/34644863-41eabfde-f33f-11e7-8ed6-6e8fa7a1e6df.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Range Float: Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

- When you input different objects independent contours will be created:

.. image:: https://user-images.githubusercontent.com/10011941/34644864-46463d24-f33f-11e7-80c1-bb0718d9966b.png
  :target: https://user-images.githubusercontent.com/10011941/34644864-46463d24-f33f-11e7-80c1-bb0718d9966b.png

* Modifiers->Modifier Change-> :doc:`Mesh Join </nodes/modifier_change/mesh_join_mk2>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

- With the intersection mode on "Circular" the intersection points will be placed as if we were using perfect circles. This will change the edges angles, but the distance between the intersection point and the original points will be maintained. On "Polygonal" the edges angles are preserved but the distance to original vertex will depend on the number of vertices.

.. image:: https://user-images.githubusercontent.com/10011941/35116834-027e2f8c-fc8d-11e7-9cff-35465e3e5e17.png
  :target: https://user-images.githubusercontent.com/10011941/35116834-027e2f8c-fc8d-11e7-9cff-35465e3e5e17.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

- Integrated list match function can lead to different results:

.. image:: https://user-images.githubusercontent.com/10011941/34644870-5935b1ee-f33f-11e7-99ba-0c536bf67f91.png
  :target: https://user-images.githubusercontent.com/10011941/34644870-5935b1ee-f33f-11e7-99ba-0c536bf67f91.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Range Float: Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

- Different ranges can be used to create a complex contour.

.. image:: https://user-images.githubusercontent.com/10011941/35116835-029ea8de-fc8d-11e7-9df0-f044677c059a.png
  :target: https://user-images.githubusercontent.com/10011941/35116835-029ea8de-fc8d-11e7-9df0-f044677c059a.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Modifiers->Modifier Change-> :doc:`Smooth Vertices </nodes/modifier_change/smooth>`
* Modifiers->Modifier Change-> :doc:`Triangulate Mesh </nodes/modifier_change/triangulate>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Range Float: Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* ADD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Vector-> :doc:`Vector Interpolation </nodes/vector/interpolation_mk3>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Struct-> :doc:`List Flip </nodes/list_struct/flip>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

- When using text meshes it can get very slow but also interesting

.. image:: https://user-images.githubusercontent.com/10011941/35116836-02b9cc36-fc8d-11e7-9526-259c18c8556f.png
  :target: https://user-images.githubusercontent.com/10011941/35116836-02b9cc36-fc8d-11e7-9526-259c18c8556f.png

* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* Analyzer-> :doc:`Mesh Filter </nodes/analyzer/mesh_filter>`
* Analyzer-> :doc:`Mesh Filter </nodes/analyzer/mesh_filter>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* ADD: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Range Float: Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Viz-> :doc:`Curve Viewer </nodes/viz/viewer_curves>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Notes
-----

- This implementation can get very slow when working with hundreds of inputs and different distances, handle it with patience.
- If the node does not create a closed contour try increasing the vertices number or rising the mask tolerance slowly
- This is the pull request where this node was added https://github.com/nortikin/sverchok/pull/2001
