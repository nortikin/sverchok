Find closest value
==================

.. image:: https://user-images.githubusercontent.com/28003269/107801210-3ace4880-6d79-11eb-9fe4-440caef9f73f.png

Functionality
-------------
The node takes data where to search and values which should be found in the data.
The closest value (and index of the value) to given will be return. Input data can be unsorted.

Category
--------

List -> Find closest value

Inputs
------

- **Values** - list of figures which should be found
- **Data** - list of figures where to search
- **Range** - determines how output values can be differ from input one

Outputs
-------

- **Closest values** - list of figures from data socket which are closest to given values
- **Closest indexes** - indexes of closest values in data list

Options
-------

- **Mode** - *single* mode will find closest value to input one, *range* - will find closest values which will be in given range relatively to input value

Notes
-----
In the range mode the output of the node has one more nested list.
To each input value there is output list.
For example to input values like this [[1, 10]] output can look like [[[0,1,2], [9,10,11]]]
Also keep in mind that output lists can be empty in case if no values feat in range.

Examples
--------

**Find closest value to 5 in random range from 0 to 10**

.. image:: https://user-images.githubusercontent.com/28003269/90544116-bae36f00-e197-11ea-9138-90d79dad6176.png

**Searching value in input data in range between 3.97 to 5.03**

.. image:: https://user-images.githubusercontent.com/28003269/107801848-0dce6580-6d7a-11eb-9562-0d09c8c05779.png