Extrude Region
==============

.. image:: https://user-images.githubusercontent.com/14288520/200082470-2101619a-c63c-45e6-8663-017922fafbc8.png
  :target: https://user-images.githubusercontent.com/14288520/200082470-2101619a-c63c-45e6-8663-017922fafbc8.png

Functionality
-------------

This node applies Extrude operator to the region of selected faces, as whole. After that, resulting faces can be either transformed by any matrix, or moved along normal and scaled.
If transformation is specified by matrix, it is possible to provide specific matrix for each vertex.

.. image:: https://user-images.githubusercontent.com/14288520/200111848-b798b6b6-06d8-4679-822c-957e3d7ea3ee.png
  :target: https://user-images.githubusercontent.com/14288520/200111848-b798b6b6-06d8-4679-822c-957e3d7ea3ee.png

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Polygons**
- **Mask**. List of boolean or integer flags. Zero means do not process face
  with corresponding index. If this input is not connected, then by default all
  faces will be processed.
- **Height**. Extrude factor. Available only in **Along normal** mode.
- **Scale**. Scaling factor. Available only in **Along normal** mode.
- **Matrix**. Transformation matrices. Available only in **Matrix** mode.

Parameters
----------

This node has the following parameters:

- **Transformation mode**. Controls how the transformation of extruded vertices
  is specified. There are two modes available:

  - **Matrix**. This is the default mode. Transformation is specified by matrix
    provided at **Matrix** input. 
  - **Along normal**. Vertices are translated along normal and scaled. Please
    note, that by *normal* here we mean *average of normals of selected faces*.
    Scaling center is average center of selected faces.
- **Multiple extrude**. This parameter defines how to deal with multiple
  matrices passed into **Matrix** input or multiple values passed into
  **Height** and **Scale** inputs. This parameter is available only in
  **Matrix** mode; in **Along normal** mode, this parameter is always checked.

  - If not checked (and **Matrix** mode is used), then each matrix provided
    will be applied to corresponding extruded vertex. So number of matrices in
    input is expected to be from 1 to the number of vertices which are
    extruded.
  - If checked, or **Along normal** mode is used, then extrusion operation may
    be performed several times:

    - In **Along normal** mode, extrusion operation will be performed one time
      for each pair of **Height** and **Scale** input values.
    - In **Matrix** mode, extrusion operation will be performed one time for
      each matrix passed into **Matrix** input.
- **Dissolve Orthogonal Edges**. This parameter is available only since Blender
  version 2.90. Removes and connects edges whose faces form a flat surface and
  intersect new edges. Unchecked by default.
- **Keep original**. If checked, the original geometry will be passed to output
  as well as extruded geometry. This parameter is visible only in
  **Properties** (N) panel.
- **Height**. Available only in **Along normal** mode. Extrude factor as a
  portion of face normal length. Default value of zero means do not extrude.
  Negative value means extrude to the opposite direction. This parameter can be
  also provided via corresponding input.
- **Scale**. Available only in **Along normal** mode. Scale factor. Default
  value of 1 means do not scale. This parameter can be also provided via
  corresponding input.
- **Mask Output**. Defines which faces will be marked with 1 in the **Mask**
  output. Several modes may be selected together. The available modes are:

   - **Mask**. The faces which were masked out by the **Mask** input.
   - **In**. Inner faces of the extrusion, i.e. the same faces that are in the
     **ExtrudedFaces**  output.
   - **Out**. Outer faces of the extrusion.

   The default value is **Out**.

Outputs
-------

This node has the following outputs:

- **Vertices**. All vertices of resulting mesh.
- **Edges**. All edges of resulting mesh.
- **Polygons**. All faces of resulting mesh.
- **NewVerts**. Only newly created vertices.
- **NewEdges**. Only newly created edges.
- **NewFaces**. Only newly created faces.
- **Mask**. Mask for faces of the resulting mesh; which faces are selected
  depends on the **Mask Output** parameter.
- **FaceData**. List containing data items from the **FaceData** input, which
  contains one item for each output mesh face.

