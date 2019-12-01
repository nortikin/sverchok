Framework node
==============

Functionality
-------------

This node generates framework / construction carcass-like structure (fr. ferme)
from a flat mesh that defines construction profile. That profile can be
extruded along one of coordinate axis ("orientation axis"), or along custom
curve.

In custom curve mode, to generate framework's lengthswise crossbars, each
vertex of profile mesh is extruded along the specified curve. One can provide
specific curve for each profile mesh vertex.

In "orientation axis" mode (the default one), to generate framework's
lengthswise crossbars, each vertex of profile mesh is extruded along the
specified axis. Number of vertices to generate from one vertex of profile mesh
can be specified for each vertex.

Generated vertices are then connected by transverse edges. Each vertex is
connected to several vertices of the neighbour lengthwise crossbars. Number of
transverse edges to originate from each vertex, and maximum possible length of
transverse edge, can be specified for each vertex of profile mesh.

If number of transverse edges and maximum length of transverse edge is high
enough, then transverse edges can intersect, so more complex structure is generated.

NB: to generate "Frame" output, standard Blender's "fill holes" function is
used. It can behave somewhat unexpected when the vertex of profile mesh is
connected to more than two other vertices.

Inputs
------

This node has the following inputs:

* **Vertices**. Vertices of the profile mesh. This input is mandatory.
* **Edges**. Edges of the input mesh. This input is mandatory.
* **Curve**. The curve along which the vertices of profile mesh should be
  extruded in order to make lengthswise crossbars. This input consumes a list
  of lists of vertices - one list of vertices per each vertex of the profile
  mesh. This input is visible and is mandatory in case the **Z Mode** parameter
  is set to **Curve**.
* **Offset**. Offset of the first vertex in the lengthwise crossbar, in units
  of **Step** input. This input can consume a list of values, one value per
  profile mesh vertex. This input can be also provided as a parameter. The
  default value is 0.0. This input is visible only when **Z Mode** parameter is
  set to **Axis**.
* **Step**. Step of vertices generation along the lengthswise crossbars (i.e.
  the length of lengthswise edges). This input can consume a list of values,
  one value per profile mesh vertex. This input can be also provided as a
  parameter. The default value is 1.0. This input is visible only when **Z
  Mode** parameter is set to **Axis**.
* **Connections**. Maximum number of neighbour lengthwise crossbar vertices
  each vertex can be connected to. This input can consume a list of values, one
  value per profile mesh vertex. This input can be also provided as a
  parameter. The default value is 1.
* **Max Distance**. Maximum length of the traverse edges. This input can
  consume a list of values, one value per profile mesh vertex. This input can
  be also provided as a parameter. The default value is 1.
* **Count**. Number of vertices on the lengthwise crossbars to generate. This
  input can consume a list of values, one value per profile mesh vertex. This
  input can be also provided as a parameter. The default value is 10. This
  input is visible only if **Len Mode** parameter is set to **Count**.
* **Length**. Length of lengthwise crossbars. This input can consume a list of
  values, one value per profile mesh vertex. This input can be also provided as
  a parameter. The default value is 10. This input is visible only if **Len
  Mode** parameter is set to **Length**.  

Parameters
----------

This node has the following parameters:

* **Z Mode**. Mode of lengthwise crossbars generation. The following values are available:

  - **Axis**. The vertices of the profile mesh will be extruded along one of the coordinate axis.
  - **Curve**. The vertices of the profile mesh will be extruded along the specified curve.

  The default value is **Axis**.

* **Orientation axis**. The axis along which the vertices of profile mesh
  should be extruded. The available values are X, Y, and Z. The default value
  is Z. This parameter is visible only when the **Z Mode** parameter is set to
  **Axis**.
* **Len Mode**. The mode of lengthwise crossbars lengths definition. The available values are:

   - **Count**. Crossbars length is defined by the value of **Step** input
     multiplied by the value of the **Count** input, plus the value of the
     **Offset** input multiplied by the value of the **Step** input.
   - **Length**. Crossbars length is defined by the value of the **Length** input.

   The default value is **Count**.

* **Basis**. Whether to generate additional vertices to make all lengthwise
  crossbars of the same length. This parameter is visible only if the **Z
  Mode** parameter is set to **Axis**. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Vertices**. Output mesh vertices.
* **Edges**. Output mesh edges.
* **Faces**. Output mesh faces.

Examples of usage
-----------------


