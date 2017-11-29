Object ID Sort
==============

Functionality
-------------
This node sorts input list based on selected parameter, then returns sorted list.

Inputs
------
**Objects** - list of Blender Objects to sort.

**CustomValue**

Parameters
----------
**location.x** - Default value, but there can be many more other parameters,
like for example *rotation_euler*. To get full list of available parameters its possible
to use **Scripted Node Lite** and *ID dir function* template.

Outputs
-------
**Objects** - sorted list of Blender Objects

Example of usage
----------------
