//  OpenVPN 3 Linux client -- Next generation OpenVPN client
//
//  SPDX-License-Identifier: AGPL-3.0-only
//
//  Copyright (C) 2017-  OpenVPN Inc <sales@openvpn.net>
//  Copyright (C) 2017-  David Sommerseth <davids@openvpn.net>
//

/**
 * @file   utils.hpp
 *
 * @brief  Misc utility functions
 */

#pragma once

#include <ctime>
#include <string>

void drop_root();

/**
 *  Get the version string used to identify the product, program
 *  and version.
 *
 *  If a git checkout is discovered, flags identifying if there are
 *  uncommitted changes will added.  These flags are identified by
 *  a double underbar (__) and a character per flag.
 *
 *  Flags used are:  m - files are modified
 *                   s - some files are modified and staged in the git index
 *
 *
 * @param component  An additional string identifying which component this
 *                   version reference belongs to.  Normally argv[0].
 *
 * @return A pre-formatted std::string containing the version references
 */
std::string get_program_version(const std::string &component);


/**
 *  Returns a string contaiining only the release/git version
 *
 *  This value is typically used in the D-Bus services root
 *  object and represented in the 'version' property.
 *
 * @return const char* containing the version identifier.
 */
const char * get_package_version();

/**
 *  A variant of the get_program_version(), used
 *  in the OpenVPN protocol for the IV_GUI_VER peer-info
 *  field.
 *
 *  The format of this string must be:
 *     OpenVPN3/Linux/$VERSION
 *
 * @return const std::string containing the string to be
 *         used in the IV_GUI_VER field.
 */
const std::string get_guiversion();
int stop_handler(void *loop);
void set_console_echo(bool echo);

static inline std::string simple_basename(const std::string &filename)
{
    return filename.substr(filename.rfind('/') + 1);
}


/**
 *  Converts a time_t (epoch) value to a human readable
 *  date/time string, based on the local time zone.
 *
 * @param epoch         time_t value to convert
 * @return std::string containing the human readable representation
 */
std::string get_local_tstamp(std::time_t epoch);


/**
 *  Checks if the currently available console/terminal is
 *  capable of doing colours.
 *
 * @return bool, true if it is expected the terminal output can handle
 *               colours; otherwise false
 */
bool is_colour_terminal();
