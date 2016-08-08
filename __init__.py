# -*- coding: utf-8 -*-
"""
/***************************************************************************
 kmeans
                                 A QGIS plugin
 This plugin clusters for point features by k-means.
                             -------------------
        begin                : 2016-06-16
        copyright            : (C) 2016 by Mengsheng Lu
        email                : lumengsheng@whu.edu.cn
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
    from PyQt4.QtGui import QMessageBox

    wnd = iface.mainWindow()

    try:
        import matplotlib.backends.backend_qt4agg
    except ImportError:
        QMessageBox.warning(wnd,
                            wnd.tr("Error while loading plugin"),
                            wnd.tr("Could not find the matplotlib module.\nMake sure the matplotlib is installed")
                           )

        raise ImportError("Missing matplotlib Python module")
    """Load kmeans class from file kmeans.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .kmeans import kmeans
    return kmeans(iface)
