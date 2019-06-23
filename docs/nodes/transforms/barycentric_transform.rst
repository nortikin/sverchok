Barycentric Transform
=====================

Functionality
-------------

The node is coded to perform the transformation of one or many vertices according to the relation of two triangles

Eaxh triangle is defined by three vectors.


Inputs / Parameters
-------------------


+----------------------+-------------+----------------------------------------------------------------------+
| Param                | Type        | Description                                                          |  
+======================+=============+======================================================================+
| **Vertices**         | Vertices    | Points to calculate                                                  | 
+----------------------+-------------+----------------------------------------------------------------------+
| **Edg_Pol**          | Int Lists   | Edges or pols of the input Vertices (optional)                       | 
+----------------------+-------------+----------------------------------------------------------------------+
| **Verts Tri Source** | Vertices    | It will get the first and last vertices's to define the line segment |
+----------------------+-------------+----------------------------------------------------------------------+
| **Verts Tri Target** | Float       | Minimal distance to accept one point is intersecting.                |
+----------------------+-------------+----------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Implementation**: Choose between MathUtils (Faster transforming light meshes) and NumPy (Faster transforming heavy meshes)

**Output NumPy**: to get NumPy arrays in stead of regular lists (makes the node faster). Only in the NumPy implementation.

**Match List**: Define how list with different lengths should be matched. Refers to the matching of groups (one tris couple per group)

Outputs
-------

**Vertices**: Transformed vectors.

**Edg_Pol**: A matched copy of the input Edg_Pol data.


Example of usage
----------------

The node can be used to place geometry over triangular faces.

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/transforms/barycentric_transform/barycentric_transform_sverchok_blender_adaptative_tris.png
  :alt: barycentric_transform/barycentric_transform_sverchok_blender_adaptative_tris.png

  
The List Match option can offer different output combinations, in this case Cyclic is used

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/transforms/barycentric_transform/barycentric_transform_sverchok_blender_list_match.png
  :alt: barycentric_transform_sverchok_blender_list_match.png

  
Custom triangular Tessellation in this case Cyclic is used to alternate between the input geometry

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/transforms/barycentric_transform/barycentric_transform_sverchok_blender_triangle_tesselation.png
  :alt: barycentric_transform_sverchok_blender_list_match.png

