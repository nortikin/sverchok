Adaptative Edges
================

.. image:: https://github.com/user-attachments/assets/b2e12f75-f2c1-46ff-9b39-df83d2d74380
  :target: https://github.com/user-attachments/assets/b2e12f75-f2c1-46ff-9b39-df83d2d74380

Inputs
------

- **Adaptive verts**.
- **Adaptive edges**. What edges are used as base:

  .. image:: https://github.com/user-attachments/assets/9eac2148-bda4-4eed-baa3-4bbdbd46fa2c
    :target: https://github.com/user-attachments/assets/9eac2148-bda4-4eed-baa3-4bbdbd46fa2c

- **Mask of adaptive edges**. What edges hide from using as adaptive edges. Can be used as Boolean mask or Indexes mask

  .. image:: https://github.com/user-attachments/assets/ecb6fe06-b83d-4c44-8af4-5e8405e4452b
    :target: https://github.com/user-attachments/assets/ecb6fe06-b83d-4c44-8af4-5e8405e4452b

  if socket **Mask of adaptive edges** are not connected then all edges are ised:

  .. image:: https://github.com/user-attachments/assets/81479547-9405-41d6-9c2a-260e575ed66d
    :target: https://github.com/user-attachments/assets/81479547-9405-41d6-9c2a-260e575ed66d

- **Verts**.
- **Edges**. Mesh are used to adaptive

  .. image:: https://github.com/user-attachments/assets/6a44b94e-f726-409f-b718-0e77e70dc575
    :target: https://github.com/user-attachments/assets/6a44b94e-f726-409f-b718-0e77e70dc575

- **First adaptive index**.
- **Second adaptive index**. Indexes of vertices of Mesh that will be used to align with adaptive edges (you may use verts not only Ox direction)

  .. image:: https://github.com/user-attachments/assets/b79aa32d-8d5f-4aee-95cf-7173a76f3f96
    :target: https://github.com/user-attachments/assets/b79aa32d-8d5f-4aee-95cf-7173a76f3f96

  .. image:: https://github.com/user-attachments/assets/f4ece3e3-36bd-494c-b5d8-28e23b336e4c
    :target: https://github.com/user-attachments/assets/f4ece3e3-36bd-494c-b5d8-28e23b336e4c

  If you swap indexes then shape of adaptive mesh will changed:

  .. image:: https://github.com/user-attachments/assets/5a9444eb-3d94-4f09-8f38-8fae23242a60
    :target: https://github.com/user-attachments/assets/5a9444eb-3d94-4f09-8f38-8fae23242a60

Parameters
----------

- **Join meshes**. Join all meshes to a single mesh.

Outputs
-------

- **Vertices**.
- **Edges**. Results mesh or meshes

Examples
========

Rotation of source mesh are transfered to the adaptive mesh
-----------------------------------------------------------

.. image:: https://github.com/user-attachments/assets/ce50368c-0f1e-413a-9915-0ef92e532b72
  :target: https://github.com/user-attachments/assets/ce50368c-0f1e-413a-9915-0ef92e532b72

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`3pt Arc </nodes/generator/basic_3pt_arc>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Matrix-> :doc:`Matrix Input </nodes/matrix/input>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`


.. image:: https://github.com/user-attachments/assets/6796a0c3-7df6-4ec2-93a9-91f2dda3d4f7
  :target: https://github.com/user-attachments/assets/6796a0c3-7df6-4ec2-93a9-91f2dda3d4f7

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`3pt Arc </nodes/generator/basic_3pt_arc>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Matrix-> :doc:`Matrix Input </nodes/matrix/input>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

.. image:: https://github.com/user-attachments/assets/9891b297-a860-487f-aa46-d116b7d6001d
  :target: https://github.com/user-attachments/assets/9891b297-a860-487f-aa46-d116b7d6001d

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator->Generatots Extended-> :doc:`Hilbert </nodes/generators_extended/hilbert>`
* Transform-> :doc:`Rotate </nodes/transforms/rotate_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
