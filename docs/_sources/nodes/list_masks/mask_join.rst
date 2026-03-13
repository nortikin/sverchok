List Mask Join (In)
===================

.. image:: https://user-images.githubusercontent.com/14288520/189611716-899bd122-6af1-4025-bc6f-62b2ccff5ade.png
  :target: https://user-images.githubusercontent.com/14288520/189611716-899bd122-6af1-4025-bc6f-62b2ccff5ade.png

Functionality
-------------

This node use the mask list i.e. 1,0,0,0 as switch to mix two data list together.

**0** means false, an item from the **Data False** will be appended to the output data;

**1** will be considered as true (actually any value that evaluate as true in python), an item from the **Data True** will be appended to the output data. If the mask list, the **Data True**, and the **Data False** are not of the same length, how to match the inputs can be determined via the list match mode in the N panel.

Length of mask list affect output because every item (without Choice activated) corresponding to Inputs several times.

The main design reason behind this node is to be able to conditionally apply operations to one a masked list, for example select vertices based on location and move them or as shown below, select numbers and negate them.

Inputs
------

* **Mask:** Input socket for mask list.
* **Data True:** Input socket for True Data list.
* **Data False:** Input socket for False Data list.

Parameters
----------


* **Level:** Set the level at which the items to be masked.

* **Choice:** When true, use the mask to choose between elements of the lists, otherwise, use the mask to mix the lists while keeping all their elements.

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Match List Global:** Define how list with different lengths should be matched. **Data True** and **Data False** are matched together at each level, and also matched with **Mask** on the two last levels (depending on **Level**).

Outputs
-------

* **Data:** Mixed data of the incoming data, the length of Outputs depends on the  **Data True**, **Data False** and **Mask** list lengths.

Example
-------

.. image:: https://user-images.githubusercontent.com/14288520/188215041-1bc98399-0ce8-4381-917b-89c01ebc94f9.png
  :target: https://user-images.githubusercontent.com/14288520/188215041-1bc98399-0ce8-4381-917b-89c01ebc94f9.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://cloud.githubusercontent.com/assets/5409756/11457323/e7af5960-96e0-11e5-86e0-a9401f5e059e.png
  :alt: ListMaskDemo.PNG

.. image:: https://cloud.githubusercontent.com/assets/6241382/11584560/2604eebe-9a65-11e5-9aff-8eb123167a6a.png
  :alt: Masked apply
