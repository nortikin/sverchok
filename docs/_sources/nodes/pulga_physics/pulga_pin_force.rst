Pulga Pin Force
===============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c38bf44e-b9f5-47cf-81dc-6028c38b9ecf
  :target: https://github.com/nortikin/sverchok/assets/14288520/c38bf44e-b9f5-47cf-81dc-6028c38b9ecf

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The force restricts the movement of the pinned verts

.. image:: https://github.com/nortikin/sverchok/assets/14288520/9335ef65-affc-485e-89ed-fe9d709ce18a
  :target: https://github.com/nortikin/sverchok/assets/14288520/9335ef65-affc-485e-89ed-fe9d709ce18a

Input
-----

* **Pins**: It will accept a Boolean list as a mask list or a Integer list as the index of the vertex to pin

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/08c46707-59ab-440c-bd9c-0904f939d107
    :target: https://github.com/nortikin/sverchok/assets/14288520/08c46707-59ab-440c-bd9c-0904f939d107

* **Axis**: Axis to restrict. It can be defined with the drop-down menu or a list from a list from 0 to 6 to define the axis restriction per pin. (0 = XYZ, 1 = XY, 2 = XZ, 3 = YZ, 4 = X, 5 = Y, 6 = Z )

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/fd1b527d-03b9-4df4-b904-bf58ff6a09dd
    :target: https://github.com/nortikin/sverchok/assets/14288520/fd1b527d-03b9-4df4-b904-bf58ff6a09dd

* **Pins Goal**: End position of the pinned vertices.

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/b79858f9-f878-46ee-b7ee-2e4326051b41
    :target: https://github.com/nortikin/sverchok/assets/14288520/b79858f9-f878-46ee-b7ee-2e4326051b41

Examples
--------

Description example:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/09eca1c8-ad58-4d83-9618-59a286f6babf
  :target: https://github.com/nortikin/sverchok/assets/14288520/09eca1c8-ad58-4d83-9618-59a286f6babf

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Analyzers->Component Analyzer: :ref:`Adjacent faces num<VERTICES_ADJACENT_FACES_NUM>`
* MUL, SINCOS, MUL X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector Polar Output </nodes/vector/vector_polar_out>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* LESS EQ: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Vector Force </nodes/pulga_physics/pulga_vector_force>`
* Pulga Physics-> :doc:`Pulga Springs Force </nodes/pulga_physics/pulga_springs_force>`

--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/fe532189-7aca-41b4-91eb-3ab2594295f2
  :target: https://github.com/nortikin/sverchok/assets/14288520/fe532189-7aca-41b4-91eb-3ab2594295f2

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Analyzers->Component Analyzer: :ref:`Adjacent faces num<VERTICES_ADJACENT_FACES_NUM>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* LESS EQ: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Vector Force </nodes/pulga_physics/pulga_vector_force>`
* Pulga Physics-> :doc:`Pulga Springs Force </nodes/pulga_physics/pulga_springs_force>`

--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4ec10d8b-b78e-45fd-b325-855e3e0deb9b
  :target: https://github.com/nortikin/sverchok/assets/14288520/4ec10d8b-b78e-45fd-b325-855e3e0deb9b

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzers->Component Analyzer: :ref:`Adjacent faces num<VERTICES_ADJACENT_FACES_NUM>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* LESS EQ: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Vector Force </nodes/pulga_physics/pulga_vector_force>`
* Pulga Physics-> :doc:`Pulga Springs Force </nodes/pulga_physics/pulga_springs_force>`

---------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_pin_force/blender_sverchok_pulga_pin_force_example_02.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_pin_force/blender_sverchok_pulga_pin_force_example_02.png