**Note 1**: Indicies in **NewEdges**, **NewFaces**, **Mask** outputs relate to
vertices in **Vertices** output, not to **NewVerts** ones.

**Note 2**: If multiple extrusion is used, then **NewVerts**, **NewEdges**,
**NewFaces**, **Mask** outputs will contain only geometry created by *last*
extrusion operation.

Examples of usage
-----------------

Extrude along normal:

.. image:: https://user-images.githubusercontent.com/14288520/200112273-879eb030-b0fa-40c8-8b05-6b7fc03aa104.png
  :target: https://user-images.githubusercontent.com/14288520/200112273-879eb030-b0fa-40c8-8b05-6b7fc03aa104.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Analyzers-> :ref:`Select Mesh Elements (By Center and radius)<MODE_BY_CENTER_AND_RADIUS>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Extrude by scale matrix:

.. image:: https://user-images.githubusercontent.com/14288520/200112489-b9eac1f7-25a8-4be3-bce9-6d29f5003017.png
  :target: https://user-images.githubusercontent.com/14288520/200112489-b9eac1f7-25a8-4be3-bce9-6d29f5003017.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Analyzers-> :ref:`Select Mesh Elements (By Center and radius)<MODE_BY_CENTER_AND_RADIUS>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Multiple extrusion mode:

.. image:: https://user-images.githubusercontent.com/14288520/200115164-2be6a492-f834-46c4-b49a-443c9d15e0f6.png
  :target: https://user-images.githubusercontent.com/14288520/200115164-2be6a492-f834-46c4-b49a-443c9d15e0f6.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzers-> :ref:`Select Mesh Elements (By Center and radius)<MODE_BY_CENTER_AND_RADIUS>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Example of FaceData sockets usage:

.. image:: https://user-images.githubusercontent.com/14288520/200115914-b7cef699-9436-4157-990f-6d7f328a110d.png
  :target: https://user-images.githubusercontent.com/14288520/200115914-b7cef699-9436-4157-990f-6d7f328a110d.png

* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Analyzers-> :ref:`Select Mesh Elements (By Center and radius)<MODE_BY_CENTER_AND_RADIUS>`
* Analyzers-> :doc:`Wave Painter </nodes/analyzer/wave_paint>`
* Modifiers->Modifier Change-> :doc:`Flip Normals </nodes/modifier_change/flip_normals>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* List->List Main-> :doc:`List Math </nodes/list_main/func>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* NOT: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Example of Mask output usage together with Extrude Separate node:

.. image:: https://user-images.githubusercontent.com/284644/71817318-4562dc80-30a7-11ea-9f44-ae2d2bae7acf.png
  :target: https://user-images.githubusercontent.com/284644/71817318-4562dc80-30a7-11ea-9f44-ae2d2bae7acf.png

replay with new nodes:

.. image:: https://user-images.githubusercontent.com/14288520/200116794-70581c84-8f8f-4265-b4c4-7109375a863a.png
  :target: https://user-images.githubusercontent.com/14288520/200116794-70581c84-8f8f-4265-b4c4-7109375a863a.png

* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Modifiers->Modifier Change-> :doc:`Flip Normals </nodes/modifier_change/flip_normals>`
* Analyzers-> :ref:`Select Mesh Elements (By Center and radius)<MODE_BY_CENTER_AND_RADIUS>`
* Analyzers-> :doc:`Wave Painter </nodes/analyzer/wave_paint>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* List->List Main-> :doc:`List Math </nodes/list_main/func>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Modifiers->Modifier Change-> :doc:`Extrude Separate Faces </nodes/modifier_change/extrude_separate>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* BPY Date-> Vertex Color MK3 (No docs)

---------

Example of "Dissolve orthogonal edges" parameter usage:

.. image:: https://user-images.githubusercontent.com/14288520/200117301-f28d4450-eeb4-4d30-b28f-22e3018003bf.png
  :target: https://user-images.githubusercontent.com/14288520/200117301-f28d4450-eeb4-4d30-b28f-22e3018003bf.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Analyzers-> :ref:`Select Mesh Elements (By Cylinder)<MODE_BY_CYLINDER>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`