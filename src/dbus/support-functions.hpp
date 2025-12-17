//  OpenVPN 3 Linux client -- Next generation OpenVPN client
//
//  SPDX-License-Identifier: AGPL-3.0-only
//
//  Copyright (C) 2025-  OpenVPN Inc <sales@openvpn.net>
//  Copyright (C) 2025-  David Sommerseth <davids@openvpn.net>
//

/**
 * @file support-functions.hpp
 *
 * @brief GDBus++ support functions not currently available in
 *        the GDBus++ release OpenVPN 3 Linux targets.
 */

#pragma once

#include <gdbuspp/proxy.hpp>

/**
 *  Support function for features lacking in GDBus++ v3 and older
 *
 *  This is a more lightweight approach to check if an object exists,
 *  through inspecting the Introspection data of the service.
 *
 *  Most of this code is taken from a newer GDBUs++ codebase and adopted
 *  to fit into OpenVPN 3 Linux.  For the current OpenVPN 3 Linux release,
 *  we do not want to upgrade the GDBus++ library.
 *
 *  FIXME:  Remove this function when upgrading to GDBus++ v4 or newer
 *
 * @param proxy   DBus::Proxy::Client to use for quering a D-Bus service
 * @param path    DBus::Object::Path of the object to check for
 * @return true if the object is found in the introspection data, otherwise false
 */


namespace GDBusPP::Proxy::Utils {

bool LookupObject(DBus::Proxy::Client::Ptr proxy, const DBus::Object::Path &path);

}