# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import datetime

import bpy
from bpy.props import StringProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

reference_table = """\
Note: Examples are based (http://strftime.org/ ) on datetime.datetime(2013, 9, 30, 7, 6, 5)
Python Docs: https://docs.python.org/3.6/library/datetime.html#strftime-and-strptime-behavior
+-----+------------+---------------------
|Code | Catches    | Meaning Example
+=====+============+=====================
| %a  | Mon        | Weekday as locale’s abbreviated name.
| %A  | Monday     | Weekday as locale’s full name.
| %w  | 1          | Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.
| %d  | 30         | Day of the month as a zero-padded decimal number.
| %-d | 30         | Day of the month as a decimal number. (Platform specific)
| %b  | Sep        | Month as locale’s abbreviated name.
| %B  | September  | Month as locale’s full name.
| %m  | 09         | Month as a zero-padded decimal number.
| %-m | 9          | Month as a decimal number. (Platform specific)
| %y  | 13         | Year without century as a zero-padded decimal number.
| %Y  | 2013       | Year with century as a decimal number.
| %H  | 07         | Hour (24-hour clock) as a zero-padded decimal number.
| %-H | 7          | Hour (24-hour clock) as a decimal number. (Platform specific)
| %I  | 07         | Hour (12-hour clock) as a zero-padded decimal number.
| %-I | 7          | Hour (12-hour clock) as a decimal number. (Platform specific)
| %p  | AM         | Locale’s equivalent of either AM or PM.
| %M  | 06         | Minute as a zero-padded decimal number.
| %-M | 6          | Minute as a decimal number. (Platform specific)
| %S  | 05         | Second as a zero-padded decimal number.
| %-S | 5          | Second as a decimal number. (Platform specific)
| %f  | 000000     | Microsecond as a decimal number, zero-padded on the left.
| %z  | ?          | UTC offset in the form +HHMM or -HHMM (empty string if the the object is naive).
| %Z  | ?          | Time zone name (empty string if the object is naive).
| %j  | 273        | Day of the year as a zero-padded decimal number.
| %-j | 273        | Day of the year as a decimal number. (Platform specific)
| %U  | 39         | Week number of the year (Sunday as the first day of the week) as a zero padded decimal number.
|     |            | All days in a new year preceding the first Sunday are considered to be in week 0.
| %W  | 39         | Week number of the year (Monday as the first day of the week) as a decimal number.
|     |            | All days in a new year preceding the first Monday are considered to be in week 0.
| %c  | Mon Sep 30 07:06:05 2013 | Locale’s appropriate date and time representation.
| %x  | 09/30/13                 | Locale’s appropriate date representation.
| %X  | 07:06:05                 | Locale’s appropriate time representation.
| %%  | %                        | A literal '%' character.
+-----+--------------------------+

"""


class SvDatetimeStrings(bpy.types.Node, SverchCustomTreeNode):
    ''' a SvDatetimeStrings f '''
    bl_idname = 'SvDatetimeStrings'
    bl_label = 'Datetime Strings'
    bl_icon = 'SORTTIME'

    def show_short_reference(self, context):
        """ just keep writing to the table if it exists. """

        doc_name = "[DOC] strptime / strftime"
        texts = bpy.data.texts
        if not doc_name in texts:
            texts.new(doc_name)
        texts[doc_name].from_string(reference_table)


    time_offset: StringProperty(
        default="01/01/2018", update=updateNode,
        description="for graphing purposes you might need to subtract a start date", name='offset')

    calc_subordinal: BoolProperty(
        update=updateNode,
        name="Subordinal", 
        description="produces the ordinal with a subordinal - useful for timeseries with sub day precision"
    )

    date_pattern: StringProperty(
        default="%m/%d/%Y", update=updateNode,
        description="date formatting information", name="Date Time String Formatter")

    make_reference: BoolProperty(name="Make Reference in Texts", update=show_short_reference)
    float_to_int: BoolProperty(name="Float to Int", update=updateNode)

    def sv_init(self, context):
        self.inputs.new("SvStringsSocket", "times")
        self.inputs.new("SvStringsSocket", "time offset").prop_name = "time_offset"
        self.outputs.new("SvStringsSocket", "times")

    def draw_buttons(self, context, layout):
        layout.prop(self, "date_pattern", text="", icon="SORTTIME")
        layout.prop(self, "calc_subordinal", toggle=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "make_reference")
        layout.prop(self, "float_to_int")

    def sub_ordinal(self, value):
        stamp = datetime.datetime.strptime(value, self.date_pattern)
        seconds_in_day = 24*60*60
        f = (stamp.hour * 60 * 60) + (stamp.minute * 60) + stamp.second
        return f / seconds_in_day

    def process(self):

        V1 = self.inputs["times"].sv_get()
        V2 = self.inputs["time offset"].sv_get()

        if len(V1) == len(V2):
            # all times have an offset
            pass
        elif len(V1) == len(V2[0]):
            V2 = [[v] for v in V2[0]]
        elif len(V1) > len(V2) and len(V2):
            V1, V2 = match_long_repeat([V1, V2])
        else:
            print("see source code to show why execution is displaying this message")
            return

        VC_main = []
        for V, offset in zip(V1, V2):
            VC = []
            ordinal_offset = datetime.datetime.strptime(offset[0], self.date_pattern).toordinal()
            for value in V:
                value = value if not self.float_to_int else str(int(value))
                t = datetime.datetime.strptime(value, self.date_pattern).toordinal()
                m = t - ordinal_offset
                if self.calc_subordinal:
                    m = m + self.sub_ordinal(value)
                VC.append(m)
            VC_main.append(VC)

        self.outputs['times'].sv_set(VC_main)


def register():
    bpy.utils.register_class(SvDatetimeStrings)


def unregister():
    bpy.utils.unregister_class(SvDatetimeStrings)

