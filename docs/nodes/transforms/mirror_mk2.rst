Mirror
======

Functionality
-------------

This node mirrors vertices relative to a specified point, axis or plane.
Several ways of specifying the mirroring center are available.

Inputs
------

This node has the following inputs:

* **Vertices**. Vertices to be mirrored.
* **Vert A**. A vertex defining the mirroring center. It has different meanings
  depending on the **Mode** parameter:

   - In **Vertex** mode, this defines the point other vertices will be mirrored around.
   - In **Axis by 2 points** mode, this defines the first point of the
     mirroring axis. Used together with **Vert B** input.
   - In **Axis by point and direction** mode, this defines the point used to
     define the axis. Used together with **Direction** input.
   - In **Plane by normal and point** mode, this defines the point used to
     define the plane. Used together with **Normal** input.
   - It is not visible in the other modes.

   The default value is `(0, 0, 0)`. This input can also be specified as a parameter.

* **Vert B**. The second point of the mirroring axis. Used together with **Vert
  A** input. This input is only visible when **Mode** parameter is set to
  **Axis by 2 points**. The default value is `(1, 0, 0)`. This input can also
  be specified as a parameter.
* **Plane**. The matrix used to define the mirroring plane. XOY plane of that
  matrix will be used. The default value is identity matrix, which means
  mirroring around the XOY plane. This input is ony visible when **Mode**
  parameter is set to **Plane by matrix**.
* **Normal**. Normal vector of the mirroring plane. Used together with **Vert
  A** input. The default value is `(0, 0, 1)`. This input is visible only when
  **Mode** parameter is set to **Plane by normal and point**.
* **Direction**. Mirroring axis direction. Used together with **Vert A** input.
  The default value is `(0, 0, 1)`. This input is only visible when **Mode**
  parameter is set to **Axis by point and direction**.

Parameters
----------

This node has the following parameters:

- **Mode**. Available values are:
   - **Vertex** - mirror around the point specified by the **Vert A** input.
   - **Axis by 2 points** - mirror around the axis defined by **Vert A** and
     **Vert B** inputs.
   - **Coordinate axis** - mirror around X, Y or Z coordinate axis.
   - **Axis by point and direction** - mirror around the axis defined by **Vert
     A** and **Direction** inputs.
   - **Plane by matrix** - mirror around the plane defined by **Plane** input.
   - **Plane by normal and point** - mirror around the plane defined by **Vert
     A** and **Normal** inputs.
   - **Coordinate plane** - mirror around XOY, YOZ or XOZ coordinate plane.
- **Coordinate axis**. This is visible only when **Mode** parameter is set to
  **Coordinate axis**. The available values are X, Y and Z. The default value
  is Z.
- **Coordinate plane**. This is visible only when **Mode** parameter is set to
  **Coordinate plane**. The available values are XY, YZ and XZ. The default
  value is XZ.

Outputs
-------

This node has the following output:

- **Vertices**. The mirrored vertices.

Example of usage
----------------

Suzanne mirrored around some random plane:

.. image:: https://user-images.githubusercontent.com/284644/70866839-782a2100-1f90-11ea-9682-9a7d66acc7bb.png

