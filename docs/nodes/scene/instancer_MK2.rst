Instancer MK2
=============

Functionality
-------------

This node takes one or more objects (which will be called 'blueprints' from here) and creates instances of said blueprints with the position, rotation and scale values of the given matrices. All instances share the blueprint's mesh(es). Additionally, the node can automatically remove the blueprint after processing it, allowing for integration into the node workflow.

Inputs
------

+-----------------+--------------------------------------------------------------------------+
| Input           | Description                                                              |
+=================+==========================================================================+
| objects         | The blueprint object or objects                                          |
+-----------------+--------------------------------------------------------------------------+
| Matrices        | full on 4*4 transform matrices defining the instance's placements        |
+-----------------+--------------------------------------------------------------------------+

Parameters
----------

+-----------------+--------------------------------------------------------------------------+
| Properties      | Description                                                              |
+=================+==========================================================================+
| Update          | Switches processing of the node on and off.                              |
|                 | The duplication is set to VERTS.                                         | 
+-----------------+--------------------------------------------------------------------------+
| Delete Source   | When set, removes the blueprint(s) after processing, leaving only the    |
|                 | instanced objects in place.                                              |
|                 | Intended use is integration in a node tree workflow.                     |
+-----------------+--------------------------------------------------------------------------+
| Base Name       | The base name the instances will have. Actual names will be patterned    |
|                 | like Base.0001, Base.0002, and so on, in a collection named 'Base'       |
+-----------------+--------------------------------------------------------------------------+

Caveats
-------

Using the output of the object picker node and switching on 'Delete Source' deletes the source object from the scene. Use with caution.

This node produces as many instances as there are matrices given in the input. With more than one blueprint, the resulting instances will 'loop' through the given blueprints until the input of matrices is exhaused. For example, three blueprints and ten matrices will still yield ten instances, the first nine instances being sets of all three instanced blueprints, and the tenth being an instance of the first blueprint again.


