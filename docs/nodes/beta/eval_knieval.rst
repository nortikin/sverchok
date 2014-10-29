Eval Knieval
================

*destination after Beta: control (or basic data..but preferably a new ``control`` menu)*


Functionality
-------------

This is a massively powerful node, it allows you to control pretty much anything in Blender with minimal admin.
The node has 3 main modes (``Set, Get, and Do``). Do has 3 of its own modes (``eval_text, read_text, do_function``).


+-----------+-------------+---------------------------------------+
| main mode | minor mode  | quick info                            | 
+===========+=============+=======================================+
| Set       |             | ``path.to.prop`` (set from Sverchok)  |
+-----------+-------------+---------------------------------------+
| Get       |             | ``path.to.prop`` (take into Sverchok) | 
+-----------+-------------+---------------------------------------+
| Do        | eval_text   | ``eval_text(a, b, [True])``           |
+-----------+-------------+---------------------------------------+
|           | read_text   | ``read_text(a, [True])``              |
+-----------+-------------+---------------------------------------+
|           | do_function | ``do_function(a) with x``             | 
+-----------+-------------+---------------------------------------+

Inputs & Parameters & Outputs
-----------------------------

Heavily depending on which mode you have switched to. 

**Set and Get**

Set takes only an input, while Get only makes an output. Both have convenience local aliases.
::
    c = bpy.context
    scene = c.scene
    data = bpy.data
    objs = data.objects
    mats = data.materials
    meshes = data.meshes
    texts = data.texts

The scheme for both is the same, and the node will figure out in the background what socket to use 
depending on the type of data you reference::

    """
    - SET:  `path.to.prop`
    - GET:  `path.to.prop`
    """
    # you might do something like this to set the cube location
    # depending on if you have Set or Get it will make an input or output socket
    objs['Cube'].location

    # more



**eval_text**

``eval_text(function_text, out_text, update=True)``

+---------------+---------------------------------------------------------------------------------+
| parameter     | description                                                                     | 
+===============+=================================================================================+
| function_text | a reference to a file inside blender. This text should be initiated outside     |
|               | of blender or made external by saving and loading. The content of this file is  |
|               | what writes to the out_text.                                                    |
+---------------+---------------------------------------------------------------------------------+
| out_text      | the internal text file to read from. The content of which might be changing on  |
|               | each update.                                                                    |
+---------------+---------------------------------------------------------------------------------+
| update        | this parameter isn't very useful at the moment, but keep it to True if you      | 
|               | want to update the content of the internal text file. Else only the external    |
|               | file will be read.                                                              |
+---------------+---------------------------------------------------------------------------------+


**do_function**

This function aims to facilitate the repeated execution of a python file
located inside Blender. Similar to Scripted Node but with the restriction
that it has one input by design. Realistically the input can be an array,
and therefore nested with a collection of variables.

The python file to exec shall be specified in the eval string like so:

    ``do_function('file_name.py') with x``

Here x is the value of the input socket, this will automatically be in the
scope of the function when EK calls it. First it is executed in a
try/except scenario, and if that went OK then the next update is without
try/except.

The content of file_name.py can be anything that executes, function or
a flat file. The following convenience variables will be present.
::
    c = bpy.context
    scene = c.scene
    data = bpy.data
    objs = data.objects
    mats = data.materials
    meshes = data.meshes
    texts = data.texts


Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/7894950/4715836/5513ae5c-5902-11e4-8f05-40520d57476a.png

Notes
-----

str datatype not currently supported, but can be easily.
