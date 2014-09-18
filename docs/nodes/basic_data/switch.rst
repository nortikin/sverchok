Switch
=============

Functionality
-------------
[basic switch image]
Switches between to sets of inputs.

Inputs
------

+--------+--------------------------------------------------------------------------+
| Input  | Description                                                              |
+========+==========================================================================+
| state  | state that decides which set of sockets to use                           | 
+--------+--------------------------------------------------------------------------+
| T 0    | If state is false this socket is used                                    |
+--------+--------------------------------------------------------------------------+
| F 0    | If state is true this socket  used                                       |
+--------+--------------------------------------------------------------------------+


Parameters
----------


**Count**

Number of sockets in each set.

**state**

If set to 1 T sockets are used, otherwise the F socket are used.


Outputs
-------

Out 0 to Out N depending on count. Socket types are copied from first from the T set.

Examples
--------
[switch draw image]
Switching between a sphere and cylinder for drawing using switch node.
