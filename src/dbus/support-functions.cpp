//  OpenVPN 3 Linux client -- Next generation OpenVPN client
//
//  SPDX-License-Identifier: AGPL-3.0-only
//
//  Copyright (C) 2025-  OpenVPN Inc <sales@openvpn.net>
//  Copyright (C) 2025-  David Sommerseth <davids@openvpn.net>
//

/**
 * @file support-functions.cpp
 *
 * @brief GDBus++ support functions not currently available in
 *        the GDBus++ release OpenVPN 3 Linux targets.
 *
 */

#include <string>
#include <regex>
#include <fmt/compile.h>
#include <fmt/format.h>
#include <gdbuspp/proxy.hpp>
#include <gdbuspp/proxy/utils.hpp>


namespace GDBusPP::Proxy::Utils {


bool LookupObject(DBus::Proxy::Client::Ptr proxy, const DBus::Object::Path &path)
{
    DBus::Object::Path parent_object_path;
    std::string child_object;
    auto split_point = path.find_last_of("/");
    if (split_point == std::string::npos)
    {
        throw DBus::Proxy::Exception("Invalid path - no separator character found");
    }

    // Split up the D-Bus object path into the parent object path
    // of the requested path, and preserve the final
    parent_object_path = {path.substr(0, split_point)};
    child_object = {path.substr(split_point + 1)};

    if (!parent_object_path.empty() && child_object.empty())
    {
        throw DBus::Proxy::Exception("Invalid D-Bus path - no trailing slash (/) allowed");
    }

    if (parent_object_path.empty())
    {
        parent_object_path = "/";
    }

    auto prxqry = DBus::Proxy::Utils::Query::Create(std::move(proxy));
    std::string introsp;
    for (uint8_t attempts = 3; attempts > 0; attempts--)
    {
        introsp = prxqry->Introspect(parent_object_path);
        if (introsp.length() > 218)
        {
            break;
        }
        usleep(100000);
    }

    if (introsp.length() > 218 && child_object.empty() && "/" == parent_object_path)
    {
        // This is a special case for checking the root (/) object
        // If the introspection didn't fail, the object exists.
        return true;
    }

    const std::regex lookup_expr{fmt::format(FMT_COMPILE("\\<node name=\"({})\"/\\>"),
                                             child_object)};
    std::smatch m;
    if (std::regex_search(introsp, m, lookup_expr))
    {
        // If a <node name="$child_object"/> element is found in the
        // introspection, only a single such node is expected.  The
        // check for m.size() == 2 is due to m[0] holding the whole regex
        // match, while m[1] holds just the content of the 'name' attribute.
        // The content of the 'name' attribute must match the requested
        // child_object.
        return (m.size() == 2 && m[1] == child_object);
    }
    return false;
}

} // namespace GDBusPP::Proxy::Utils