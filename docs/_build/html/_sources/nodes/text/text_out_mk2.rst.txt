Text Out
========

Functionality
-------------

This node takes incoming socket data, and write the appropriate file to bpy.data.texts. You can pick various formatting conventions. Effectively this node mirrors the features of **Text In**

- You must make the textfile first in bpy.data.texts
- for large data you may want to stop showing the TextEditor while updating all the time
- The autodump is useful, but can be switched off.
- the various modes ( CSV, Sverchok, Json) all output data that is custom to the implementation, any frequent user/consumer of these formats will know what to do. Much information about json/csv exists online.

https://github.com/nortikin/sverchok/issues/1954
https://github.com/nortikin/sverchok/pull/1956

.. image:: https://user-images.githubusercontent.com/619340/78012659-99e3c400-7345-11ea-9a98-e7a30994bc98.png