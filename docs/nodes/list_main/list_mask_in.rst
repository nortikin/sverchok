List Mask In
============

Functionality
-------------

This node use the mask list as switch to mix two data list together. **0** means false, an item from the **Data False** will be appended to the output data; mask list item other than **0** will be considered as true, an item from the **Data True** will be appended to the output data. If the mask list is not long enough to cover all the inputs, it will be repeated as the mask for the rest of inputs. 

Inputs
------

**Mask:** Input socket for mask list.

**Data True:** Input socket for True Data list.

**Data False:** Input socket for False Data list.



Parameters
----------

**Level:** Set the level at which the items to be masked.


Outputs
-------

**Data:** Mixed data of the incoming data, the length of Outputs depends on the  **Data True** and  **Data False** list length.

Example
-------

.. image:: https://cloud.githubusercontent.com/assets/5409756/11457323/e7af5960-96e0-11e5-86e0-a9401f5e059e.png
  :alt: ListMaskDemo.PNG
