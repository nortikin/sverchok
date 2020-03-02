# -*- coding: utf-8 -*-
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

extra_category_providers = []

def register_extra_category_provider(provider):
    global extra_category_providers
    extra_category_providers.append(provider)

def unregister_extra_category_provider(identifier):
    global extra_category_providers
    idx = None
    for i, provider in enumerate(extra_category_providers):
        if provider.identifier == identifier:
            idx = i
    if idx is None:
        raise Exception(f"Provider {identifier} was not registered")
    del extra_category_providers[idx]

def get_extra_categories():
    global extra_category_providers
    result = []
    for provider in extra_category_providers:
        result.extend(provider.get_categories())
    return result

