Extrude Separate Faces
======================

.. image:: https://user-images.githubusercontent.com/14288520/200059403-a4f56307-a840-4e45-8f4e-0fe1f803e7b9.png
  :target: https://user-images.githubusercontent.com/14288520/200059403-a4f56307-a840-4e45-8f4e-0fe1f803e7b9.png

Functionality
-------------

This node applies Extrude operator to each of input faces separately. After
that, resulting faces can be scaled up or down by specified factor.
It is possible to provide specific extrude and scaling factors for each face.
As an option, transformation matrix may be provided for each face.

.. image:: https://user-images.githubusercontent.com/14288520/200061209-f3345179-13ac-4a52-8e7b-ac646464d86d.png
  :target: https://user-images.githubusercontent.com/14288520/200061209-f3345179-13ac-4a52-8e7b-ac646464d86d.png

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Polygons**
- **Mask**. List of boolean or integer flags. Zero means do not process face
  with corresponding index. If this input is not connected, then by default all
  faces will be processed.
- **Height**. Extrude factor.
- **Scale**. Scaling factor.
- **Matrix**. Transformation matrix. Default value is the identity matrix.
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.

Parameters
----------

This node has the following parameters:

+-----------------+---------------+-------------+------------------------------------------------------+
| Parameter       | Type          | Default     | Description                                          |
+=================+===============+=============+======================================================+
| **Mode**        | Enumeration   | Normal      | This defines how the transformation of faces being   |
|                 |               |             |                                                      |
|                 |               |             | extruded is specified. There are the following       |
|                 |               |             |                                                      |
|                 |               |             | modes available:                                     |
|                 |               |             |                                                      |
|                 |               |             | * **Normal**: the transformation is defined by       |
|                 |               |             |                                                      |
|                 |               |             |   **Height** and **Scale** inputs (see below).       |
|                 |               |             |                                                      |
|                 |               |             | * **Matrix**: the transformation is defined by       |
|                 |               |             |                                                      |
|                 |               |             |   the **Matrix** input.                              |
+-----------------+---------------+-------------+------------------------------------------------------+
| **Mask mode**   | Enumeration   | Do not      | This defines what exactly to do with faces that are  |
|                 |               |             |                                                      |
|                 |               | extrude     | masked out. The available modes are:                 |
|                 |               |             |                                                      |
|                 |               |             | * **Do not extrude**. Do not perform extrusion       |
|                 |               |             |                                                      |
|                 |               |             |   operation on such faces.                           |
|                 |               |             |                                                      |
|                 |               |             | * **Do not transform**. Such faces will be           |
|                 |               |             |                                                      |
|                 |               |             |   extruded, but will not be transformed (moved       |
|                 |               |             |                                                      |
|                 |               |             |   or scaled away from positions of original          |
|                 |               |             |                                                      |
|                 |               |             |   vertices); so the new vertices will be at the      |
|                 |               |             |                                                      |
|                 |               |             |   same positions as original ones. You may           |
|                 |               |             |                                                      |
|                 |               |             |   want to remove them with **Remove Doubles**        |
|                 |               |             |                                                      |
|                 |               |             |   node, or move them with another node.              |
|                 |               |             |                                                      |
|                 |               |             | This parameter is available in the N panel only.     |
|                 |               |             |                                                      |
+-----------------+---------------+-------------+------------------------------------------------------+
| **Height**      | Float         | 0.0         | Extrude factor as a portion of face normal length.   |
|                 |               |             |                                                      |
|                 |               |             | Default value of zero means do not extrude.          |
|                 |               |             |                                                      |
|                 |               |             | Negative value means extrude to the opposite         |
|                 |               |             |                                                      |
|                 |               |             | direction. This parameter can be also provided via   |
|                 |               |             |                                                      |
|                 |               |             | corresponding input. The input and parameter are     |
|                 |               |             |                                                      |
|                 |               |             | available only if **Mode** is set to **Normal**.     |
+-----------------+---------------+-------------+------------------------------------------------------+
| **Scale**       | Float         | 1.0         | Scale factor. Default value of 1 means do not scale. |
|                 |               |             |                                                      |
|                 |               |             | The input and parameter are                          |
|                 |               |             |                                                      |
|                 |               |             | available only if **Mode** is set to **Normal**.     |
+-----------------+---------------+-------------+------------------------------------------------------+
| **Mask Output** | Enumeration   | Out         | This defines which faces will be marked with 1 in    |
|                 |               |             |                                                      |
|                 |               |             | the **Mask** output. Several modes may be selected   |
|                 |               |             |                                                      |
|                 |               |             | together. The available modes are:                   |
|                 |               |             |                                                      |
|                 |               |             | * **Mask**. The faces which were masked out by       |
|                 |               |             |                                                      |
|                 |               |             |   the **Mask** input.                                |
|                 |               |             |                                                      |
|                 |               |             | * **In**. Inner faces of the extrusion, i.e. the     |
|                 |               |             |                                                      |
|                 |               |             |   same faces that are in the **ExtrudedPolys**       |
|                 |               |             |                                                      |
|                 |               |             |   output.                                            |
|                 |               |             |                                                      |
|                 |               |             | * **Out**. Outer faces of the extrusion; these are   |
|                 |               |             |                                                      |
|                 |               |             |   the same as in **OtherPolys** output, excluding    |
|                 |               |             |                                                      |
|                 |               |             |   faces that were masked out by **Mask** input.      |
+-----------------+---------------+-------------+------------------------------------------------------+

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Polygons**. All faces of resulting mesh.
- **ExtrudedPolys**. Only extruded faces of resulting mesh.
- **OtherPolys**. All other faces of resulting mesh.
- **Mask**. Mask for faces of the resulting mesh; which faces are selected
  depends on the **Mask Output** parameter.
