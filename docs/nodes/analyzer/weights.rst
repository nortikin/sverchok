Weights
=======
Functionality
-------------

automatically creates a group of vertices and allows you to assign each vertex weight in many different ways

Input sockets
-------------

**vertIND** - Connect here a list of needed vertex indexes, or node automatically creates a list of indexes of all vertices of the object

**weights** - vertex weights (floats less than 0.0 count as 0.0, bigger than 1.0 count as 1.0)

Parameters
----------

**clear unused** - zero weights for all vertices which is not indexed in the list of indexes

**object name** - name of object to create vertex group for.

**iteration modes** - method that achieve the same amount of vertIND and weights values. "match short"- cuts that list that was longer, "match long cycle"- cycle through elements of the list that was shorter




Usage
-----

.. image:: https://cloud.githubusercontent.com/assets/7894950/4438270/fb374678-47a9-11e4-8aa3-777def8de15d.png
.. image:: https://cloud.githubusercontent.com/assets/7894950/4474551/8c0e9184-4961-11e4-9b91-3cd9ea1c88d4.png
  
