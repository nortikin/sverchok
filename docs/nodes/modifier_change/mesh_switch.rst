Mesh Switch
-----------

This node allows to switch among an arbitrary number of mesh inputs (verts, edges, polys) connected to the node.

Inputs
======

**Verts A**
Takes a Vertex list from outside nodes.

**EdgePolys A**
Takes either an Edge or a Poly list from outside nodes.

The node starts with one set of mesh input sockets ("Verts A" and "EdgePolys A") and will create new mesh sockets whenever the last Verts input socket is connected, thus allowing additional mesh inputs to be connected to the node. Whenever the last Verts input socket is disconnected the node will remove the all disconnected inputs at the end of the input list except the last disconnected set of inputs, thus always allowing one extra mesh to be connected to the node.

Parameters
==========

The **Selected** parameter accepts single input values directly from the node or from an outside node. The value is sanitized to be bounded to the range of the connected inputs (0, N-1) and it is also converted via a modulo-N function to wrap around within (0, N-1) range for values larger than N. In other words, as the **Selected** value increases the node essentially cycles through the connected meshes.

+---------------+---------+---------+-------------------------------------------------+
| Param         | Type    | Default | Description                                     |
+===============+=========+=========+=================================================+
| **Selected**  | Int     | 0       | The index of the selected mesh to output.       |
+---------------+---------+---------+-------------------------------------------------+

Outputs
=======

**Verts**
**EdgePolys**

When an output socket is connected the node will output the mesh corresponding to the selected index.

