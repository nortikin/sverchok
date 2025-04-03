FCStd Read Mod (Exchange)
=========================

Functionality
-------------

This node is an experimental modification of the original FCStd Read node.
This node reads one or more FCStd files, and 

- inputs: Labels can be used to narrow down which objects you wish retrieve from the files.
- outputs: the `obj.Shape` as a Solid socket, it also 
- outputs: `obj.FullName, obj.Name, obj.Label` in the Names socket.


Parameters
----------


- **global update**:, when this is enabled, any updates upstream into this node will trigger an update and the file is read again. Useful if your file is changing externally.

- **read body**:, add ``PartDesign  Body`` items to the seek list

- **read part**:, add ``Part`` items to the seek list.

- **tool parts**:, (todo)

- **inverse filter**:, this will produce only the items listed in the Filter labels.

- **merge linked**:, this will pull in objects that are linked from other FreeCAD files. ( ``App  Link`` )

- **read all**:, this "greedy mode" tells the node to ignore any filter labels and instead all possible shapes.

- **unit factor**: selected object shapes will be scaled locally by this factor, unchanged if 1.0

Inputs
------

filepath, label1 filter, label2 filter

Outputs
-------

solids, names

Examples
--------

