Stethoscope
===========


Functionality
-------------

The Node is designed to give a general sense of the connected data stream. After a short preprocessing step Stethoscope draws the data directly to the Node view. 

**The processing step**

+---------------------------------------------------+
| The first and last 20 sublists will be displayed. | 
| The data in between is dropped and represented by |
| placeholder ellipses.                             | 
+---------------------------------------------------+
| Float values are rounded if possible.             |
+---------------------------------------------------+


Inputs
------

Any known Sverchok data type.


Parameters
----------

- Currently a *visibility* toggle and *text drawing color* chooser.
- The Rounding parameter is useful to restrict the significant digit information for floats and vectors. 
- Setting the Rounding value to `0` will turn off any string-formatted rounding techniques, this is useful for example quickly looking at object names.


Outputs
-------

Direct output to Node View


Examples
--------

Notes
-----

Implementation is ``POST_PIXEL`` using ``bgl`` and ``blf``