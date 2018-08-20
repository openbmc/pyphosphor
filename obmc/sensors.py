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

import os
import subprocess
import dbus
import dbus.service
from obmc.dbuslib.bindings import DbusProperties


# Abstract class, must subclass
class SensorValue(DbusProperties):
    IFACE_NAME = 'org.openbmc.SensorValue'

    def __init__(self, bus, name):
        self.Set(SensorValue.IFACE_NAME, 'units', "")
        self.Set(SensorValue.IFACE_NAME, 'error', False)

    @dbus.service.method(
        IFACE_NAME, in_signature='v', out_signature='')
    def setValue(self, value):
        self.Set(SensorValue.IFACE_NAME, 'value', value)

    @dbus.service.method(
        IFACE_NAME, in_signature='', out_signature='v')
    def getValue(self):
        return self.Get(SensorValue.IFACE_NAME, 'value')


class VirtualSensor(SensorValue):
    def __init__(self, bus, name):
        DbusProperties.__init__(self)
        SensorValue.__init__(self, bus, name)
        dbus.service.Object.__init__(self, bus, name)


CONTROL_IFACE = 'org.openbmc.Control'


