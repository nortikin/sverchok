List Input
==========

.. image:: https://user-images.githubusercontent.com/14288520/189119138-868bf887-8eb0-4839-8cf2-9664388bcb35.png
  :target: https://user-images.githubusercontent.com/14288520/189119138-868bf887-8eb0-4839-8cf2-9664388bcb35.png

Functionality
-------------

Provides a way to create a flat list of *Integers*, *Floats*, or *Vectors*. 
The length of the list is hardcoded to a maximum of **32** elements for integer or float and **10** vectors,
we believe that if you need  more then you should use a Text File

.. image:: https://user-images.githubusercontent.com/14288520/189121461-11d4ff38-7142-4da7-884a-10bf8e3d4915.png
  :target: https://user-images.githubusercontent.com/14288520/189121461-11d4ff38-7142-4da7-884a-10bf8e3d4915.png

and the :doc:`Text->Text In+ </nodes/text/text_in_mk2>` node.


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
    :target: https://user-images.githubusercontent.com/28003269/70140711-c7c63e00-16ae-11ea-9266-e4f24586e448.png
    

.. image:: https://user-images.githubusercontent.com/14288520/189119167-e08360ab-fd27-47d1-947d-1c0628bdac8a.png 
  :target: https://user-images.githubusercontent.com/14288520/189119167-e08360ab-fd27-47d1-947d-1c0628bdac8a.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`