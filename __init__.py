# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BelgianAddressGeolocation
                                 A QGIS plugin
 Geolocate by official addresses
                             -------------------
        begin                : 2015-09-16
        copyright            : (C) 2015 by Peter Nuyts / Gitos
        email                : peter@gitos.be
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load BelgianAddressGeolocation class from file BelgianAddressGeolocation.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .BAG import BelgianAddressGeolocation
    return BelgianAddressGeolocation(iface)
