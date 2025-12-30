================================
openvpn3-desktop-session-watcher
================================

---------------------------------
OpenVPN 3 Desktop Session Watcher
---------------------------------

:Manual section: 1
:Manual group: OpenVPN 3 Linux

SYNOPSIS
========
| ``openvpn3-desktop-session-watcher``
| ``systemctl --user {start,status,stop,enable,disable} openvpn3-desktop-session-watcher.service``


DESCRIPTION
===========
This is a simple utility for graphical desktop users which will
issue a notification event when VPN sessions are started, stopped
or otherwise changes status.  If the VPN session requires a web-based
authentication, the URL for the authentication is made easily
available in the desktop notification.

A `systemd` user service unit is provided as well, to start this
session watcher automatically during the desktop login.


To start the session watcher at login:

::

    $ systemctl --user enable --now openvpn3-desktop-session-watcher.service


To stop starting the session watcher at login:

::

    $ systemctl --user disable --now openvpn3-desktop-session-watcher.service

