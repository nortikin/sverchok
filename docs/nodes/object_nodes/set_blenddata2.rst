Object ID Set
=============

Functionality
-------------
This node takes list of strings, containing object IDs, and changes selected parameter
of every object in the list.

Inputs
------
**Objects** - List of strings, containing object ID, which looks like.
 *bpydata.objects['Object Name']*

**values** - New value to pass to object parameter.

Parameters
----------
**delta_transfrom** - Default value, but there can be many more other parameters,
like for example *location.x*. To get full list of available parameters its possible
to use **Scripted Node Lite** and *ID dir function* template.

Outputs
-------
**outvalues**

**Objects** - same objects as the input.

Example of usage
----------------
