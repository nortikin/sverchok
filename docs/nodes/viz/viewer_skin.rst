Skin Mesher
===========

.. image:: https://github.com/user-attachments/assets/32d50e61-141c-44ce-b46f-a8ceb04929b9
  :target: https://github.com/user-attachments/assets/32d50e61-141c-44ce-b46f-a8ceb04929b9

.. image:: https://user-images.githubusercontent.com/14288520/190581380-acb569e2-d9c0-498e-8ba9-666642008309.png
  :target: https://user-images.githubusercontent.com/14288520/190581380-acb569e2-d9c0-498e-8ba9-666642008309.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`

Functionality
-------------

This node is an interpretation of the current features of the Skin Modifier. During manual editing you would use
alt+s to scale up the size of individual vertices, this node offers the ability to scale vertices by accepting two 
lists of scalar values, one for x scale and one for y scale.

settings roots: Depending on how complicated and disjoint your mesh is you may find the result of the modifier can be made more natural by adjusting the way the node sets the roots.

  .. image:: https://github.com/user-attachments/assets/be22fc14-7cf1-41f6-a2df-57a2d6e0a4e9
    :target: https://github.com/user-attachments/assets/be22fc14-7cf1-41f6-a2df-57a2d6e0a4e9

Additionally you can move skin and subdiv modifier over Modifier Stack:

  .. image:: https://github.com/user-attachments/assets/99b00aea-f144-4e38-9356-34abe9a9e920
    :target: https://github.com/user-attachments/assets/99b00aea-f144-4e38-9356-34abe9a9e920

Category
--------

Viz -> Skin Mesher

Inputs
------

This node takes ``verts``, ``edges``, and optionally ``matrices``, as inputs.
Additionally it accepts ``scale X`` and ``scale Y``

Outputs
-------

Outputs a mesh with a SkinModifier added to it, directly into the scene.

Parameters
----------

  .. image:: https://github.com/user-attachments/assets/5b8dcdc0-c2cb-4484-9f60-d8250ef9a588
    :target: https://github.com/user-attachments/assets/5b8dcdc0-c2cb-4484-9f60-d8250ef9a588

- **Doubles distance** - Removes coinciding verts, also aims to remove double radii data

Caution
-------

You do not want to manually edit the product of this node, that would break the procedural nature of the node. Manual
editing after creation can result in undefined behaviour and is likely overwritten as soon as you update the Sverchok
node tree again by moving upstream sliders etc.

Examples
--------

  .. image:: https://user-images.githubusercontent.com/619340/127733080-a0e2c470-9a72-4c72-88c6-41a814c45d17.png
    :target: https://user-images.githubusercontent.com/619340/127733080-a0e2c470-9a72-4c72-88c6-41a814c45d17.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`

---------

  .. image:: https://user-images.githubusercontent.com/619340/127733292-c7019c45-492d-4c85-b713-931063bac9b4.png
    :target: https://user-images.githubusercontent.com/619340/127733292-c7019c45-492d-4c85-b713-931063bac9b4.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

  .. image:: https://user-images.githubusercontent.com/14288520/190387407-495a6f72-bd39-4138-a758-fb58c550a2ae.png
    :target: https://user-images.githubusercontent.com/14288520/190387407-495a6f72-bd39-4138-a758-fb58c550a2ae.png


* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

  .. image:: https://github.com/user-attachments/assets/eba02be2-c03a-42b0-9e1e-5a725f4e436e
    :target: https://github.com/user-attachments/assets/eba02be2-c03a-42b0-9e1e-5a725f4e436e

Modifiers before and after Skin Viewer modifiers
------------------------------------------------

.. raw:: html

    <video width="700" controls>
        <source src="https://github.com/user-attachments/assets/767cee5e-d6f3-4f21-adc0-0f5312a0c9aa" type="video/mp4">
    Your browser does not support the video tag.
    </video>

.. image:: https://github.com/user-attachments/assets/50f4bf60-ddce-4297-b6c2-60b3b13d8cc1
  :target: https://github.com/user-attachments/assets/50f4bf60-ddce-4297-b6c2-60b3b13d8cc1