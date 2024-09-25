List Input
==========

.. image:: https://github.com/user-attachments/assets/dda5d39e-91ab-48e2-8a61-aad2dbe06a59
  :target: https://github.com/user-attachments/assets/dda5d39e-91ab-48e2-8a61-aad2dbe06a59

Functionality
-------------

This node got huge update for MK2 version:

- appended new types of data.
- now there is no limits of counters.

Provides a way to create a flat list of *Booleans*, *Integers*, *Floats*, *Vectors*, *Quaternions*,
*Matrixes*, *Colors*, *Texts* with subtypes.
Also see: :doc:`Text->Text In+ </nodes/text/text_in_mk2>` node.


Parameters
----------

The value of input fields changes according to the Type selector.

1. General controls
-------------------

.. image:: https://github.com/user-attachments/assets/69ed06b6-b90e-4a8b-aace-6891fc6750ab
  :target: https://github.com/user-attachments/assets/69ed06b6-b90e-4a8b-aace-6891fc6750ab

1.1. List length
----------------

.. image:: https://github.com/user-attachments/assets/3a4fd57f-e347-40ab-9b49-653b11fddf97
  :target: https://github.com/user-attachments/assets/3a4fd57f-e347-40ab-9b49-653b11fddf97

Length of the list is individual of Type Selector (2). You can set different length for every type of data independently.

1.2. Type Selector
------------------

.. image:: https://github.com/user-attachments/assets/80039ca9-6da9-480b-a12e-40e5d7d58504
  :target: https://github.com/user-attachments/assets/80039ca9-6da9-480b-a12e-40e5d7d58504

You can select type of *Bool*, *Int*, *Float*, *Vector*, *Quaternion*, *Matrix*, *Color*, *Text*.

1.3. Data
---------

.. image:: https://github.com/user-attachments/assets/093ec7ae-6c26-4dcb-942a-d7d523ef50c8
  :target: https://github.com/user-attachments/assets/093ec7ae-6c26-4dcb-942a-d7d523ef50c8

Data you can input manually.

1.4. Select elements
--------------------

.. image:: https://github.com/user-attachments/assets/e2a6281b-ecdf-4ce7-b54d-736995159237
  :target: https://github.com/user-attachments/assets/e2a6281b-ecdf-4ce7-b54d-736995159237

You can manually select/hide elements to output socket without changes of the source data

1.5. Clipboard control (Copy/Paste)
-----------------------------------

**Copy**

.. image:: https://github.com/user-attachments/assets/3c79346a-a828-4412-a570-84664a265d76
  :target: https://github.com/user-attachments/assets/3c79346a-a828-4412-a570-84664a265d76

**Paste**

.. image:: https://github.com/user-attachments/assets/9e43585a-8860-4c7e-a870-121f99adac0f
  :target: https://github.com/user-attachments/assets/9e43585a-8860-4c7e-a870-121f99adac0f

You can copy/paste data into or from the external text data.

1.6. Indexes of outputs
-----------------------

.. image:: https://github.com/user-attachments/assets/b20dec0e-cc66-4e67-b006-3adf1a95b5d6
  :target: https://github.com/user-attachments/assets/b20dec0e-cc66-4e67-b006-3adf1a95b5d6

Indexes of output list. (For information)

1.7. Subtype of data
--------------------

View list of Floats as Angles (Degrees or Radians), Distance (meters) of Power:

.. image:: https://github.com/user-attachments/assets/5386c842-7bd7-48b7-8f03-5d579b91684f
  :target: https://github.com/user-attachments/assets/5386c842-7bd7-48b7-8f03-5d579b91684f

View list of colors as 4D vector, Color with Alpha and Color Gamma without Alpha:

.. image:: https://github.com/user-attachments/assets/793737be-be57-4fec-9801-55a0655b047c
  :target: https://github.com/user-attachments/assets/793737be-be57-4fec-9801-55a0655b047c


2. Using of Mask input socket
-----------------------------

If mask is true then element is hiding from output (is an oposite of selector 4)

You can use external data as mask for this node:

.. image:: https://github.com/user-attachments/assets/d82738df-eb38-46e8-9201-28f697a4b3a2
  :target: https://github.com/user-attachments/assets/d82738df-eb38-46e8-9201-28f697a4b3a2

You can select what type of data are mask - boolean or indexes. You can invert mask by "Invert" button in Mask input socket.

3. Matrixes
-----------

Matrixes are compicated elements. So they has a some controls to converts views. You can set view of every mastrix as you wish: as 4x4, or Euler Angles, or Angle Axis:

