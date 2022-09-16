Obj instancer
=============

.. image:: https://user-images.githubusercontent.com/14288520/190443161-564c19ea-fc8e-401b-9828-8c756f3061fb.png
  :target: https://user-images.githubusercontent.com/14288520/190443161-564c19ea-fc8e-401b-9828-8c756f3061fb.png

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
| Random name     | Generates random name with random letters                                |
+-----------------+--------------------------------------------------------------------------+
| Show objects    | Show / hide objects in viewport.                                         |
+-----------------+--------------------------------------------------------------------------+
| Selectable obj  | Make objects selectable / unselectable                                   |
+-----------------+--------------------------------------------------------------------------+
| Render objects  | Show / hide objects for render engines                                   |
+-----------------+--------------------------------------------------------------------------+
| Select          | Select every object in 3dview that was created by this Node              |
+-----------------+--------------------------------------------------------------------------+
| Collection      | Collection where to put instances                                        |
+-----------------+--------------------------------------------------------------------------+
| Full copy       | All properties related with given objects will be copied into instances  |
|                 | this property can be used for copying modifier stack for example         |
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

.. image:: https://user-images.githubusercontent.com/14288520/190443212-7b379629-c1dc-41ba-bf70-052aec19d4b0.png
  :target: https://user-images.githubusercontent.com/14288520/190443212-7b379629-c1dc-41ba-bf70-052aec19d4b0.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Math </nodes/matrix/matrix_math>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`