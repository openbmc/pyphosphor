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
import dbus.service
import dbus.exceptions

OBJ_PREFIX = '/xyz/openbmc_project'


def is_unique(connection):
    return connection[0] == ':'


def get_dbus():
    return dbus.SystemBus()


class DbusProperties(dbus.service.Object):
    def __init__(self, **kw):
        self.validator = kw.pop('validator', None)
        super(DbusProperties, self).__init__(**kw)
        self.properties = {}
        self._export = False

    def unmask_signals(self):
        self._export = True
        inst = super(DbusProperties, self)
        if hasattr(inst, 'unmask_signals'):
            inst.unmask_signals()

    def mask_signals(self):
        self._export = False
        inst = super(DbusProperties, self)
        if hasattr(inst, 'mask_signals'):
            inst.mask_signals()

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

        if self.validator:
            self.validator(interface_name, property_name, new_value)

        try:
            old_value = self.properties[interface_name][property_name]
            if (old_value != new_value):
                self.properties[interface_name][property_name] = new_value
                if self._export:
                    self.PropertiesChanged(
                        interface_name, {property_name: new_value}, [])

        except:
            self.properties[interface_name][property_name] = new_value
            if self._export:
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
        if (value_changed is True and self._export):
            self.PropertiesChanged(interface_name, prop_dict, [])

    @dbus.service.signal(
        dbus.PROPERTIES_IFACE, signature='sa{sv}as')
    def PropertiesChanged(
            self, interface_name, changed_properties, invalidated_properties):
        pass


class DbusObjectManager(dbus.service.Object):
    def __init__(self, **kw):
        super(DbusObjectManager, self).__init__(**kw)
        self.objects = {}
        self._export = False

    def unmask_signals(self):
        self._export = True
        inst = super(DbusObjectManager, self)
        if hasattr(inst, 'unmask_signals'):
            inst.unmask_signals()

    def mask_signals(self):
        self._export = False
        inst = super(DbusObjectManager, self)
        if hasattr(inst, 'mask_signals'):
            inst.mask_signals()

    def add(self, object_path, obj):
        self.objects[object_path] = obj
        if self._export:
            self.InterfacesAdded(object_path, obj.properties)

    def remove(self, object_path):
        obj = self.objects.pop(object_path, None)
        obj.remove_from_connection()
        if self._export:
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
        pass

    @dbus.service.signal(
        "org.freedesktop.DBus.ObjectManager", signature='oas')
    def InterfacesRemoved(self, object_path, interfaces):
        pass
