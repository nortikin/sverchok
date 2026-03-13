Multi Cache
===========

.. image:: https://user-images.githubusercontent.com/14288520/188329320-aec08286-a0f1-4d8b-8589-c174370c112d.png
  :target: https://user-images.githubusercontent.com/14288520/188329320-aec08286-a0f1-4d8b-8589-c174370c112d.png

Functionality
-------------

The node stores lists in different "memory buckets" it can output one or many buckets at the same time.

The node can only work properly with lists of numbers (with any wrapping) but will fail to store abstract objects like Curves, Surfaces or Solids


Category
--------

List ->Multi Cache

Inputs
------

- **Data** - data to store
- **In Bucket** - bucket to store input data. If multiple values are given the Data will be split among the defined buckets
- **Out Bucket** - bucket to output data from

Options
-------

- **Pause** - stop recording
- **Unwrap** - every bucket will be surrounded by a [], enabling this option will remove the extra [] by flatting the output list
- **Reset** - Deletes all stored values

Outputs
-------

- **Data** - Data stored in out bucket id


Examples
--------

**Tracing particle movement**

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/list%20mutators/multi_cache/blender_sverchok_multi_cache_example.png
    :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/list%20mutators/multi_cache/blender_sverchok_multi_cache_example.png
