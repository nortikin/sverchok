Extrude Region
==============

Functionality
-------------

This node applies Extrude operator to the region of selected faces, as whole. After that, resulting faces can be either transformed by any matrix, or moved along normal and scaled.
If transformation is specified by matrix, it is possible to provide specific matrix for each vertex.

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Polygons**
- **Mask**. List of boolean or integer flags. Zero means do not process face with corresponding index. If this input is not connected, then by default all faces will be processed.
- **Height**. Extrude factor. Available only in **Along normal** mode.
- **Scale**. Scaling factor. Available only in **Along normal** mode.
- **Matrix**. Transformation matrices. Available only in **Matrix** mode.

Parameters
----------

This node has the following parameters:

- **Transformation mode**. Controls how the transformation of extruded vertices is specified. There are two modes available:

  - **Matrix**. This is the default mode. Transformation is specified by matrix provided at **Matrix** input. 
  - **Along normal**. Vertices are translated along normal and scaled. Please note, that by *normal* here we mean *average of normals of selected faces*. Scaling center is average center of selected faces.
- **Keep original**. If checked, the original geometry will be passed to output as well as extruded geometry.
- **Height**. Available only in **Along normal** mode. Extrude factor as a portion of face normal length. Default value of zero means do not extrude. Negative value means extrude to the opposite direction. This parameter can be also provided via corresponding input.
- **Scale**. Available only in **Along normal** mode. Scale factor. Default value of 1 means do not scale. This parameter can be also provided via corresponding input.

Outputs
-------

This node has the following outputs:

- **Vertices**. All vertices of resulting mesh.
- **Edges**. All edges of resulting mesh.
- **Polygons**. All faces of resulting mesh.
- **NewVerts**. Only newly created vertices.
- **NewEdges**. Only newly created edges. Note that indices here relate to **Vertices** output, not to **NewVerts**.
- **NewFaces**. Only newly created faces. Note that indices here relate to **Vertices** output, not to **NewVerts**.

Examples of usage
-----------------

Extrude along normal:

.. image:: https://cloud.githubusercontent.com/assets/284644/23824189/4686ba06-069c-11e7-9522-51d25e7667ad.png

Extrude by scale matrix:

.. image:: https://cloud.githubusercontent.com/assets/284644/23824190/46b7b1a6-069c-11e7-87fb-ddabeb87e6b9.png

