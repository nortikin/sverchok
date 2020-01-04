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

import os
import os.path
#import subprocess

import sverchok

BRANCH = ""

def get_branch():
    global BRANCH

    # this commented out code needs revisiting at some point.

    # first use git to find branch
    # try:
    #     res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
    #                           stdout=subprocess.PIPE,
    #                           cwd=os.path.dirname(sverchok.__file__),
    #                           timeout=2)

    #     branch = str(res.stdout.decode("utf-8"))
    #     BRANCH = branch.rstrip()
    # except: # if does not work ignore it
    #     BRANCH = ""
    # if BRANCH:
    #     return

    # if the above failed we can dig deeper, if this failed we concede victory.
    try:
        head = os.path.join(os.path.dirname(sverchok.__file__), '.git', 'HEAD')
        branch = ""
        with open(head) as headfile:
            branch = headfile.readlines()[0].split("/")[-1]
        BRANCH = branch.rstrip()
    except:
        BRANCH = ""

    return BRANCH

def get_hash():
    get_branch()
    if BRANCH:
        path = os.path.join(os.path.dirname(sverchok.__file__), '.git', 'refs', 'heads', BRANCH)
        if os.path.exists(path):
            with open(path) as hashfile:
                return hashfile.readlines()[0].strip()[:8]
        else:
            return None
    else:
        return None

def get_version_string():
    version = ".".join(map(str, sverchok.bl_info['version']))
    branch = get_branch()
    if branch:
        version += ", branch " + branch
        hash = get_hash()
        if hash:
            version += ", commit " + hash
    return version

