Object ID Filter
=======================

Functionality
-------------
This node takes list of strings, containing object IDs, and filters them by name
(default parameter) or by custom **mask**. Then returns filtered list of object ID strings.

Inputs
------
**Objects** - List of strings, containing object ID, which looks like
 *bpydata.objects['Object Name']*

**mask** - custom mask to filter input list

Parameters
----------

**write name here** - Node will use Object name as mask. It will take all objects
with the same name from input list, and mask it, creating two new lists:

**Object(have)** - list that contains only objects with provided name

**Object(not)** - list that contains all objects except ones with provided name

Outputs
-------

**Objects(have)** - new list, that contain only masked elements.

**Objects(not)** - new list, that contain all elements, except masked ones.

Example of usage
----------------
