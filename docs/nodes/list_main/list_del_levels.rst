List Delete Levels
==================

Functionality
-------------

This helps flatten lists, or make them less nested. 

The analogy to keep in mind might be: 

.. pull-quote::
    knocking through walls in a house to join two spaces, or knock non load bearing walls between buildings to join them.

Incoming nested lists can be made less nested.

.. code-block:: python

    # del level 0, remove outer wrapping
    
    [[0,1,2,3,4]] 
    >>> [0,1,2,3,4]

    [[4, 5, 6], [4, 7, 10], [4, 9, 14]]
    >>> [4, 5, 6, 4, 7, 10, 4, 9, 14]

    [[5], [5], [5], [5], [5], [5]]
    >>> [5, 5, 5, 5, 5, 5]

Inputs
------

Parameters
----------

Outputs
-------

Examples
--------

Notes
-----
