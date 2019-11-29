# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

from sverchok.utils.context_managers import sv_preferences

login_found = False

with sv_preferences() as prefs:
    login_found = bool(prefs.github_token)


