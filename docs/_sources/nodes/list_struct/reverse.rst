List Reverse
============

.. image:: https://user-images.githubusercontent.com/14288520/187989090-d505d1bd-601d-47bc-bfeb-4b7026949a30.png
  :target: https://user-images.githubusercontent.com/14288520/187989090-d505d1bd-601d-47bc-bfeb-4b7026949a30.png

Functionality
-------------

Reverse items from list based on index. It should accept any type of data from Sverchok: Vertices, Strings (Edges, Polygons) or Matrix.

Inputs
------

Takes any kind of data.

Parameters
----------


* **Level:** Set the level at which to observe the List.

Outputs
-------

Depends on incoming data and can be nested. Level 0 is top level (totally zoomed out), higher levels get more granular (zooming in) until no higher level is found (atomic). The node will just reverse the data at the level selected.

Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/187989115-28629d0a-d37b-4d17-9ac5-82ac7cf4dad4.png
  :target: https://user-images.githubusercontent.com/14288520/187989115-28629d0a-d37b-4d17-9ac5-82ac7cf4dad4.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Zip </nodes/list_main/zip>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

In this example the node reverse a list a integers