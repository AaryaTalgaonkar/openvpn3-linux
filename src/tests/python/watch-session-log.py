#!/usr/bin/python3
#  OpenVPN 3 Linux client -- Next generation OpenVPN client
#
#  SPDX-License-Identifier: AGPL-3.0-only
#
#  Copyright (C) 2025 -       OpenVPN Inc <sales@openvpn.net>
#  Copyright (C) 2025 -       David Sommerseth <dazo@eurephia.org>

import argparse
import datetime
import dbus
import sys
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

import openvpn3
from openvpn3 import StatusMajor, StatusMinor

# Prepare a globla glib2 Main Loop object, required
# for asynchronous event handling
mainloop = GLib.MainLoop()


# Log event callback function, called each time a
# net.openvpn.v3.session.Log signal is sent by the
# OpenVPN 3 Session Manager
def LogHandler(group, catg, msg):
    loglines = [l for l in msg.split('\n') if len(l) > 0]
    if len(loglines) < 1:
        return

    print('%s [LOG] %s' % (datetime.datetime.now(), loglines[0]))
    for line in loglines[1:]:
        print('%s%s' % (' ' * 33, line))

# Status change event callback function, called each time a
# net.openvpn.v3.session.StatusChange signal is sent by the
# OpenVPN 3 Session Manager
def StatusHandler(major, minor, msg):
    maj = StatusMajor(major)
    min = StatusMinor(minor)

    print('%s [STATUS] (%s, %s) %s' % (datetime.datetime.now(), maj, min, msg))

    # Session got most likely disconnected outside of this program
    if StatusMajor.SESSION == maj and StatusMinor.PROC_STOPPED == min:
        mainloop.quit()
    if StatusMajor.CONNECTION == maj and StatusMinor.CONN_AUTH_FAILED == min:
        mainloop.quit()
    if StatusMajor.CONNECTION == maj and StatusMinor.CONN_FAILED == min:
        mainloop.quit()
    if StatusMajor.CONNECTION == maj and StatusMinor.CONN_DISCONNECTED == min:
        mainloop.quit()


if __name__ == '__main__':
    # Prepare an argument parser
    optparser = argparse.ArgumentParser('watch-session-log',
                                        description='Prints log events for an OpenVPN session to the console')
    optparser.add_argument('-l','--log-level', nargs=1,
                           metavar='LOG-LEVEL',
                           help='Log verbosity level, range 1 to 6')
    sessionopts = optparser.add_mutually_exclusive_group()
    sessionopts.add_argument('-c','--config', nargs=1,
                             metavar='CONFIG-NAME',
                             help='Lookup a running VPN session with the given configuration name')
    sessionopts.add_argument('-p','--path', nargs=1,
                             metavar='SESSION-PATH',
                             help='Use the given D-Bus path to the running VPN session')
    opts = optparser.parse_args(sys.argv[1:])

    # Setup the D-Bus mainloop and connect to the system bus
    dbusloop = DBusGMainLoop(set_as_default=True)
    sysbus = dbus.SystemBus(mainloop=dbusloop)

    # Connect to the OpenVPN 3 Session Manager
    sessionmgr = openvpn3.SessionManager(sysbus)

    # Find the D-Bus object path to the requested VPN session
    session_path = None
    if opts.config is not None:
        # Lookup the D-Bus session path from a configuration name
        search = sessionmgr.LookupConfigName(opts.config[0])
        if len(search) == 0:
            optparser.error('No VPN session found with the "%s" configuration name' % opts.config[0])
        elif len(search) > 1:
            optparser.error('More than one running VPN session was found under the name "%s". Use --path instead' % opts.config[0])
        session_path = dbus.ObjectPath(search[0])
    elif opts.path is not None:
        session_path = dbus.ObjectPath(opts.path[0])
    else:
        optparser.error('One of --config or --path must be provided')

    # Retrieve the Session object for this VPN session
    # and prepare the callback handler for log and status change events
    session = sessionmgr.Retrieve(session_path)
    session.LogCallback(LogHandler)
    session.StatusChangeCallback(StatusHandler)

    # If a specific log level is required, set that
    if opts.log_level is not None:
        session.SetProperty('log_verbosity', dbus.UInt32(opts.log_level[0]))

    #  Start the main loop and wait for log and status change events
    try:
        mainloop.run()
    except KeyboardInterrupt:
        print("Stopping")

    # Disable the log callback, this will also clean up
    # the log proxy infrastructure in the OpenVPN 3 Session Manager
    session.LogCallback(None)

    sys.exit(0)
