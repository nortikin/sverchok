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
   - **DXF Hatches** for patterned fills
   - **DXF Linear Dimensions** for measurements
3. Connect all DXF objects to **DXF Export** node
4. Set export path and click "Export DXF"

**Color System:**
- Use RGB colors for visual consistency
- Or use DXF color indices (-4 to 255) for specific DXF color requirements
- -4 = ignore (use default), -3 = by block, -2 = by layer

**Line Types:**
Support for standard DXF line types including CONTINUOUS, DASHED, DOTTED, etc.

**Compatibility:**
- Supports DXF R12 and later formats
- Compatible with most CAD software including AutoCAD, LibreCAD, QCAD
- Preserves layer information and entity properties

.. toctree::
   :glob:
   :maxdepth: 1

   *
