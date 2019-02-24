Input Switch
------------

This node allows switching among an arbitrary number of sets of any type of inputs connected to the node.

Inputs
======

When first created, the node has a single **set** of input sockets (e.g. ["Alpha 1", "Alpha 2"]) and it will automatically create new sets of input sockets (e.g. ["Beta 1", "Beta 2"], ["Gamma 1", "Gamma 2"] etc) whenever any socket of the last set is connected, thus always allowing additional set of inputs to be connected to the node. Also, when all the sockets of the last connected set are disconnected the node will remove all but the last disconnected sets, thus always allowing one extra set of inputs to be connected to the node.

The node takes any type of inputs from the external nodes for its sets.

The sets are labeled based on the Greek alphabet letters from **Alpha** to **Omega** and the inputs within each set are suffixed with an increasing number starting from 1 (e.g. Alpha 1, Alpha 2, etc).

**Alpha #**
This first set of inputs always exists, no matter whether any of its input sockets are connected to or not.

**Beta #**
...
**Omega #**
These sets of inputs are created automatically, one at a time, only as the last set is connected.

Note: Be advised that while it is possible to connect any arbitrary mixture of input types to any sets (e.g. Vertex & Edge to the Alpha set, and Float & Color to Beta set etc) this combination of mixed sets of inputs may likely be of little to no use. This is because the output of the Input Switch node is likely going to be connected to a node tree that expects specific types of inputs, and therefore when changing the selection of the set, the Input Switch node will output a set of values that may be incompatible with the ones expected by the nodes it connects to. There are exceptions to this rule, of course, for instance: you can connect Vertex & Edge to Alpha set and Vertex & Poly to Beta set and have the output of the Input Switch node connected to a node that expects Vertex and EdgePoly as inputs. In this case, switching the set selection from Alpha to Beta will not break the node-tree since the final node can take either VE or VP as inputs.


Parameters
==========

The **Selected** parameter accepts single input values directly from the node or from an outside node. The value is sanitized to be bounded by the number N of the connected inputs (0, N-1). In fact, the value is converted via a modulo-N function to wrap around within (0, N-1) range for values larger than N. In other words, as the **Selected** value increases, the node essentially cycles through the connected sets as it picks one to be sent to the output.

+--------------+-------+---------+----------------------------------------------+
| Param        | Type  | Default | Description                                  |
+==============+=======+=========+==============================================+
| **Set Size** | Int   | 2       | The number of inputs in a set. [1][2][3]     |
+--------------+-------+---------+----------------------------------------------+
| **Selected** | Int   | 0       | The index of the selected set to output. [4] |
+--------------+-------+---------+----------------------------------------------+

Notes:
[1] : As the size of the set changes, the corresponding number of inputs are generated for each set with labels in increasing order (e.g. Lambda 1, Lambda 2, ... ).
[2] : When changing the set size, the existing connections of the input & output sockets to the outer nodes are being preserved, unless decreasing the set size renders some of the connected input & output sockets non-existent.
[3] : Currently the node limits the max set size to 9 since it is assumed it's unlikely the user may need sets larger than this. Not putting a limit on the size sets could end up creating very tall nodes.
[4] : The index 0 corresponds to the first set


Extra Parameters
================
**Show Separators**
The sets are separated by an empty socket / line to aid with visually differentiating between sets. The Property Panel has a toggle to turn the separators ON and OFF if desired (default is ON).

**Greek Labels**
The input sockets in each set have Greek letter names as labels. The Property Panel has a toggle to turn the labels from Greek to Latin if desired (default is Greek). The Latin labels are simply letters A to Z.


Outputs
=======

**Data #**
The number of Data output sockets is the same as the number of inputs in a set (set size) and they correspond to the inputs in the selected set (e.g. for Selected = 0 : Data 1 = Alpha 1, Data 2 = Alpha 2 .. etc)

When an output socket is connected the node will output the corresponding input in the selected set.

As the node is vectorized, whenever the **Selected** parameter is given a list of indices each Data output is a list of set input values corresponding to the given indices. (e.g. for Selected = [0, 1, 1] : Data 1 = [Alpha 1, Beta 1, Beta 1], Data 2 = [Alpha 2, Beta 2, Beta 2]).

Output Socket Types
===================
The types of the output sockets are automatically updated to correspond to the types of outer nodes connected to the the input sockets of the selected set. If the **Selected** socket is connected, however, the output sockets types will default to StringSockets (green) as the output would consist in this case of a combination of sets which may or may not have the same types for the corresponding inputs.

Macros
======
There is a macro that allows to automatically connect multiple selected nodes (e.g. generators) to a switch node and to a ViewerDraw node. To connect the nodes, first select the desired nodes, then search and select "> sw" (short for switch).