.. image:: https://github.com/user-attachments/assets/7a08d702-f816-4820-b49c-d544c3e7f2c9
  :target: https://github.com/user-attachments/assets/7a08d702-f816-4820-b49c-d544c3e7f2c9

if you choose matrix view as *Euler* or *Axis Angle* then you can also set a shears componets of matrix:

.. image:: https://github.com/user-attachments/assets/83fa740e-12b9-4711-b641-a17b60111610
  :target: https://github.com/user-attachments/assets/83fa740e-12b9-4711-b641-a17b60111610

Shears components are shares between Euler and Axis Angle.

3.1. Matrixes addition controls
-------------------------------

**Reset 4x4 diagonal to ones**:

.. image:: https://github.com/user-attachments/assets/f14afd06-c86a-44ee-92d9-ecffbd492873
  :target: https://github.com/user-attachments/assets/f14afd06-c86a-44ee-92d9-ecffbd492873

**Reset shears to zero**:

.. image:: https://github.com/user-attachments/assets/cd46b2fe-d71f-48c7-9f7a-cfe0bcdbafd7
  :target: https://github.com/user-attachments/assets/cd46b2fe-d71f-48c7-9f7a-cfe0bcdbafd7

**Copy data from Euler view into the 4x4 view**:

.. image:: https://github.com/user-attachments/assets/4033ef48-6403-4593-96c0-c4ca158a1c02
  :target: https://github.com/user-attachments/assets/4033ef48-6403-4593-96c0-c4ca158a1c02

**Copy data from Axis Angle view into the 4x4 view**:

.. image:: https://github.com/user-attachments/assets/bea0f130-e7a7-482f-84a3-3050c3d5cf71
  :target: https://github.com/user-attachments/assets/bea0f130-e7a7-482f-84a3-3050c3d5cf71

**Copy data from Euler Angles view into the Axis Angle View (all shears has to be 0)**:

.. image:: https://github.com/user-attachments/assets/25cca0ab-54bc-488c-bc84-3ed4d4169e7e
  :target: https://github.com/user-attachments/assets/25cca0ab-54bc-488c-bc84-3ed4d4169e7e

4. Strings mode
---------------

.. image:: https://github.com/user-attachments/assets/9ee3c288-1f2d-4469-8e8f-eef31e2cb3a8
  :target: https://github.com/user-attachments/assets/9ee3c288-1f2d-4469-8e8f-eef31e2cb3a8

You can edit strings without activate Sverchok node. Some times Blender do not want to update output data for strings. So you have to press button "update text":

.. image:: https://github.com/user-attachments/assets/7db1644e-55fa-4c9c-b9a0-3aead716320c
  :target: https://github.com/user-attachments/assets/7db1644e-55fa-4c9c-b9a0-3aead716320c

Output
------

A single *flat* ``list``.

3D panel
--------

The node can show its properties on 3D panel. 
For this parameter `to 3d` should be enabled, output should be linked.
After that you can press `scan for props` button on 3D panel for showing the node properties on 3D panel.

.. image:: https://github.com/user-attachments/assets/a9f600f4-901a-43a6-9482-82e11a4878f3
  :target: https://github.com/user-attachments/assets/a9f600f4-901a-43a6-9482-82e11a4878f3

.. image:: https://github.com/user-attachments/assets/b790da38-c16d-41ee-bb7c-d83e2d0219d1
  :target: https://github.com/user-attachments/assets/b790da38-c16d-41ee-bb7c-d83e2d0219d1

Warning: Matrixes are not shown for a while in 3D panel.

Examples
--------

Useful when you have no immediate need to generate such lists programmatically.

.. image:: https://user-images.githubusercontent.com/28003269/70140711-c7c63e00-16ae-11ea-9266-e4f24586e448.png
    :target: https://user-images.githubusercontent.com/28003269/70140711-c7c63e00-16ae-11ea-9266-e4f24586e448.png
    

.. image:: https://user-images.githubusercontent.com/14288520/189119167-e08360ab-fd27-47d1-947d-1c0628bdac8a.png 
  :target: https://user-images.githubusercontent.com/14288520/189119167-e08360ab-fd27-47d1-947d-1c0628bdac8a.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Use List input as input matrixes and colors:

.. image:: https://github.com/user-attachments/assets/457905bd-1d9e-41f2-9d7d-5e4cd97a364a
  :target: https://github.com/user-attachments/assets/457905bd-1d9e-41f2-9d7d-5e4cd97a364a

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`