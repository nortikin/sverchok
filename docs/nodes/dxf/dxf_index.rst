***
DXF
***

DXF Workflow
============

Overview
--------

The DXF nodes provide a complete workflow for importing and exporting DXF files in Sverchok:

**Import Workflow:**
1. Use **DXF Import** node to load DXF files
2. Filter layers as needed using the layer management system
3. Use "Add Viewers" to quickly visualize different geometry types
4. Process imported geometry through Sverchok nodes

**Export Workflow:**
1. Create geometry using standard Sverchok nodes
2. Convert to DXF objects using specialized DXF nodes:

   - **DXF Lines** for edge-based geometry
   - **DXF Polygons** for face-based geometry  
   - **DXF Circles** for circles geometry from curves    
   - **DXF Hatches** for patterned fills
   - **DXF Linear Dimensions** for measurements
   - **DXF Texts** for texts geometry 

3. Connect all DXF objects to **DXF Export** node
4. Set export path, (optionally export all as block) and click "Export DXF"

**Color System:**
- Use RGB colors for visual consistency
- Or use DXF color indices (-4 to 255) for specific DXF color requirements
- -4 = ignore (use default), -3 = by block, -2 = by layer

**Line Types:**
Support for standard DXF line types including CONTINUOUS, DASHED, DOTTED, etc.

**Compatibility:**
- Supports DXF R12 and later formats
- Compatible with most CAD software including AutoCAD, LibreCAD, ZWCAD, QCAD and ZCAD.
- The last, ZCAD is mostly fits my needs. Opensource, cross-platform, fast, supports all my entities. Recommend it for everyday usage.
- Preserves layer information and entity properties

**General for export nodes**

*Default DXF linetypes*

.. image:: https://github.com/user-attachments/assets/1fe1e785-04fc-441c-b267-514538a53388

*Default DXF thicknesses*

.. image:: https://github.com/user-attachments/assets/aa8cd5af-a423-4a6d-8e01-54f32e7831ad

*Default DXF colors - use whether color in node or DXF index from table*

.. image:: https://github.com/user-attachments/assets/390e21c3-3f23-4766-bde1-5cb555b980c4
.. image:: https://github.com/user-attachments/assets/951d31c1-a2ad-4309-912e-61d230509ee5



.. toctree::
   :glob:
   :maxdepth: 1

   *
