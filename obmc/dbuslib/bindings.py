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

BUS_PREFIX = 'org.openbmc'
OBJ_PREFIX = "/org/openbmc"
BUS = "system"


def is_unique(connection):
    return connection[0] == ':'


def get_system_name():
    #use filename as system name, strip off path and ext
    parts = __file__.replace('.pyc', '').replace('.py', '').split('/')
    return parts[len(parts)-1]


def get_dbus():
    bus = None
    if (BUS == "session"):
        bus = dbus.SessionBus()
    else:
        bus = dbus.SystemBus()
    return bus


class DbusProperties(dbus.service.Object):
    def __init__(self):
        dbus.service.Object.__init__(self)
        self.properties = {}
        self.object_path = ""

    @dbus.service.method(
        dbus.PROPERTIES_IFACE,
        in_signature='ss', out_signature='v')
    def Get(self, interface_name, property_name):
        d = self.GetAll(interface_name)
        try:
            v = d[property_name]
            return v
        except:
            raise dbus.exceptions.DBusException(
                "org.freedesktop.UnknownProperty: "+property_name)

    @dbus.service.method(
        dbus.PROPERTIES_IFACE,
        in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface_name):
        try:
            d = self.properties[interface_name]
            return d
        except:
            raise dbus.exceptions.DBusException(
                "org.freedesktop.UnknownInterface: "+interface_name)

    @dbus.service.method(
        dbus.PROPERTIES_IFACE,
        in_signature='ssv')
    def Set(self, interface_name, property_name, new_value):
        if (interface_name not in self.properties):
            self.properties[interface_name] = {}
        try:
            old_value = self.properties[interface_name][property_name]
            if (old_value != new_value):
                self.properties[interface_name][property_name] = new_value
                self.PropertiesChanged(
                    interface_name, {property_name: new_value}, [])

        except:
            self.properties[interface_name][property_name] = new_value
            self.PropertiesChanged(
                interface_name, {property_name: new_value}, [])

    @dbus.service.method(
        "org.openbmc.Object.Properties", in_signature='sa{sv}')
    def SetMultiple(self, interface_name, prop_dict):
        if (interface_name not in self.properties):
            self.properties[interface_name] = {}

        value_changed = False
        for property_name in prop_dict:
            new_value = prop_dict[property_name]
            try:
                old_value = self.properties[interface_name][property_name]
                if (old_value != new_value):
                    self.properties[interface_name][property_name] = new_value
                    value_changed = True

            except:
                self.properties[interface_name][property_name] = new_value
                value_changed = True
        if (value_changed is True):
            self.PropertiesChanged(interface_name, prop_dict, [])

    @dbus.service.signal(
        dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(
            self, interface_name, changed_properties, invalidated_properties):
        pass


class DbusObjectManager(dbus.service.Object):
    def __init__(self):
        dbus.service.Object.__init__(self)
        self.objects = {}

    def add(self, object_path, obj):
        self.objects[object_path] = obj
        self.InterfacesAdded(object_path, obj.properties)

    def remove(self, object_path):
        obj = self.objects.pop(object_path, None)
        obj.remove_from_connection()
        self.InterfacesRemoved(object_path, obj.properties.keys())

    def get(self, object_path, default=None):
        return self.objects.get(object_path, default)

    @dbus.service.method(
        "org.freedesktop.DBus.ObjectManager",
        in_signature='', out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        data = {}
        for objpath in self.objects.keys():
            data[objpath] = self.objects[objpath].properties
        return data

    @dbus.service.signal(
        "org.freedesktop.DBus.ObjectManager", signature='oa{sa{sv}}')
    def InterfacesAdded(self, object_path, properties):
        self.ObjectAdded(object_path, "")

    @dbus.service.signal(
        "org.freedesktop.DBus.ObjectManager", signature='oas')
    def InterfacesRemoved(self, object_path, interfaces):
        pass

    ## Legacy support, need to eventually refactor out
    @dbus.service.signal(
        "org.openbmc.Object.ObjectMapper", signature='ss')
    def ObjectAdded(self, object_path, interface_name):
        pass

    ## flattens interfaces
    @dbus.service.method(
        'org.openbmc.Object.Enumerate', in_signature='',
        out_signature='a{sa{sv}}')
    def enumerate(self):
        data = {}
        for objpath in self.objects.keys():
            props = self.objects[objpath].properties
            data[objpath] = {}
            for iface in props.keys():
                data[objpath].update(props[iface])

        return data
