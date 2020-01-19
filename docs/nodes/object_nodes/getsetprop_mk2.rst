Get Property / Set Property
===========================

Functionality
-------------

These nodes can be used to control almost anything in Blender once you know the python path. For instance if you want to ``Set`` the location of a scene object called ``Cube``, the python path is ```bpy.data.objects['Cube'].location```.

By default these nodes don't expose their input / output sockets, but they will appear if the node was able to find a compatible property in the path you provided.  If you are trying a path and it's not wortking and no socket is appearing, please let us know in the issue tracker and we'll try to fix it. 

The Socket types that the node generates depend on the kind of data path you gave it. It knows about Matrices and Vectors and Numbers etc..

There are also convenience aliases. Instead of writing ```bpy.data.objects['Cube'].location``` you can write ```objs['Cube'].location``` . The aliases are as follows::

    aliases = {
        "c": "bpy.context",
        "C" : "bpy.context",
        "scene": "bpy.context.scene",
        "data": "bpy.data",
        "D": "bpy.data",
        "objs": "bpy.data.objects",
        "mats": "bpy.data.materials",
        "M": "bpy.data.materials",
        "meshes": "bpy.data.meshes",
        "texts": "bpy.data.texts"
    }  

useful info for path lookups:

    Many properties can be right-clicked and have the option to "copy data path" (to your clipboard for pasting), this can help reduce some console probing / documentation reading. Usually, however, you will need to provide the start of the path yourself. For example: if you copy the path one of the Color properties in a ColorRamp of a shader, then following will be be copied to the clipboard: `node_tree.nodes["ColorRamp"].color_ramp.elements[0].color` , this is not the full path, you will need to add the path to the `node_tree`, something like `bpy.data.materials['Material'].node_tree.nodes["ColorRamp"].color_ramp.elements[0].color`, then the node will know what you're intention is.


Input
-----

In ``Set`` mode

+-----------------+--------------------------------------------------------------------------+
| Input           | Description                                                              |
+=================+==========================================================================+
| Dynamic         | Any of the Sverchok socket types that make sense                         | 
+-----------------+--------------------------------------------------------------------------+

Output
------

In ``Get`` mode

+-----------------+--------------------------------------------------------------------------+
| Output          | Description                                                              |
+=================+==========================================================================+
| Dynamic         | Any of the Sverchok socket types that make sense                         | 
+-----------------+--------------------------------------------------------------------------+



Parameters
----------

The only parameter is the python path to the property you want to set or get. Usually we search this manually using Blender's Python console.


Limitations
-----------

Because this is a generic set/get nodeset, the backend is relatively heavy on logic to provide the simplest user interface. This means sometimes we'll encounter new properties that aren't yet matched in our internal logic, and won't result in a socket or expected behaviour. Let us know when you find such properties and we can adjust our code. 

When piping values into our nodetree from a property of a material or some other Blend object, that value will not update automatically in the Sverchok nodetree until the nodetree is told specifically to update. You can updat the nodetree manually several ways, but the handiest is usually a simple framechange (kb left/right). Another way is to have animation running.


Examples
--------


.. image:: https://cloud.githubusercontent.com/assets/619340/11468741/2a1aa3c4-9752-11e5-85d9-13cd8478c0d2.png

.. image:: https://cloud.githubusercontent.com/assets/619340/11468834/a9eaa342-9752-11e5-8ea9-76a0b678c2a4.png

Using aliases ``objs`` instead of ``bpy.data.objects``

.. image:: https://cloud.githubusercontent.com/assets/619340/11468901/1af0f73a-9753-11e5-8fb3-55b8975178bb.png
