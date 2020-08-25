Obj instancer
=============

.. image:: https://user-images.githubusercontent.com/28003269/90861816-71647100-e39d-11ea-80de-5591a991a3fe.png

Functionality
-------------

This node takes one or more objects and creates instances of the object 
with the same data block (mesh, light, camera, ...) and with the position,
rotation and scale values of the given matrices.

This node can't work at least with next data blocks: metaballs, images, force fields.

Category
--------

Viz -> Obj instanser

Inputs
------

+-----------------+--------------------------------------------------------------------------+
| Input           | Description                                                              |
+=================+==========================================================================+
| objects         | Blender objects                                                          |
+-----------------+--------------------------------------------------------------------------+
| Matrices        | full on 4*4 transform matrices defining the instance's placements        |
+-----------------+--------------------------------------------------------------------------+


Outputs
-------

+-----------------+--------------------------------------------------------------------------+
| Input           | Description                                                              |
+=================+==========================================================================+
| objects         | The resulting instanced objects                                          |
+-----------------+--------------------------------------------------------------------------+


Parameters
----------

+-----------------+--------------------------------------------------------------------------+
| Properties      | Description                                                              |
+=================+==========================================================================+
| Live            | Switches processing of the node on and off.                              |
+-----------------+--------------------------------------------------------------------------+
| Base Name       | The base name the instances will have. Naming logic will be as           |
|                 | Blender gives names objects                                              |
+-----------------+--------------------------------------------------------------------------+
| Show objects    | Show / hide objects in viewport.                                         |
+-----------------+--------------------------------------------------------------------------+
| Selectable obj  | Make objects selectable / unselectable                                   |
+-----------------+--------------------------------------------------------------------------+
| Render objects  | Show / hide objects for render engines                                   |
+-----------------+--------------------------------------------------------------------------+
| Collection      | Collection where to put instances                                        |
+-----------------+--------------------------------------------------------------------------+
| Full copy       | All properties related with given objects will be copied into instances  |
|                 | this property can be used for coping modifier stack for example          |
+-----------------+--------------------------------------------------------------------------+

Caveats
-------

This node produces as many instances as there are matrices given in the input. 
With more than one object, the resulting instances will 'loop' through the given objects
until the input of matrices is exhausted. For example, three objects and ten matrices 
will still yield ten instances, the first nine instances being sets of all three instanced objects, 
and the tenth being an instance of the first object again.

Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/90870285-6e23b200-e3aa-11ea-9b73-abbf0c0f25de.png