Split Faces
===========

.. image:: https://user-images.githubusercontent.com/14288520/199610547-42161738-df2e-4f0f-beb5-db668f72f7d6.png
  :target: https://user-images.githubusercontent.com/14288520/199610547-42161738-df2e-4f0f-beb5-db668f72f7d6.png

Functionality
-------------

This node splits NGon faces of the input mesh into smaller faces by one of two available rules:

* Split non-planar faces. In this mode, it will split NGon faces, that are not
  planar (flat), into smaller planar (flat) faces. There is adjustable limit of
  what exactly faces should be considered non-planar. For example, if the angle
  between two parts of the face is less than 1 degree, we can consider it
  planar.
* Split concave faces. This will split faces that are not convex **polygons**.
  Please note that this **does not** mean that it will split faces so that the
  resulting mesh will make convex volume - it only checks for convex polygons.

.. image:: https://user-images.githubusercontent.com/14288520/199610555-23dc58ae-10ac-48f9-9713-e87fc2b8d587.png
  :target: https://user-images.githubusercontent.com/14288520/199610555-23dc58ae-10ac-48f9-9713-e87fc2b8d587.png

Inputs
------

This node has the following inputs:

- **Vertices**. This input is mandatory.
- **Edges**. 
- **Faces**. This input is mandatory.
- **FaceMask**. The mask for faces which should be considered. By default, all
  faces are considered.
- **MaxAngle**. Maximum angle (in degrees) between parts of the face for it to
  be considered planar. The default value is 5 degrees. This input can also be
  specified as parameter. This input is only visible when **Mode** parameter is
  set to **Non-planar**.
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.

Parameters
----------

This node has the following parameters:

- **Mode**. This defines which faces should be split. Available values are
  **Non-planar** and **Concave**. The default value is **Non-planar**.

Outputs
-------

This node has the following outputs:

- **Vertices**. Output mesh vertices.
- **Edges**. Output mesh edges.
- **Faces**. Output mesh faces.
- **FaceData**. List containing data items from the **FaceData** input, which
  contains one item for each output mesh face.

See also
--------

* Modifiers->Modifier Change-> :doc:`Triangulate Mesh </nodes/modifier_change/triangulate>`

Examples of usage
-----------------

Simple example of splitting non-planar faces:

.. image:: https://user-images.githubusercontent.com/14288520/199611523-ab25ea6b-f03d-4974-9a28-c3d2d17cabf9.png
  :target: https://user-images.githubusercontent.com/14288520/199611523-ab25ea6b-f03d-4974-9a28-c3d2d17cabf9.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Spatial-> :doc:`Concave Hull </nodes/spatial/concave_hull>`
* Modifiers->Modifier Make-> :doc:`Dual Mesh </nodes/modifier_make/dual_mesh>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

An example of splitting concave faces:

.. image:: https://user-images.githubusercontent.com/14288520/199614376-e10cbdcb-1f21-4cfe-b816-dc12d4dacab0.png
  :target: https://user-images.githubusercontent.com/14288520/199614376-e10cbdcb-1f21-4cfe-b816-dc12d4dacab0.png

* Generator->Generatots Extended-> :doc:`Hilbert </nodes/generators_extended/hilbert>`
* Modifiers->Modifier Make-> :doc:`Offset Line </nodes/modifier_make/offset_line>`
* Modifiers->Modifier Change->Limited Dissolve (TODO)
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`