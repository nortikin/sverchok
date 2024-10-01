A Number
========

.. image:: https://github.com/user-attachments/assets/25848436-3f59-448b-80e4-a17ba775b308
  :target: https://github.com/user-attachments/assets/25848436-3f59-448b-80e4-a17ba775b308

Functionality
-------------

This node lets you output a number, either Int or Float. It also lets you set the Min and Max of the slider to ensure that the node never outputs beyond a certain range. 


Warning
-------

Currently: 

The node will pass any input directly to the output, it will not first recast ints to floats if you feed it integers while the node is in Integer mode. The reverse is also true. When the node's input socket is connected it will not limit the values of the incoming data. (you probably want to use a Remap Range node in that case anyway)


Inputs & Parameters
-------------------

**float or integer**  

Extended parameters
-------------------

**Show Limits** - boolean switch will show the Min and Max sliders on the UI when pressed. Unpressed the node only shows the choice between Integer and Float mode.


Outputs
-------

**float or integer** - only one digit. when unlinked

3D panel
--------

The node can show its properties on 3D panel. 
For this parameter `to 3d` should be enabled, output should be linked and input should not be linked.
After that you can press `scan for props` button on 3D panel for showing the node properties on 3D panel.

.. image:: https://github.com/user-attachments/assets/c4d37081-fae1-4acd-971b-dec5fc3671cb
  :target: https://github.com/user-attachments/assets/c4d37081-fae1-4acd-971b-dec5fc3671cb

Examples
--------

see https://github.com/nortikin/sverchok/pull/1450 for examples

.. image:: https://user-images.githubusercontent.com/14288520/188992296-6c13d18d-93d1-48cb-8614-4c3ca687be6a.gif
  :target: https://user-images.githubusercontent.com/14288520/188992296-6c13d18d-93d1-48cb-8614-4c3ca687be6a.gif

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`