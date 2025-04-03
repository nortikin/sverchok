Color Ramp
==========

.. image:: https://user-images.githubusercontent.com/14288520/189643169-e8791fe1-51b4-4508-8c0f-cb4691f4e117.png
  :target: https://user-images.githubusercontent.com/14288520/189643169-e8791fe1-51b4-4508-8c0f-cb4691f4e117.png

Functionality
-------------

This node map all the incoming values turning them to colors using the gradient you define manually through the interface.

Disclaimer
----------

This node creates a Blender material node-group and uses "Color Ramp" nodes to create and store the gradients.
Due the nature of this implementation the changing the gradient will not trigger the node update.
To update the output you need to click in the "Update" button or perform another action that triggers the node-tree update.

Inputs
------

This node has the following input:

* **Value**. The value to be used as an input for the function. The default value is 0.5.

Parameters
----------

* **Animate Node**. Update node on frame change
* **Update**. Update node
* **Use Alpha** Output RGBA or RGB colors


Outputs
-------

This node has the following outputs:

* **Color**. The result of the function application to the input value.


Examples
--------

Basic usage:

.. image:: https://user-images.githubusercontent.com/14288520/189643223-692b702c-1d7d-41d8-993f-76765d0ce2b8.png
  :target: https://user-images.githubusercontent.com/14288520/189643223-692b702c-1d7d-41d8-993f-76765d0ce2b8.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Viz-> :doc:`Texture Viewer </nodes/viz/viewer_texture>`