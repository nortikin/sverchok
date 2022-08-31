List Index
==========

.. image:: https://user-images.githubusercontent.com/14288520/187533476-0cce7810-4f52-4997-92d9-6ffac7c0669f.png

Functionality
-------------
This node searches items in given data and returns their indexes. It's equivalent to `list.index` method in Python.

Category
--------

List -> List main -> List Index

Inputs
------

- **data** - where to search items
- **Item** - what to search in data

In use range mode:

- **Start index** - index from which to start searching (inclusive)
- **End index** - index where to finish searching (exclusive)

Outputs
-------

- **Index** - An index of an item in data. If there is no such item -1 value will be returned.

Options
-------

- **Level** - Level of data where to search items. With level 2 it will search in nested list of main one.
- **Use range** - It adds two extra sockets for specifying a range where to search items in given data.

Examples
--------

**Finding index of maximum value in array of random values**

.. image:: https://user-images.githubusercontent.com/28003269/107858186-57878080-6e4c-11eb-84a4-3f23260caa9f.png

**Finding several indices:**

.. image:: https://user-images.githubusercontent.com/14288520/187533943-79991e77-371a-48ad-bc93-5073691c2beb.png
