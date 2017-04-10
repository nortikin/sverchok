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

import webbrowser


def launch_browser_search(type_of_search, input_string):
    
    search_tail = ''
    search_term = input_string.rsplit('?', 1)[0]

    if type_of_search == 'bpy docs':
        search_head = 'https://docs.blender.org/api/blender_python_api_current/search.html?q='
        search_tail = '&check_keywords=yes&area=default'

    elif type_of_search == 'by docs':
        search_head = 'http://docs.python.org/3/search.html?q='

    elif type_of_search == 'sv docs':
        search_head = "http://sverchok.readthedocs.io/en/latest/search.html?q="
        search_tail = "&check_keywords=yes&area=default"

    elif type_of_search == 'github code':
        search_head = "https://github.com/nortikin/sverchok/search?utf8=%E2%9C%93&q="
        search_tail = "&type="

    elif type_of_search == 'github issues':
        search_head = "https://github.com/nortikin/sverchok/issues?utf8=%E2%9C%93&q=is%3Aissue%20"

    try:
        full_url_term = ''.join([search_head, search_term, search_tail])
        webbrowser.open(full_url_term)
    except Exception as err:
        print('unable to browse {0} online'.format(type_of_search))
        print(repr(err))



def routing_table(input_string):
    if input_string.endswith(r'?bpy'):
        type_of_search = 'bpy docs'
    elif input_string.endswith(r'?py'):
        type_of_search = 'py docs'
    elif input_string.endswith(r'?sv'):
        type_of_search = 'sv docs'
    elif input_string.endswith(r'?ghc'):
        type_of_search = 'github code'
    elif input_string.endswith(r'?gh'):
        type_of_search = 'github issues'
    else:
        return False

    launch_browser_search(type_of_search, input_string)
    return True
