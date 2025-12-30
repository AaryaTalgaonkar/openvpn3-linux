#!/usr/bin/python3
#
#  OpenVPN 3 Linux client -- Next generation OpenVPN client
#
#  SPDX-License-Identifier: AGPL-3.0-only
#
#  Copyright (C) 2025-  OpenVPN Inc <sales@openvpn.net>
#  Copyright (C) 2025-  David Sommerseth <davids@openvpn.net>
#

import datetime
import dbus
import openvpn3
import os
import sys
import time
from dbus.mainloop.glib import DBusGMainLoop
from openvpn3.constants import SessionManagerEventType, StatusMajor, StatusMinor
from gi.repository import GLib

# Global main loop object
mainloop = GLib.MainLoop()

# If the 'OPENVPN3_DEBUG' environment variable is found, debug logging will
# be enabled and sent to the console
OPENVPN3_DEBUG=os.getenv('OPENVPN3_DEBUG') is not None

def DEBUG(msg):
    if OPENVPN3_DEBUG:
        print(msg)


class Notify(object):
    """
    Simple class interacting with the desktop notification API provided
    via the session D-Bus.  This API is documented here:
    https://specifications.freedesktop.org/notification-spec/notification-spec-latest.html
    """
    def __init__(self):
        self.__bus = dbus.SessionBus()

        object_connected = False
        while object_connected == False:
            try:
                self.__object = self.__bus.get_object('org.freedesktop.Notifications', '/org/freedesktop/Notifications')
                object_connected = True
            except dbus.exceptions.DBusException:
                print('Waiting for org.freedesktop.Notifications to become available')
                time.sleep(10)

        self.__notify_method = self.__object.get_dbus_method('Notify','org.freedesktop.Notifications')
        self.__close_notify_method = self.__object.get_dbus_method('CloseNotification','org.freedesktop.Notifications')
        self.__auth_notif = {}
        self.__reconn_notif = {}


    def __notify(self, title, msg):
        nid = self.__notify_method('OpenVPN 3 Linux', 0, 'network', title, msg, {}, {}, 0)
        DEBUG('Notification ({}): title="{}", msg="{}"'.format(nid, title, msg))


    def __close_notify(self, nid):
        if nid is None:
            return
        self.__close_notify_method(nid)
        DEBUG('Closed notification ID {}'.format(nid))


    def WebAuthenticate(self, path, url):
        """
        An on-going VPN session is requesting authentication via a web portal, notify the user
        with the appropriate URL to do the authentication
        """

        if path in self.__auth_notif:
            self.CloseNotification('auth', path)
        self.__auth_notif[path] = self.__notify('OpenVPN - Authentication Required',
                                                'Visit {}'.format(url))


    def Connected(self, path, name):
        if path in self.__auth_notif:
            self.CloseNotification('auth', path)
        self.__auth_notif[path] = self.__notify('OpenVPN - Authentication Successful',
                                                'OpenVPN session "{}" connected successfully'.format(name))


    def Reconnecting(self, path, name):
        "A reconnection has started, inform the user"

        if path in self.__reconn_notif:
            self.CloseNotification('reconnect', path)
        self.__reconn_notif[path] = self.__notify('OpenVPN session reconnecting',
                                                  'Session "{}" is reconnecting'.format(name))


    def Reconnected(self, path, name):
        "The reconnection was successful, inform the user"

        if path in self.__reconn_notif:
            self.CloseNotification('reconnect', path)
        self.__reconn_notif[path] = self.__notify('OpenVPN session reconnected',
                                                  'Session "{}" reconnected successfully'.format(name))


    def Disconnected(self, path, name):
        "The VPN session was disconnected, notify the user"

        if path in self.__auth_notif:
            self.CloseNotification('auth', path)
        if path in self.__reconn_notif:
            self.CloseNotification('reconnect', path)

        self.__reconn_notif[path] = self.__notify('OpenVPN session disconnected',
                                                  'Session "{}" was disconnected'.format(name))


    def CloseNotification(self, group, path):
        "Close any open notifications for the given session path"

        if 'auth' == group:
            if path in self.__auth_notif:
                self.__close_notify(self.__auth_notif[path])
        elif 'reconnect' == group:
            if path in self.__reconn_notif:
                self.__close_notify(self.__reconn_notif[path])




