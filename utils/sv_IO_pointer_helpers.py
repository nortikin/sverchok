# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

def pack_pointer_property_name(datablock, node_ref, key_name):
    """
    store the pointerproperty with a temporary key in the json for exporting
    
    input:
        datacblock : your pointer directly, something like self.texture_pointer
        node_ref   : node_ref you get from inside 'storage_get_data` function.
        key_name   : the temporary name inside the node_ref which the exporter 
                     will use to keep track of datablock.name . This should be 
                     a unique name and not be identical to any attribute or 
                     annotation of the node
    return:
        False (no useful return yet)

    """
    node_ref[key_name] = datablock.name if datablock else ""

def unpack_pointer_property_name(data_kind, node_ref, key_name):
    """
    attempt to unpack the pointerproperty data found in the json, 
    if the datablock is found inside the .blend being imported into, then the 
    function returns that datablock or None

    input:
        data_kind  : this can be any bpy.data.*  <images, texts, materials...>
        node_ref   : the reference obtained in `storage_set_data` function
        key_name   : the datablock.name that was stored in json. 
    return:
        datablcok or None

    """
    key = node_ref.get(key_name)
    if key in data_kind:
        return data_kind.get(key)
    return None

"""
usage

from sverchok.utils.sv_IO_pointer_helpers import pack_pointer_property_name, unpack_pointer_property_name

class node

    properties_to_skip_iojson = ['texture_pointer']
    ...

    def storage_get_data(self, node_ref):
        pack_pointer_property_name(self.texture_pointer, node_ref, "texture_name")

    def storage_set_data(self, node_ref):
        self.texture_point = unpack_pointer_property_name(bpy.data.textures, node_ref, "texture_name")

"""


