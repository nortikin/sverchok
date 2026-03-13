Objects in Lite
===============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c48180bc-b46a-4e64-8293-3133faacb3ec
  :target: https://github.com/nortikin/sverchok/assets/14288520/c48180bc-b46a-4e64-8293-3133faacb3ec

this node stores the object you pick up, and uses the stored information until you pick up the object manually again (kind of like a cache). This node is useful for storing scene objects (mesh based..) inside the iojson gists.

stores: verts/edges/polygons/material indices/matrix associated with **one object**.

the development thread is a good place to start understanding the node, then the code.
https://github.com/nortikin/sverchok/issues/1033