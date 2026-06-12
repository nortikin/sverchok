# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from os import link
from platform import node

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty, CollectionProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, describe_data_shape_by_level, list_levels_adjust, SIMPLE_DATA_TYPES,
                                     changable_sockets)
from sverchok.utils.curve.core import SvCurve
from sverchok.core.socket_data import sv_deep_copy
from sverchok.utils.surface.core import SvSurface
from sverchok.dependencies import FreeCAD
from sverchok.utils.sv_logging import sv_logger
from sverchok.utils.handle_blender_data import correct_collection_length
from numpy import ndarray
from dataclasses import dataclass

ALL_TYPES = SIMPLE_DATA_TYPES + (SvCurve, SvSurface)
OBJECTS_TYPES = (SvCurve, SvSurface)
if FreeCAD is not None:
    import Part
    OBJECTS_TYPES = OBJECTS_TYPES + (Part.Shape,)

@dataclass
class LevelInfo:
    TYPE: str = None
    COUNT: int = 0
    ALERT: bool = False
    SUB: bool = False # leaf or list (можно ли просканировать в глубину)
    pass

class SvNestingLevelEntryMK3(bpy.types.PropertyGroup):
    def update_entry(self, context):
        if hasattr(context, 'node'):
            updateNode(context.node, context)
        else:
            sv_logger.debug("Node is not defined in this context, so will not update the node.")

    description : StringProperty(options = {'SKIP_SAVE'}, default="?")
    flatten : BoolProperty(
                name = "Flatten",
                description = "Concatenate all child lists into one list",
                default=False,
                update=update_entry)
    wrap : BoolProperty(
                name = "Wrap",
                description = "Wrap data into additional pair of square brackets []",
                default=False,
                update=update_entry)
    alert : BoolProperty(
                name = "Alert",
                description = "Alert some warning about this level",
                default=False,
                options={'SKIP_SAVE'},
                )

def recursive_unpack(data, levels_info=None):
    # res = []
    if levels_info is None:
        raise Exception("levels_info should be provided for recursive_unpack")
    if len(levels_info)==0:
        raise Exception("levels_info should contain at least one level for recursive_unpack")

    level = 0
    LIST_TYPES = (list, tuple,) # раньше ещё был ndarray, но в sv_get(deep_copy==True) его нет, так что уберу
    LIST_TYPES_EXACT = frozenset(LIST_TYPES) # На больших списках даже на 3 элемента даёт маленький прирост, его видно, если убрать frozenset
    len_levels_info = len(levels_info)-1
    force_reload_config = False
    max_level_reached = False

    # Вызов только при погружении в уровень, так как при первом вызове функции data может быть простым числом,
    # и тогда не будет смысла проверять галочки flatten/wrap, так как они относятся к спискам, а не к элементарным типам.
    def _recursive_unpack(data, level, res=None):
        nonlocal force_reload_config, max_level_reached
        #if res is None:
        res = []
        res_append = res.append
        res_extend = res.extend
        next_level = level+1
        if len_levels_info<next_level:
            # Выставить признак принудительной перезагрузка конфигурации данных после завершения
            # работы функции
            force_reload_config = True
            # Продолжение копирования, без изменения данных после обнаружения превышения количества настроенных уровней.
            flatten_wrap = 0
        else:
            # Если уровень дошёл до нижнего уровня конфигурации
            if len_levels_info==next_level:
                max_level_reached = True
            flatten_wrap = levels_info[next_level]

        if flatten_wrap==0: # flatten==False and wrap==False
            for elem in data:
                if type(elem) in LIST_TYPES_EXACT:
                    elem = _recursive_unpack(elem, next_level)
                res_append(elem)
            pass
        elif flatten_wrap==1: # flatten==False and wrap==True
            for elem in data:
                if type(elem) in LIST_TYPES_EXACT:
                    elem = _recursive_unpack(elem, next_level)
                res_append([elem])
            pass
        elif flatten_wrap==2: # flatten==True and wrap==False
            for elem in data:
                if type(elem) in LIST_TYPES_EXACT:
                    val = _recursive_unpack(elem, next_level)
                    res_extend(val)
                else:
                    res_append(elem)
            pass
        elif flatten_wrap==3: # flatten==True and wrap==True
            for elem in data:
                if type(elem) in LIST_TYPES_EXACT:
                    val = _recursive_unpack(elem, next_level)
                    res_extend(val)
                else:
                    res_append(elem)
            pass
            # Обернуть результат flatten текущего уровня:
            res = [res]
        else:
            raise Exception(f"Unsupported flatten/wrap mode: {flatten_wrap}")

        return res
    
    type_elem = type(data)
    if type_elem in LIST_TYPES_EXACT:
        res = _recursive_unpack(data, level)
        # На верхнем уровне flatten не выполняется, так как там нет родительского уровня, который нужно распаковать. Поэтому можно выполнить только wrap:
        if levels_info[0] in (1,3):
            res = [res]
        pass
    else:
        res = data
    
    if max_level_reached==False:
        # Перегрузить конфигурацию, если не достинут максимальный уровень:
        # (пользователь может сделать flatten и тогда функция не достигнет
        # низа. Тоже нужно пересчитать)
        force_reload_config = True

    return (res, force_reload_config)

