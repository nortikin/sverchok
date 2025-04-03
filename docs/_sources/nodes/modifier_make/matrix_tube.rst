Matrix Tube
============

.. image:: https://user-images.githubusercontent.com/14288520/201468347-0efebe3f-4554-4308-81fc-e9f0cce9fb17.png
  :target: https://user-images.githubusercontent.com/14288520/201468347-0efebe3f-4554-4308-81fc-e9f0cce9fb17.png

*destination after Beta: Modifier Make*

Functionality
-------------

Makes a tube or pipe from a list of matrices. This node takes a list of matrices and a list of vertices as input. The vertices are joined together to form a ring. This ring is transformed by each matrix to form a new ring. Each ring is joined to the previous ring to form a tube. 

.. image:: https://user-images.githubusercontent.com/14288520/201468943-0b3de332-16fa-4bf1-a2fc-187758c7041e.png
  :target: https://user-images.githubusercontent.com/14288520/201468943-0b3de332-16fa-4bf1-a2fc-187758c7041e.png

Inputs
------

* **Matrices** - List of transform matrices.
* **Vertices** - Vertices of ring. Usually from a "Circle" or "NGon" node   
 
Outputs
-------

- **Vertices, Edges and Faces** - These outputs will define the mesh of the tube that skins the input matrices. 

Example of usage
------------------

.. image:: https://user-images.githubusercontent.com/14288520/201469603-49ffbc9c-c7d9-41c3-b503-35dd27687a90.png
  :target: https://user-images.githubusercontent.com/14288520/201469603-49ffbc9c-c7d9-41c3-b503-35dd27687a90.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Vector-> :doc:`Vector sort </nodes/vector/vertices_sort>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/201470303-d76a5344-6098-4839-91c2-09b90573a7d1.png
  :target: https://user-images.githubusercontent.com/14288520/201470303-d76a5344-6098-4839-91c2-09b90573a7d1.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix Euler </nodes/matrix/euler>`
* Matrix-> :doc:`Matrix Matrix Transform </nodes/matrix/iterate>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`