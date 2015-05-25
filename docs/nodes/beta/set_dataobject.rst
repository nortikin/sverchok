Set_dataobject
==============

*destination after Beta:*

Functionality
-------------

*It works with a list of objects and a list of Values*

*multiple lists can be combined into one with the help of ListJoin node*

When there is only one socket Objects- performs **(Object.str)**

If the second socket is connected Values- performs **(Object.str=Value)**

If the second socket is connected OutValues- performs **(OutValue=Object.str)**

*Do not connect both the Values sockets at the same time*

Inputs
------

This node has the following inputs:

- **Objects** - only one list of python objects, like **bpy.data.objects** or **mathutils.Vector**
- **values** - only one list of any type values like **tupple** or **float** or **bpy.data.objects**


Outputs
-------

This node has the following outputs:

- **outvalues** - the list of values returned by the **str** expression for each object

Examples of usage
-----------------
