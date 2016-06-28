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

import xml.etree.ElementTree as ET
import dbus
import obmc.dbuslib.enums


class IntrospectionNodeParser:
    def __init__(self, data, tag_match=bool, intf_match=bool):
        self.data = data
        self.cache = {}
        self.tag_match = tag_match
        self.intf_match = intf_match

    def parse_args(self):
        return [x.attrib for x in self.data.findall('arg')]

    def parse_children(self):
        return [x.attrib['name'] for x in self.data.findall('node')]

    def parse_method_or_signal(self):
        name = self.data.attrib['name']
        return name, self.parse_args()

    def parse_interface(self):
        iface = {}
        iface['method'] = {}
        iface['signal'] = {}

        for node in self.data:
            if node.tag not in ['method', 'signal']:
                continue
            if not self.tag_match(node.tag):
                continue
            p = IntrospectionNodeParser(
                node, self.tag_match, self.intf_match)
            n, element = p.parse_method_or_signal()
            iface[node.tag][n] = element

        return iface

    def parse_node(self):
        if self.cache:
            return self.cache

        self.cache['interfaces'] = {}
        self.cache['children'] = []

        for node in self.data:
            if node.tag == 'interface':
                p = IntrospectionNodeParser(
                    node, self.tag_match, self.intf_match)
                name = p.data.attrib['name']
                if not self.intf_match(name):
                    continue
                self.cache['interfaces'][name] = p.parse_interface()
            elif node.tag == 'node':
                self.cache['children'] = self.parse_children()

        return self.cache

    def get_interfaces(self):
        return self.parse_node()['interfaces']

    def get_children(self):
        return self.parse_node()['children']

    def recursive_binding(self):
        return any('/' in s for s in self.get_children())


class IntrospectionParser:
    def __init__(self, name, bus, tag_match=bool, intf_match=bool):
        self.name = name
        self.bus = bus
        self.tag_match = tag_match
        self.intf_match = intf_match

    def _introspect(self, path):
        try:
            obj = self.bus.get_object(self.name, path, introspect=False)
            iface = dbus.Interface(obj, dbus.INTROSPECTABLE_IFACE)
            data = iface.Introspect()
        except dbus.DBusException:
            return None

        return IntrospectionNodeParser(
            ET.fromstring(data),
            self.tag_match,
            self.intf_match)

    def _discover_flat(self, path, parser):
        items = {}
        interfaces = parser.get_interfaces().keys()
        if interfaces:
            items[path] = {}
            items[path]['interfaces'] = interfaces

        return items

    def introspect(self, path='/', parser=None):
        items = {}
        if not parser:
            parser = self._introspect(path)
        if not parser:
            return {}
        items.update(self._discover_flat(path, parser))

        if path != '/':
            path += '/'

        if parser.recursive_binding():
            callback = self._discover_flat
        else:
            callback = self.introspect

        for k in parser.get_children():
            parser = self._introspect(path + k)
            if not parser:
                continue
            items.update(callback(path + k, parser))

        return items


def find_dbus_interfaces(conn, service, path, match):
    class _FindInterfaces(object):
        def __init__(self):
            self.results = {}

        @staticmethod
        def _get_object(path):
            try:
                return conn.get_object(service, path, introspect=False)
            except dbus.exceptions.DBusException, e:
                if e.get_dbus_name() in [
                        obmc.dbuslib.enums.DBUS_UNKNOWN_SERVICE,
                        obmc.dbuslib.enums.DBUS_NO_REPLY]:
                    print "Warning: Introspection failure: " \
                        "service `%s` is not running" % (service)
                    return None
                raise

        @staticmethod
        def _invoke_method(path, iface, method, *args):
            obj = _FindInterfaces._get_object(path)
            if not obj:
                return None

            iface = dbus.Interface(obj, iface)
            try:
                f = getattr(iface, method)
                return f(*args)
            except dbus.exceptions.DBusException, e:
                if e.get_dbus_name() in [
                        obmc.dbuslib.enums.DBUS_UNKNOWN_SERVICE,
                        obmc.dbuslib.enums.DBUS_NO_REPLY]:
                    print "Warning: Introspection failure: " \
                        "service `%s` did not reply to "\
                        "method call on %s" % (service, path)
                    return None
                raise

        @staticmethod
        def _introspect(path):
            return _FindInterfaces._invoke_method(
                path,
                dbus.INTROSPECTABLE_IFACE,
                'Introspect')

        @staticmethod
        def _get_managed_objects(om):
            return _FindInterfaces._invoke_method(
                om,
                dbus.BUS_DAEMON_IFACE + '.ObjectManager',
                'GetManagedObjects')

        @staticmethod
        def _to_path(elements):
            return '/' + '/'.join(elements)

        @staticmethod
        def _to_path_elements(path):
            return filter(bool, path.split('/'))

        def __call__(self, path):
            self.results = {}
            self._find_interfaces(path)
            return self.results

        @staticmethod
        def _match(iface):
            return iface == dbus.BUS_DAEMON_IFACE + '.ObjectManager' \
                or match(iface)

        def _find_interfaces(self, path):
            path_elements = self._to_path_elements(path)
            path = self._to_path(path_elements)
            data = self._introspect(path)
            if data is None:
                return

            root = ET.fromstring(data)
            ifaces = filter(
                self._match,
                [x.attrib.get('name') for x in root.findall('interface')])
            self.results[path] = ifaces

            if dbus.BUS_DAEMON_IFACE + '.ObjectManager' in ifaces:
                objs = self._get_managed_objects(path)
                for k, v in objs.iteritems():
                    self.results[k] = v
            else:
                children = filter(
                    bool,
                    [x.attrib.get('name') for x in root.findall('node')])
                children = [
                    self._to_path(
                        path_elements + self._to_path_elements(x))
                    for x in sorted(children)]
                for child in children:
                    if child not in self.results:
                        self._find_interfaces(child)

    return _FindInterfaces()(path)
