Chess Selection
===============

.. image:: https://user-images.githubusercontent.com/14288520/197345091-2d118715-4268-4253-8dff-b14439f04634.png
  :target: https://user-images.githubusercontent.com/14288520/197345091-2d118715-4268-4253-8dff-b14439f04634.png

Functionality
-------------
The node creates face selection mask with pattern like chess board.

.. image:: https://user-images.githubusercontent.com/14288520/197345375-154e0819-e26f-4b83-8308-d51cbf5046fa.png
  :target: https://user-images.githubusercontent.com/14288520/197345375-154e0819-e26f-4b83-8308-d51cbf5046fa.png

Category
--------

Analysers -> Chess Selection

Inputs
------

- **Vertices** - vertices of base mesh
- **Faces** - faces of base mesh

Outputs
-------

- **Face mask** - list of True or False per give faces for usage with other nodes

Usage
-----

.. image:: https://user-images.githubusercontent.com/14288520/197347215-0d47659c-26e8-4f75-bb27-3775c4e104d8.png
  :target: https://user-images.githubusercontent.com/14288520/197347215-0d47659c-26e8-4f75-bb27-3775c4e104d8.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Can be used with 3D primitives.

.. image:: https://user-images.githubusercontent.com/14288520/197347851-2cd64f57-b7f4-49ad-93ac-6f8328dd6dd5.png
  :target: https://user-images.githubusercontent.com/14288520/197347851-2cd64f57-b7f4-49ad-93ac-6f8328dd6dd5.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`