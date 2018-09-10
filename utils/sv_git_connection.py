# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from sverchok.utils.sv_gist_tools import get_git_login_hash

login_found = False

if get_git_login_hash():
    login_found = True