# Загрузить описание уровней данных. 
def data_levels_info(data, levels_info=None, level_root=0):
    LIST_TYPES_EXACT = frozenset((list, tuple,))
    if levels_info is None or level_root==0:
        levels_info = [dict(), dict()]

    def data_levels_info(data, levels_info, level_root):
        # TODO: разобраться, когда среди вложенных данных только list
        if not data:
            return
        if len(levels_info) <= level_root+1:
            levels_info.append(dict())
        levels_info_level_root = levels_info[level_root+1]

        for elem in data:
            type_elem = type(elem)
            if type_elem not in levels_info_level_root:
                levels_info_level_root[type_elem] = LevelInfo(TYPE=type_elem, COUNT=0, ALERT=False, SUB=False)
            
            if type_elem in LIST_TYPES_EXACT:
                levels_info_level_root[type_elem].SUB = True
                data_levels_info(elem, levels_info, level_root + 1)
                pass
            else:
                break
        pass
        return


    levels_info_level_root = levels_info[level_root+1]
    if isinstance(data, ALL_TYPES):
        # Срабатывает, если вызов сразу происходит для простого числа
        levels_info_level_root.setdefault(type(data), LevelInfo(TYPE=type(data), COUNT=1, ALERT=False))
    else:
        levels_info[0][type(data)] = LevelInfo(TYPE=type(data), COUNT=1, ALERT=False)
        data_levels_info(data, levels_info, level_root)
    return levels_info

