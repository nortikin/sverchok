List Mask Out
=============

Functionality
-------------

This node masks **data** list. Masked list contain only masked elements.

Inputs
------

**data** - List of any type and any length that will be masked.

**mask** - List of single value type: *int*, *float*. Its length must be the same as **data** list to work properly.
For every element with non-zero value of **mask**, every element of **data** with the same indices will be masked (therefore rest of the elements will be deleted, *masked*).

Outputs
-------

**mask** - same as input **mask** list

**ind_true** - list of indices of **mask** list with non-zero value

**ind_false** - list of indices of **mask** list with zero value

**dataTrue** - masked list with only **ind_true** indices elements

**dataFalse** - masked list with only **ind_false** indices elements

Examples
--------