- **FaceData**. List containing data items from the **FaceData** input, which
  contains one item for each output mesh face.

.. image:: https://user-images.githubusercontent.com/14288520/202865440-2bb41cad-b22c-49bc-8efe-0600fa2627e0.png
  :target: https://user-images.githubusercontent.com/14288520/202865440-2bb41cad-b22c-49bc-8efe-0600fa2627e0.png

.. image:: https://user-images.githubusercontent.com/14288520/200063766-001beaba-ad54-4ab4-aa55-ceff013989b5.png
  :target: https://user-images.githubusercontent.com/14288520/200063766-001beaba-ad54-4ab4-aa55-ceff013989b5.png

Example of usage
----------------

Extruded faces of sphere, extruding factor depending on Z coordinate of face:

.. image:: https://user-images.githubusercontent.com/14288520/200066554-e0edef9c-f45c-493d-a278-8b9c1c354062.png
  :target: https://user-images.githubusercontent.com/14288520/200066554-e0edef9c-f45c-493d-a278-8b9c1c354062.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* POW2: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Vector-> :doc:`Vector Out </nodes/vector/vector_out>`
* Matrix-> :doc:`Matrix Out </nodes/matrix/matrix_out_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Sort of cage:

.. image:: https://user-images.githubusercontent.com/14288520/200066985-dec9a695-6826-499f-a486-242789199028.png
  :target: https://user-images.githubusercontent.com/14288520/200066985-dec9a695-6826-499f-a486-242789199028.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

An example of **Matrix** mode usage:

.. image:: https://user-images.githubusercontent.com/14288520/200067832-443b8691-248b-4a26-90e9-fb6d78a5b306.png
  :target: https://user-images.githubusercontent.com/14288520/200067832-443b8691-248b-4a26-90e9-fb6d78a5b306.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Voronoi grid with each cell extruded by it's specific random matrix:

.. image:: https://user-images.githubusercontent.com/14288520/200071116-b875ffcc-61d9-4a9e-bb4b-365309a16afb.png
  :target: https://user-images.githubusercontent.com/14288520/200071116-b875ffcc-61d9-4a9e-bb4b-365309a16afb.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Spacial-> :doc:`Voronoi 2D </nodes/spatial/voronoi_2d>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Modifiers->Modifier Change-> :doc:`Fill Holes </nodes/modifier_change/holes_fill>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

FaceData sockets usage:

.. image:: https://user-images.githubusercontent.com/284644/71816744-69bdb980-30a5-11ea-94eb-5a3a459a9b0a.png
  :target: https://user-images.githubusercontent.com/284644/71816744-69bdb980-30a5-11ea-94eb-5a3a459a9b0a.png

Replay with new nodes:

.. image:: https://user-images.githubusercontent.com/14288520/200072683-6e2627b4-f5b1-420e-9922-ff03d57d3ec6.png
  :target: https://user-images.githubusercontent.com/14288520/200072683-6e2627b4-f5b1-420e-9922-ff03d57d3ec6.png

* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Analyzers-> :ref:`Select Mesh Elements (By Center and radius)<MODE_BY_CENTER_AND_RADIUS>`
* Analyzers-> :doc:`Wave Painter </nodes/analyzer/wave_paint>`
* Modifiers->Modifier Change-> :doc:`Flip Normals </nodes/modifier_change/flip_normals>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* List->List Main-> :doc:`List Math </nodes/list_main/func>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`