class SvListLevelsNodeMK3(SverchCustomTreeNode, bpy.types.Node):
    '''
    Triggers: List Levels
    Tooltip: List nesting levels manipulation\n\t[[0,1,2,3,4]] (Flatten) => [0,1,2,3,4]\n\t[[0,1,2,3,4]] (Wrap) => [[[0,1,2,3,4]]]
    '''
    bl_idname = 'SvListLevelsNodeMK3'
    bl_label = 'List Levels'
    bl_icon = 'OUTLINER'

    levels_config : bpy.props.CollectionProperty(type=SvNestingLevelEntryMK3)
    nesting: IntProperty(description="How much nested levels should be shown")
    load_levels_config_: bpy.props.BoolProperty(default=False)
    
    def updateNodeReload(self, context):
        if self.load_levels_config==True:
            updateNode(self, context)
        else:
            pass
        return
    
    load_levels_config: bpy.props.BoolProperty(
        default = False,
        name    = "Reload levels config",
        description = "Relad Levels config from current data",
        update      = updateNodeReload,
    )


    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.use_property_decorate = False
        row.use_property_split = True

        # if self.load_levels_config==False:
        #     row.column(align=True).prop(self, 'load_levels_config', toggle=True, icon='FILE_REFRESH',)
        # else:
        #     row.column(align=True).prop(self, 'load_levels_config', toggle=True, icon='GHOST_DISABLED', text='Processing... Wait')

        root = layout.box()
        if not self.nesting:
            root.label(text="No data passed")
            return
        
        grid = root.grid_flow(row_major=True, columns=4, align=True, even_columns=False, )
        e = grid.row(align=True)
        e.label(text='Lvl')
        e = grid.row(align=True)
        e.label(text='Shape')
        e = grid.row(align=True)
        e.label(text='Flatten')
        e.alignment = 'CENTER'
        e = grid.row(align=True)
        e.alignment = 'CENTER'
        e.label(text='Wrap')

        for I, entry in zip(range(self.nesting), self.levels_config):
            grid.column(align=True).label(text=f"{I+1}")
            e = grid.row(align=True)
            e.alignment = 'LEFT'
            e.alert = entry.alert
            e.label(text=entry.description,)
            if entry.alert:
                e.label(text='', icon='ERROR')
            e = grid.row(align=True)
            e.alignment = 'CENTER'
            if 0<I and I<=self.nesting-2:
                e.prop(entry, 'flatten', text='',)
            else:
                e.label(icon='X', text='')
            e = grid.row(align=True)
            e.alignment = 'CENTER'
            e.prop(entry, 'wrap', text='')
        
        return


    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'data_1')
        self.inputs['data_1'].label = 'Data'

        self.outputs.new('SvStringsSocket', 'data_1')
        self.outputs['data_1'].label = 'Data'
        return

    def sv_update(self):
        changable_sockets(self, 'data_1', ['data_1', ])
        return
    
    def reload_config(self, datas):
        self.load_levels_config = False
        level_infos = []
        for data in datas:
            _levels_info = data_levels_info(data)
            for I in range(len(_levels_info)):
                if I>=len(level_infos):
                    level_infos.append(dict())
                alert = False
                if len(_levels_info[I])>1:
                    alert = True
                for key, value in _levels_info[I].items():
                    if key not in level_infos[I]:
                        level_infos[I][key] = LevelInfo(TYPE=key, COUNT=0, ALERT=False)
                    level_infos[I][key].COUNT += value.COUNT
                    level_infos[I][key].ALERT = level_infos[I][key].ALERT or alert
                pass
            pass

        len_levels_info = len(level_infos)
        self.nesting = len_levels_info if datas else 0

        correct_collection_length(self.levels_config, len_levels_info)

        for entry, description in zip(self.levels_config, level_infos):
            #entry.description = ",".join([f"{k.__name__}: {v.COUNT}" for k, v in description.items()])
            entry.description = ",".join([f"{k.__name__}" for k, v in description.items()])
            entry.alert = next(iter(description.items()))[1].ALERT if len(description)>0 else False
        pass

        if self.levels_config:
            # Первый и последний элемент flatten надо очищать, чтобы он не сохранялся, чтобы в случае восстановления уровня неожиданно не восстанавливался как включённый.
            # Я тут не полчаса завис, когда при переподключении списков UI увеличился на одну позицию и галочка оказалась включённой, но это не обращало на себя
            # внимание, т.к. я не работал с этим нодом и не видел изменений в его UI. А ситуация может быть ещё критичнее, когда нод вообще находится 
            # за пределами области видимости.
            if self.levels_config[0].flatten != False:
                self.levels_config[0].flatten = False
            if self.levels_config[-1].flatten != False:
                self.levels_config[-1].flatten = False
        else:
            pass


    def process(self):

        force_reload_config = False
        datas = []
        for I, socket in enumerate(self.inputs):
            if socket.is_linked==False and socket==self.inputs[-1]: # Возможна ситуация, когда последний link только подключили, а новый последний неподключенный link ещё не создали.
                break
            data = socket.sv_get(default=[], deepcopy=False)
            datas.append(data)

        # Добавить ещё один входящий сокет, если последний входящий сокет подключен (но данные из него браться не будут)
        if len(self.inputs)>=1 and self.inputs[-1].is_linked==True:
            name = f"data_{len(self.inputs)+1}"
            label = f"Data_{len(self.inputs)+1}"
            self.inputs.new('SvStringsSocket', name)
            self.inputs[name].label = label
            force_reload_config = True

        while len(self.inputs) > 1 and not self.inputs[-2].links:
            socket_to_remove = self.inputs[-1]
            for link in list(socket_to_remove.links):
                self.id_data.links.remove(link)
            self.inputs.remove(socket_to_remove)

        # Проверить outputs. Если нарушен порядок или сокетов не хватает, то создать дополнительные сокеты
        for I in range(1, len(self.outputs)+1):
            IDX = I+1
            name = f'data_{IDX}'
            if name not in self.outputs:
                while(len(self.outputs)>IDX):
                    socket_to_remove = self.outputs[-1]
                    for link in list(socket_to_remove.links):
                        self.id_data.links.remove(link)
                    self.outputs.remove(socket_to_remove)
                force_reload_config = True
                break
            pass

        while(len(self.outputs)>1 and len(self.outputs) > len(self.inputs)-1):
            socket_to_remove = self.outputs[-1]
            for link in list(socket_to_remove.links):
                self.id_data.links.remove(link)
            self.outputs.remove(socket_to_remove)

        for I in range(max(1, len(self.outputs)), len(self.inputs)-1):
            IDX = I+1
            output_name  = f"data_{IDX}"
            output_label = f"Data_{IDX}"
            self.outputs.new('SvStringsSocket', output_name)
            self.outputs[output_name].label = output_label
            force_reload_config = True
            pass

        if not self.levels_config or self.load_levels_config or force_reload_config==True:
            self.reload_config(datas)

        # Сбрасывать в любом случае
        self.load_levels_config = False


        res = []
        force_reload_config = False
        if self.levels_config: # and any([e.flatten for e in self.levels_config])==True or any([e.wrap for e in self.levels_config])==True:
            levels_config = [(2 if info.flatten else 0) | (1 if info.wrap else 0) for info in self.levels_config]
            for data in datas:
                if data:
                    (res1, _force_reload_config) = recursive_unpack(data, levels_config)
                    force_reload_config |= _force_reload_config
                else:
                    res1 = []
                res.append(res1)
            pass
        else:
            res = datas

        if force_reload_config==True:
            self.reload_config(datas)

        for I, res1 in enumerate(res):
            if self.outputs[I].is_linked:
                self.outputs[I].sv_set(res1)
        return


classes = [SvNestingLevelEntryMK3, SvListLevelsNodeMK3]
register, unregister = bpy.utils.register_classes_factory(classes)
