# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


def adjacent_edg_pol(verts, edg_pol):
    '''calculate number of adjacent faces '''
    adj_edg_pol = [0 for v in verts]
    for ep in edg_pol:
        for v in ep:
            adj_edg_pol[v] += 1

    return adj_edg_pol
