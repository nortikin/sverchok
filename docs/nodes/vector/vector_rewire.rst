Vector Rewire
=============

.. image:: https://user-images.githubusercontent.com/14288520/189385948-68ae2146-49f1-41e3-acd7-d75b874d2042.png
  :target: https://user-images.githubusercontent.com/14288520/189385948-68ae2146-49f1-41e3-acd7-d75b874d2042.png

Functionality
-------------

Use this node to swap Vector components, for instance pass X to Y (and Y to X ). Or completely filter out a component by switching to the Scalar option. it will default to *0.0* when the Scalar socket is unconnected, when connected it will replace the component with the values from the socket. If the content of the Scalar input lists don't match the length of the Vectors list, the node will repeat the last value in the list or sublist (expected Sverchok behaviour).

.. image:: https://cloud.githubusercontent.com/assets/619340/22211977/3bb60a64-e18f-11e6-82ca-5afac681b195.png
  :target: https://cloud.githubusercontent.com/assets/619340/22211977/3bb60a64-e18f-11e6-82ca-5afac681b195.png
  :alt: with vector rewire

* Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Inputs
------

* **Vectors** - Any list of Vector/Vertex lists
* **Scalar** - value or series of values, will auto repeat last valid value to match Vector count.


Outputs
-------

* **Vector** - Vertex or series of vertices

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/189385973-5431c3a0-fc22-4893-9f75-86a97dd15f6d.png
  :target: https://user-images.githubusercontent.com/14288520/189385973-5431c3a0-fc22-4893-9f75-86a97dd15f6d.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/189386007-b01037a4-a855-49fa-a36f-1d94d151bd4f.gif
  :target: https://user-images.githubusercontent.com/14288520/189386007-b01037a4-a855-49fa-a36f-1d94d151bd4f.gif

.. image:: https://user-images.githubusercontent.com/14288520/189389853-0101ef1d-9cd9-4300-a108-1b26ad7a81ad.gif
  :target: https://user-images.githubusercontent.com/14288520/189389853-0101ef1d-9cd9-4300-a108-1b26ad7a81ad.gif

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`