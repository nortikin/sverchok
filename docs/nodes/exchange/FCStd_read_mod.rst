FCStd Read Mode (Exchange)
==========================

Functionality
-------------

This node is an experimental modification of the original FCStd Read node.
This node reads one or more FCStd files, and 

- intputs: Labels can be used to narrow down which objects you wish retrieve from the files.
- outputs: the `obj.Shape` as a Solid socket, it also 
- outputs: `obj.FullName, obj.Name, obj.Label` in the Names socket.


Parameters
----------


- **global update**:

- **read body**:, 

- **read parts**:, 

- **tool parts**:, (todo)

- **inverse filter**:, this will produce only the items listed in the Filter labels.

- **merge linked**:, this will pull in objects that are linked from other FreeCAD files. ( `App::Link` )

- **read all**:, this "greedy mode" tells the node to ignore any filter labels and instead all possible shapes.

Inputs
------


Outputs
-------


Examples
--------