class SessionWatcher(object):
    """
    This sets up a StatusChange event listener for a specific VPN session.
    On certain events, a desktop notification will be triggered
    """

    def __init__(self, notify, session):
        """
        Prepares a new SessionWatcher.  The notify argument must be pointing
        at an existing Notify object.  The session argument must be an
        openvpn3.Session object.
        """

        self.__notify = notify
        self.__session = session
        self.__reconnecting = False

        # Wait for the session to settle a bit before
        # trying to interact with it
        time.sleep(1)
        self.__path = self.__session.GetPath()
        self.__cfgname = self.__session.GetProperty('config_name')

        # Set up StatusChange event handler for this session
        self.__session.StatusChangeCallback(self.__status_chg_handler)
        DEBUG('Starting SessionWatcher("{}")'.format(self.__path))


    def __status_chg_handler(self, major, minor, msg):
        """
        The internal StatusChange event handler which is called each time
        the status changes for the VPN session
        """

        # Convert the input arguments to openvpn3 constant values
        maj = openvpn3.StatusMajor(major)
        min = openvpn3.StatusMinor(minor)
        self.__evaluate_status(maj, min, msg)


    def __evaluate_status(self, major, minor, msg):
        """
        Internal method to validate the session status
        and act upon certain statuses
        """
        DEBUG('{tstamp} StatusChange({maj}, {min}) {msg}'.format(tstamp=datetime.datetime.now(),
                                                                 maj=major, min=minor, msg=msg))

        #  Handle certain events
        if StatusMajor.SESSION == major:
            if StatusMinor.SESS_AUTH_URL == minor:
                self.__notify.WebAuthenticate(self.__path, msg)
                return
        elif StatusMajor.CONNECTION == major:
            DEBUG('flags: reconnecting={}'.format(self.__reconnecting))
            if StatusMinor.CONN_CONNECTED == minor:
                if self.__reconnecting is False:
                    self.__notify.Connected(self.__path, self.__cfgname)
                else:
                    self.__notify.Reconnected(self.__path, self.__cfgname)
                    self.__reconnecting = False
                return
            elif StatusMinor.CONN_RECONNECTING == minor:
                self.__notify.Reconnecting(self.__path, self.__cfgname)
                self.__reconnecting = True
                return
            elif StatusMinor.CONN_DISCONNECTED == minor:
                self.__notify.Disconnected(self.__path, self.__cfgname)
                return


    def CheckStatus(self):
        "Check and evaluate the status of the session"

        status = self.__session.GetStatus()
        self.__evaluate_status(status['major'], status['minor'], status['message'])


    def Stop(self):
        "Stops the current SessionWatcher.  This object is inactive after this call."

        DEBUG('Stopping SessionWatcher("{}")'.format(self.__path))
        self.__notify.CloseNotification('auth', self.__path)
        self.__session.StatusChangeCallback(None)



class SessionManagerWatcher(object):
    """
    The SessionManagerWatcher object will listen to any StatusManagerEvents happening.
    These events contains information about VPN sessions starting up or shutting down,
    which is used to pick up the VPN session paths to further add additional checks."
    """

    def __init__(self, sessmgr):
        """
        Prepares the SessionManagerWathcer object.  The sessmgr argument must point
        "at an instantiated openvpn3.SessionManager() object.
        """

        # Sets up the notification interface
        self.__notify = Notify()

        # Sets up the event listener for manager event
        self.__sessmgr = sessmgr
        self.__sessmgr.SessionManagerCallback(self.__mgr_event_handler)

        # Initializes the list of sessions being monitored
        self.__sessions = {}


    def __mgr_event_handler(self, event):
        "Event handler method for StatusManagerEvents"

        # If debug logging is enabled, provide information on events
        DEBUG('{tstamp} {event}'.format(tstamp=datetime.datetime.now(),
                                            event=str(event)))

        # Only care about VPN sessions the currently running user or root owns.
        # The reaons for root owned VPNs is that systemd managed sessions are
        # started by root.
        if event.GetOwner() in [os.getuid(), 0]:
            if SessionManagerEventType.SESS_CREATED == event.GetType():
                # If it's a new VPN session, register to be able to track it
                self.Register(event.GetPath())
            elif SessionManagerEventType.SESS_DESTROYED == event.GetType():
                # If the VPN session is being removed, check if we're
                # monitoring it before shutting it down from our end as well
                if event.GetPath() in self.__sessions:
                    self.__sessions[event.GetPath()].Stop()
                    self.__sessions.pop(event.GetPath())


    def Register(self, path):
        "Registers a new VPN session for monitoring"
        DEBUG('SessionManagerWatcher::Register({})'.format(path))

        # Retrieve the openvpn3.Session object from the D-Bus path
        # and track a dedicated SessionWatcher object for this session
        session = self.__sessmgr.Retrieve(path)
        self.__sessions[path] = SessionWatcher(self.__notify, session)


    def CheckStatus(self, session_path):
        "Check and evaluate the session status for a specific session"

        if session_path in self.__sessions:
            self.__sessions[session_path].CheckStatus()


#
#
#  MAIN PROGRAM
#
#
if __name__ == "__main__":
    # Get a connection to the D-Bus' system bus
    dbusloop = DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus(mainloop=dbusloop)

    # Connect to the session manager, setup a session manager wathcer
    # which will listen to global events from this manager
    sessmgr = openvpn3.SessionManager(bus)
    mgrwatcher = SessionManagerWatcher(sessmgr)

    # Register existing running sessions
    for session in sessmgr.FetchAvailableSessions():
        mgrwatcher.Register(session.GetPath())
        mgrwatcher.CheckStatus(session.GetPath())

    # Start the main process
    try:
        mainloop.run()
    except KeyboardInterrupt: # Wait for CTRL-C / SIGINT
        print("\nExiting")

    sys.exit(0)
