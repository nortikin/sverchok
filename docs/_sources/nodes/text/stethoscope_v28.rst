Stethoscope
===========


.. image:: https://github.com/user-attachments/assets/0868ac63-7635-4058-9654-a970e650a191
  :target: https://github.com/user-attachments/assets/0868ac63-7635-4058-9654-a970e650a191

Functionality
-------------

The Node is designed to give a general sense of the connected data stream. After a short preprocessing step Stethoscope draws the data directly to the Node view. 

**The processing step**

+---------------------------------------------------------------------------------+
| The first and last 20 sublists will be displayed.                               | 
| The data in between is dropped and represented by                               |
| placeholder ellipses.                                                           | 
+---------------------------------------------------------------------------------+
| Float, Matrix, Integers and Boolean values are rounded if possible.             |
+---------------------------------------------------------------------------------+

.. image:: https://github.com/user-attachments/assets/33b3d67f-bd08-4f73-ad98-1341c8faadca
  :target: https://github.com/user-attachments/assets/33b3d67f-bd08-4f73-ad98-1341c8faadca

Inputs
------

Any known Sverchok data type.


Parameters
----------

- Currently a *visibility* toggle and *text drawing color* chooser.
- The Precision parameter is useful to restrict the significant digit information for floats and vectors. 
- Setting the Rounding value to `0` will turn off any string-formatted rounding techniques, this is useful for example quickly looking at object names.
- Selecting monospace fonts allow to show aligned columns of digits

    .. image:: https://github.com/user-attachments/assets/a5e59345-485d-40f0-9976-260d75fd7c74
      :target: https://github.com/user-attachments/assets/a5e59345-485d-40f0-9976-260d75fd7c74

Outputs
-------

Direct output to Node View


Examples
--------

Notes
-----

Implementation is ``POST_PIXEL`` using ``bgl`` and ``blf``