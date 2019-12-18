Split Faces
===========

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

