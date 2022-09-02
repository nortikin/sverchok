List Mask Join In
=================

.. image:: https://user-images.githubusercontent.com/14288520/188214090-da2fd597-c35c-4a90-8b96-b0b12d9c950e.png
  :target: https://user-images.githubusercontent.com/14288520/188214090-da2fd597-c35c-4a90-8b96-b0b12d9c950e.png

Functionality
-------------

This node use the mask list i.e. 1,0,0,0 as switch to mix two data list together.

**0** means false, an item from the **Data False** will be appended to the output data;

**1** will be considered as true (actually any value that evaluate as true in python), an item from the **Data True** will be appended to the output data. If the mask list is not long enough to cover all the inputs, it will be repeated as the mask for the rest of inputs.

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
* **Choice:** Make length of out list the same as length of input list


Outputs
-------

* **Data:** Mixed data of the incoming data, the length of Outputs depends on the  **Data True** and  **Data False** list length.

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
