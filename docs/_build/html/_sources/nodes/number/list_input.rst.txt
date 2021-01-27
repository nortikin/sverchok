List Input
==========

Functionality
-------------

Provides a way to create a flat list of *Integers*, *Floats*, or *Vectors*. 
The length of the list is hardcoded to a maximum of **32** elements for integer or float and **10** vectors,
we believe that if you need  more then you should use a Text File and the Text In node.

Parameters
----------

The value input fields change according to the Mode choice.


Output
-------

A single *flat* ``list``.

3D panel
--------

The node can show its properties on 3D panel. 
For this parameter `to 3d` should be enabled, output should be linked.
After that you can press `scan for props` button on 3D panel for showing the node properties on 3D panel.

Examples
--------

Useful when you have no immediate need to generate such lists programmatically.

.. image:: https://user-images.githubusercontent.com/28003269/70140711-c7c63e00-16ae-11ea-9266-e4f24586e448.png
