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


## Abstract class, must subclass
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


class BootProgressSensor(VirtualSensor):
    def __init__(self, bus, name):
        VirtualSensor.__init__(self, bus, name)
        self.setValue("Off")
        bus.add_signal_receiver(
            self.SystemStateHandler, signal_name="GotoSystemState")

    def SystemStateHandler(self, state):
        if (state == "HOST_POWERED_OFF"):
            self.setValue("Off")

    ##override setValue method
    @dbus.service.method(
        SensorValue.IFACE_NAME,
        in_signature='v', out_signature='')
    def setValue(self, value):
        SensorValue.setValue(self, value)
        if (value == "FW Progress, Starting OS"):
            self.GotoSystemState("HOST_BOOTED")
        self.BootProgress(value)

    @dbus.service.signal(CONTROL_IFACE, signature='s')
    def GotoSystemState(self, state):
        pass

    @dbus.service.signal(CONTROL_IFACE, signature='s')
    def BootProgress(self, state):
        pass


class BootCountSensor(VirtualSensor):
    def __init__(self, bus, name):
        VirtualSensor.__init__(self, bus, name)
        # Default boot count is 2.  Add 1 onto this to allow for an
        # SBE side switch boot attempt
        self.setValue(3)

    ## override setValue method for debug purposes
    @dbus.service.method(
        SensorValue.IFACE_NAME, in_signature='v', out_signature='')
    def setValue(self, value):
        print "Setting boot count to " + str(value)
        SensorValue.setValue(self, value)


class OperatingSystemStatusSensor(VirtualSensor):
    def __init__(self, bus, name):
        VirtualSensor.__init__(self, bus, name)
        self.setValue("Off")
        bus.add_signal_receiver(
            self.SystemStateHandler, signal_name="GotoSystemState")

    def SystemStateHandler(self, state):
        if (state == "HOST_POWERED_OFF"):
            self.setValue("Off")


class PowerSupplyRedundancySensor(VirtualSensor):
    def __init__(self, bus, name):
        VirtualSensor.__init__(self, bus, name)
        ## Setting default to enabled.
        super(PowerSupplyRedundancySensor, self).setValue(1)

    ## override setValue method
    @dbus.service.method(
        SensorValue.IFACE_NAME, in_signature='b', out_signature='')
    def setValue(self, value):
        print "Setting Power Supply Redundancy is not allowed"


class PowerSupplyDeratingSensor(VirtualSensor):
    def __init__(self, bus, name):
        VirtualSensor.__init__(self, bus, name)
        super(PowerSupplyDeratingSensor, self).setValue(10)

    ## override setValue method
    @dbus.service.method(
        SensorValue.IFACE_NAME, in_signature='v', out_signature='')
    def setValue(self, value):
        print "Setting Power Supply Derating is not allowed"


class TurboAllowedSensor(VirtualSensor):
    def __init__(self, bus, name):
        VirtualSensor.__init__(self, bus, name)
        self.setValue(0)

    ## override setValue method
    @dbus.service.method(
        SensorValue.IFACE_NAME, in_signature='b', out_signature='')
    def setValue(self, value):
        super(TurboAllowedSensor, self).setValue(value)
