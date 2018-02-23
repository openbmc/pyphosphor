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
        self.bus = bus
        self.bus_name = 'xyz.openbmc_project.Settings'
        self.obj_path = '/xyz/openbmc_project/control/power_supply_redundancy'
        self.iface = 'xyz.openbmc_project.Control.PowerSupplyRedundancy'
        self.prop_iface = 'org.freedesktop.DBus.Properties'
        self.property_name = 'PowerSupplyRedundancyEnabled'
        super(PowerSupplyRedundancySensor, self).setValue(self.getValue())

    # Override setValue method
    @dbus.service.method(
        SensorValue.IFACE_NAME, in_signature='v', out_signature='')
    def setValue(self, value):
        if (value == "Enabled"):
            intf = self.getPowerSupplyInterface()
            intf.Set(self.iface, self.property_name, True)
        elif (value == "Disabled"):
            intf = self.getPowerSupplyInterface()
            intf.Set(self.iface, self.property_name, False)
        else:
            print "Invalid Power Supply Redundancy value"
            return
        super(PowerSupplyRedundancySensor, self).setValue(value)

    # Override getValue method
    @dbus.service.method(
        SensorValue.IFACE_NAME, in_signature='', out_signature='v')
    def getValue(self):
        intf = self.getPowerSupplyInterface()
        value = intf.Get(self.iface, self.property_name)
        if (value == 1):
            return "Enabled"
        elif (value == 0):
            return "Disabled"
        else:
            print "Unable to determine Power Supply Redundancy value"
            return ""

    def getPowerSupplyInterface(self):
        obj = self.bus.get_object(self.bus_name, self.obj_path,
                                  introspect=True)
        return dbus.Interface(obj, self.prop_iface)


class PowerSupplyDeratingSensor(VirtualSensor):
    def __init__(self, bus, name):
        VirtualSensor.__init__(self, bus, name)
        super(PowerSupplyDeratingSensor, self).setValue(90)

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
