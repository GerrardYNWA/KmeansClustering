# -*- coding: utf-8 -*-
"""
/***************************************************************************
 kmeansDialog
                                 A QGIS plugin
 This plugin clusters for point features by k-means.
                             -------------------
        begin                : 2016-06-16
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Mengsheng Lu
        email                : lumengsheng@whu.edu.cn
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os

from PyQt4 import QtGui, uic

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *

from ui_kmeans_dialog_base import Ui_KmeansDialog

import kmeans_utils as utils

import matplotlib
from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

version = matplotlib.__version__.split('.')
if int(version[0]) >= 1 and int(version[1]) >= 5:
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
else:
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'kmeans_dialog_base.ui'))


class kmeansDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(kmeansDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # add matplotlib figure to dialog
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self.figure)
        self.mpltoolbar = NavigationToolbar(self.canvas, self.widgetPlot)
        lstActions = self.mpltoolbar.actions()
        self.mpltoolbar.removeAction(lstActions[7])
        self.layoutPlot.addWidget(self.canvas)
        self.layoutPlot.addWidget(self.mpltoolbar)

        # and configure matplotlib params
        rcParams["font.serif"] = "Verdana, Arial, Liberation Serif"
        rcParams["font.sans-serif"] = "Tahoma, Arial, Liberation Sans"
        rcParams["font.cursive"] = "Courier New, Arial, Liberation Sans"
        rcParams["font.fantasy"] = "Comic Sans MS, Arial, Liberation Sans"
        rcParams["font.monospace"] = "Courier New, Liberation Mono"

        self.values = None
        self.outPath = None

        self.btnOk = self.buttonBox.button(QDialogButtonBox.Ok)
        self.btnClose = self.buttonBox.button(QDialogButtonBox.Close)
        self.openBtn.clicked.connect(self.saveFile)

        self.chkShowGrid.stateChanged.connect(self.refreshPlot)
        self.chkAsPlot.stateChanged.connect(self.refreshPlot)
        self.btnRefresh.clicked.connect(self.refreshPlot)

        self.manageGui()
        self.axes.set_title(unicode(self.tr(u"Statistic Plot")))

    def manageGui(self):
        self.cmbLayers.clear()
        self.cmbLayers.addItems(utils.getVectorLayerNames())

        self.btnRefresh.setEnabled(False)
		
    def accept(self):
        self.axes.clear()
        self.spnMinX.setValue(0.0)
        self.spnMaxX.setValue(0.0)
        self.lstStatistics.clearContents()
        self.lstStatistics.setRowCount(0)

        layer = utils.getVectorLayerByName(self.cmbLayers.currentText())

        statData = self.kmeansCluster(layer, self.cmbDis.currentIndex(), self.spnNum.value())
        self.processFinished(statData)
        self.addClassField(layer)
        self.progressBar.setValue(0)

    def reject(self):
        QDialog.reject(self)

    def setProgressRange(self, maxValue):
        self.progressBar.setRange(0, maxValue)

    def updateProgress(self):
        self.progressBar.setValue(self.progressBar.value() + 1)

    def processFinished(self, statData):
        # populate table with results
        self.tableData = statData[0]
        self.values = statData[1]
        rowCount = len(self.tableData)
        self.lstStatistics.setRowCount(rowCount)
        for i in xrange(rowCount):
            item = QTableWidgetItem(self.tr("%d") % (i))
            self.lstStatistics.setItem(i, 0, item)
            tmp = self.tableData[i]
            item = QTableWidgetItem(self.tr("%f") % (tmp[0]))
            self.lstStatistics.setItem(i, 1, item)
            item = QTableWidgetItem(self.tr("%f") % (tmp[1]))
            self.lstStatistics.setItem(i, 2, item)

        self.lstStatistics.resizeRowsToContents()

        self.btnRefresh.setEnabled(True)

        # create histogram
        self.refreshPlot()

    def saveFile(self):
        self.outPath = QFileDialog.getSaveFileName(self, u'保存文件',u"map","jpg(*.jpg)")
        self.lineEdit.setText(self.outPath)

    def refreshPlot(self):
        self.axes.clear()
        self.axes.set_title(unicode(self.tr("Statistic Plot")))
        interval = None

        if self.values is None:
            return

        if self.spnMinX.value() == self.spnMaxX.value():
            pass
        else:
            interval = []
            if self.spnMinX.value() > self.spnMaxX.value():
                interval.append(self.spnMaxX.value())
                interval.append(self.spnMinX.value())
            else:
                interval.append(self.spnMinX.value())
                interval.append(self.spnMaxX.value())

        if not self.chkAsPlot.isChecked():
            self.axes.hist(self.values, 18, interval, alpha=0.5, histtype="bar")
            #self.axes.plot(self.values, "ro-")
        else:
            n, bins, pathes = self.axes.hist(self.values, 18, interval, alpha=0.5, histtype="bar")
            self.axes.clear()
            c = []
            for i in range(len(bins) - 1):
                s = bins[i + 1] - bins[i]
                c.append(bins[i] + (s / 2))

            self.axes.plot(c, n, "ro-")

        self.axes.grid(self.chkShowGrid.isChecked())
        self.axes.set_ylabel(unicode(self.tr("Count")))
        self.axes.set_xlabel(unicode(self.tr("Class")))
        self.figure.autofmt_xdate()
        self.canvas.draw()

    def kmeansCluster(self, layer, distance, number):
        import scipy
        import scipy.cluster.hierarchy as sch
        from scipy.cluster.vq import vq,kmeans,whiten
        import numpy as np

        count = layer.featureCount()
        self.setProgressRange(count)
        points = []
        for f in layer.getFeatures():
            geom = f.geometry()
            x = geom.asPoint().x()
            y = geom.asPoint().y()
            point = []
            point.append(x)
            point.append(y)
            points.append(point)
            self.updateProgress()

        distances = {0:'euclidean', 1:'cityblock', 2:'hamming'}
        disMat = sch.distance.pdist(points, distances.get(distance))#'euclidean''cityblock''hamming''cosine' 
        Z=sch.linkage(disMat,method='average') 
        P=sch.dendrogram(Z)
        cluster= sch.fcluster(Z, t=1, criterion='inconsistent')
        data=whiten(points)
        centroid=kmeans(data, number)[0]
        label=vq(data, centroid)[0]
        return centroid, label

    def addClassField(self, vectorLayer):
        vectorLayerDataProvider = vectorLayer.dataProvider()
        outputFieldName = unicode(self.tr("class"))

        # Create field of not exist
        if vectorLayer.fieldNameIndex(outputFieldName) == -1:
            vectorLayerDataProvider.addAttributes([QgsField(outputFieldName, QVariant.Int)])

        vectorLayer.updateFields()
        vectorLayer.startEditing()
        attrIdx = vectorLayer.fieldNameIndex(outputFieldName)
        features = vectorLayer.getFeatures()

        idx = self.values.tolist()
        i = 0
        for feature in features:
            vectorLayer.changeAttributeValue(feature.id(), attrIdx, int(idx[i]))
            i += 1

        vectorLayer.updateFields()
        vectorLayer.commitChanges()
        self.symbolLayer(vectorLayer)

    def saveAsMap(self, layer):
        reg = QgsMapLayerRegistry.instance()
        i = QImage(QSize(800,800), QImage.Format_ARGB32_Premultiplied)
        c = QColor("white")
        i.fill(c.rgb())
        p = QPainter()
        p.begin(i)
        r = QgsMapRenderer()
        lyrs = reg.mapLayers().keys()
        r.setLayerSet(lyrs)
        rect = QgsRectangle(r.fullExtent())
        rect.scale(1.1)
        r.setExtent(rect)
        r.setOutputSize(i.size(), i.logicalDpiX())
        r.render(p)
        p.end()
        i.save(self.outPath,"jpg")

    # def saveAsMap(self, layer):
    #     i = QImage(QSize(800,800), QImage.Format_ARGB32_Premultiplied)
    #     c = QColor("white")
    #     i.fill(c.rgb())
    #     p = QPainter()
    #     p.begin(i)
    #     p.setRenderHint(QPainter.Antialiasing)
    #     r = QgsMapRenderer()
    #     lyrs = [layer.getLayerID()]
    #     r.setLayerSet(lyrs)
    #     rect = QgsRect(r.fullExtent())
    #     rect.scale(1.1)
    #     r.setExtent(rect)
    #     r.setOutputSize(i.size(), i.logicalDpiX())
    #     r.render(p)
    #     p.end()
    #     i.save(self.outPath,"jpg")

    def symbolLayer(self, layer):
        classField = (
            ("0",0,0,"red"),
            ("1",1,1,"orange"),
            ("2",2,2,"yellow"),
            ("3",3,3,"green"),
            ("4",4,4,"cyan"),
            ("5",5,5,"blue"),
            ("6",6,6,"purple"),
            ("7",7,7,"brown"),
            ("8",8,8,"grey"),
            ("9",9,9,"black"))
        ranges = []
        for label,lower,upper,color in classField:
            sym = QgsSymbolV2.defaultSymbol(layer.geometryType())
            sym.setColor(QColor(color))
            rng = QgsRendererRangeV2(lower, upper, sym, label)
            ranges.append(rng)

        field = "class"
        renderer = QgsGraduatedSymbolRendererV2(field, ranges)
        layer.setRendererV2(renderer)
        layer.triggerRepaint()
        self.saveAsMap(layer) 

