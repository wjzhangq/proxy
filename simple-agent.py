#!/usr/bin/python

import gobject

import sys
import os
import dbus
import dbus.service
import dbus.mainloop.glib


class Rejected(dbus.DBusException):
    _dbus_error_name = "org.bluez.Error.Rejected"


class Agent(dbus.service.Object):
    exit_on_release = True
    pin = "1234"

    def set_exit_on_release(self, exit_on_release):
        self.exit_on_release = exit_on_release

    @dbus.service.method("org.bluez.Agent",
                         in_signature="", out_signature="")
    def Release(self):
        print "Release"
        my_cmds = [
            "kill `cat /tmp/pand.pid`",
            "iptables -t nat -D POSTROUTING -s 10.0.0.1/24 ! -d 10.0.0.1/24 -j SNAT --to 192.168.59.132",
            "iptables -t nat -D PREROUTING -p tcp -i pan1 -j REDIRECT --to-ports 12345",
            "iptables -D FORWARD -i pan1 ! -o pan1 -j ACCEPT",
            "iptables -D INPUT -i pan1 -j ACCEPT",
        ]
        for my_cmd in my_cmds:
            print my_cmd
            os.system(my_cmd)
        if self.exit_on_release:
            mainloop.quit()

    @dbus.service.method("org.bluez.Agent",
                         in_signature="os", out_signature="")
    def Authorize(self, device, uuid):
        print "Authorize (%s, %s)" % (device, uuid)

    @dbus.service.method("org.bluez.Agent",
                         in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        print "RequestPinCode (%s) is %s " % (device, self.pin)
        return self.pin

    @dbus.service.method("org.bluez.Agent",
                         in_signature="o", out_signature="u")
    def RequestPasskey(self, device):
        print "RequestPasskey (%s) is %s" % (device, self.pin)
        passkey = self.pin
        return dbus.UInt32(passkey)

    @dbus.service.method("org.bluez.Agent",
                         in_signature="ou", out_signature="")
    def DisplayPasskey(self, device, passkey):
        print "DisplayPasskey (%s, %d)" % (device, passkey)

    @dbus.service.method("org.bluez.Agent",
                         in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print "RequestConfirmation (%s, %d)" % (device, passkey)
        confirm = "yes"
        if (confirm == "yes"):
            return
        raise Rejected("Passkey doesn't match")

    @dbus.service.method("org.bluez.Agent",
                         in_signature="s", out_signature="")
    def ConfirmModeChange(self, mode):
        print "ConfirmModeChange (%s)" % (mode)

    @dbus.service.method("org.bluez.Agent",
                         in_signature="", out_signature="")
    def Cancel(self):
        print "Cancel"


def create_device_reply(device):
    print "New device (%s)" % (device)
    mainloop.quit()


def create_device_error(error):
    print "Creating device failed: %s" % (error)
    mainloop.quit()

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()
    manager = dbus.Interface(bus.get_object("org.bluez", "/"),
                             "org.bluez.Manager")

    if len(sys.argv) > 1:
        path = manager.FindAdapter(sys.argv[1])
    else:
        path = manager.DefaultAdapter()

    adapter = dbus.Interface(bus.get_object("org.bluez", path),
                             "org.bluez.Adapter")

    path = "/test/agent"
    agent = Agent(bus, path)

    mainloop = gobject.MainLoop()

    if len(sys.argv) > 2:
        if len(sys.argv) > 3:
            device = adapter.FindDevice(sys.argv[2])
            adapter.RemoveDevice(device)

        agent.set_exit_on_release(False)
        adapter.CreatePairedDevice(sys.argv[2], path, "DisplayYesNo",
                                   reply_handler=create_device_reply,
                                   error_handler=create_device_error)
    else:
        adapter.RegisterAgent(path, "DisplayYesNo")
        print "Agent registered"
        my_cmds = [
            "hciconfig hci0 up piscan",
            "modprobe bnep",
            "pand --listen --role NAP --master -P /tmp/pand.pid",
            "/etc/init.d/dhcpd restart",
            "iptables -t nat -D POSTROUTING -s 10.0.0.1/24 ! -d 10.0.0.1/24 -j SNAT --to 192.168.59.132",
            "iptables -t nat -I POSTROUTING -s 10.0.0.1/24 ! -d 10.0.0.1/24 -j SNAT --to 192.168.59.132",
            "iptables -t nat -D PREROUTING -p tcp -i pan1 -j REDIRECT --to-ports 12345",
            "iptables -t nat -I PREROUTING -p tcp -i pan1 -j REDIRECT --to-ports 12345",
            "iptables -D FORWARD -i pan1 ! -o pan1 -j ACCEPT",
            "iptables -I FORWARD -i pan1 ! -o pan1 -j ACCEPT",
            "iptables -D INPUT -i pan1 -j ACCEPT",
            "iptables -I INPUT -i pan1 -j ACCEPT"
        ]
        for my_cmd in my_cmds:
            print my_cmd
            os.system(my_cmd)     

    mainloop.run()

    # adapter.UnregisterAgent(path)
    # print "Agent unregistered"
