Set_dataobject
==============

*destination after Beta:*

Functionality
-------------

*It works with a list of objects and a list of Values*

*multiple lists can be combined into one with the help of ListJoin node*

When there is only one socket Objects- performs ** (Object.str) **

If the second socket is connected Value- performs **(Object.str=Value)**

If the second socket is connected OutValue- performs **(OutValue=Object.str)**

*нельзя подключать оба Values сокета одновременно*

Inputs
------

This node has the following inputs:

- **Objects** 
- **values**


Outputs
-------

This node has the following outputs:

- **outvalues**

Examples of usage
-----------------
