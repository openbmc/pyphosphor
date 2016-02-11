# Contributors Listed Below - COPYRIGHT 2016
# [+] International Business Machines Corp.
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

import dbus

MAPPER_NAME = 'org.openbmc.objectmapper'
MAPPER_IFACE = MAPPER_NAME + '.ObjectMapper'
MAPPER_PATH = '/org/openbmc/objectmapper/objectmapper'
ENUMERATE_IFACE = 'org.openbmc.Object.Enumerate'
MAPPER_NOT_FOUND = 'org.openbmc.objectmapper.Error.NotFound'


class Mapper:
    def __init__(self, bus):
        self.bus = bus
        obj = bus.get_object(MAPPER_NAME, MAPPER_PATH, introspect=False)
        self.iface = dbus.Interface(
            obj, dbus_interface=MAPPER_IFACE)

    def get_object(self, path):
        return self.iface.GetObject(path)

    def get_subtree_paths(self, path='/', depth=0):
        return self.iface.GetSubTreePaths(path, depth)

    def get_subtree(self, path='/', depth=0):
        return self.iface.GetSubTree(path, depth)

    def get_ancestors(self, path):
        return self.iface.GetAncestors(path)
