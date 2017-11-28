Object ID Point on Mesh MK2
===========================

Functionality
-------------
This node takes object (list of objects), and vector (list of vertices). If distance
from object surface to vector is less than *Max_Distance* parameter, then this
vertex will be projected onto object surface. Take a note, that global transformations
of objects is not count, so all information will be represent as if objects were
placed in (0,0,0) location, has (1,1,1) scale and (0,0,0) rotation.

Inputs
------
**Objects**
**point**
**Max_Distance**

Parameters
----------
**In Mode**
**Out Mode**

Outputs
-------
**success**
**Point_on_mesh**
**Normal_on_mesh**
**FaceINDEX**

Example of usage
----------------
