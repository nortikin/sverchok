# BEGIN GPL LICENSE BLOCK #####
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
# END GPL LICENSE BLOCK #####

# author Linus Yng

def recursive_depth(l):
    if isinstance(l, (list, tuple)) and l:
        return 1 + recursive_depth(l[0])
    elif isinstance(l, (int, float, str)):
        return 0
    else:
        return None

def vectorize(*args, **kwargs):
    # find level
    
    if (isinstance(l1, (int, float)) and isinstance(l2, (int, float))):
            return f(l1, l2)
            
    if (isinstance(l2, (list, tuple)) and isinstance(l1, (list, tuple))):
        fl = l2[-1] if len(l1) > len(l2) else l1[-1]
        res = []
        res_append = res.append
        for x, y in zip_longest(l1, l2, fillvalue=fl):
            res_append(self.recurse_fxy(x, y, f))
        return res
    
    # non matching levels    
    if isinstance(l1, (list, tuple)) and isinstance(l2, (int, float)):
        return self.recurse_fxy(l1, [l2], f)
    if isinstance(l1, (int, float)) and isinstance(l2, (list, tuple)):
        return self.recurse_fxy([l1], l2, f)

class SvScript:

    def pre(self):
        '''
        Function run before
        '''
        pass
    
    def post(self):
        pass
        
    def func(self):
        pass
    
    def process(self):

        self.func()


class MyScriptNode( SvScriptNode):
.
