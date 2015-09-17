# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BelgianAddressGeolocation
                                 A QGIS plugin
 Geolocate by official addresses
                              -------------------
        begin                : 2015-09-16
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Peter Nuyts / Gitos
        email                : peter@gitos.be
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from BAG_dialog import BelgianAddressGeolocationDialog
import os.path
from datetime import time,datetime
import json
import urllib2
import urllib
import sys
from qgis.gui import QgsVertexMarker

class BelgianAddressGeolocation:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'BelgianAddressGeolocation_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = BelgianAddressGeolocationDialog()

        # Declare instance attributes
        self.completer = QCompleter()
        self.completerFlanders = QCompleter()
        self.model = QStringListModel()
        self.now = datetime.now()
        self.markers =[]
        self.getaddresses ="http://service.gis.irisnet.be/urbis/Rest/Localize/getaddresses?"
        self.suggestion ="http://loc.geopunt.be/geolocation/Suggestion?"
        self.location ="http://loc.geopunt.be/geolocation/Location?"
        self.actions = []
        self.menu = self.tr(u'&BAG')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'BelgianAddressGeolocation')
        self.toolbar.setObjectName(u'BelgianAddressGeolocation')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('BelgianAddressGeolocation', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/BelgianAddressGeolocation/icon.png'
        #self.add_action(
        #    icon_path,
        #    text=self.tr(u'Find Address'),
        #    callback=self.run,
        #    parent=self.iface.mainWindow())
        self.action = QAction(
            QIcon(icon_path),
            u"CRABB Find Address", self.iface.mainWindow())
                # connect the action to the run method
        # self.action.triggered.connect(self.run)
        QObject.connect(self.action, SIGNAL("triggered()"), self.run)
        QObject.connect(self.dlg.pushButton, SIGNAL("clicked()"), self.clearMarkers)
        QObject.connect(self.dlg.lineEdit, SIGNAL("textEdited(QString)"), self.changedData)
        QObject.connect(self.dlg.lineEditFlanders, SIGNAL("textEdited(QString)"), self.changedDataFlanders)
        QObject.connect(self.completer, SIGNAL("activated(QString)"), self.showPointOnCanvas)
        QObject.connect(self.completerFlanders, SIGNAL("activated(QString)"), self.showFlandersPointOnCanvas)
        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&CRABB FindAddress", self.action)

        #added code
        self.dlg.lineEdit.setCompleter(self.completer)
        self.dlg.lineEditFlanders.setCompleter(self.completerFlanders)
        self.completer.setModel(self.model)
        self.completer.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completer.popup().setStyleSheet("background-color: yellow")
        self.completerFlanders.setModel(self.model)
        self.completerFlanders.setCompletionMode(QCompleter.UnfilteredPopupCompletion)
        self.completerFlanders.popup().setStyleSheet("background-color: yellow")


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&BAG'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def showPointOnCanvas(self):

        try:

            self.__setMapSrs()

            inputtext = self.dlg.lineEdit.text().encode('utf8').strip()
            
            params = urllib.urlencode({ "address" : inputtext,"language" : "en","_dc" : "1386166569969" })

            result2 = urllib2.urlopen(self.getaddresses + params).read()

            doc = json.loads(result2)

            if len(doc) >0 and  len(doc["result"]) > 0 :

                
                x = doc["result"][0]["point"]['x']
                y = doc["result"][0]["point"]['y']

                canv = self.iface.mapCanvas()

                canv.clear()

                marker = QgsVertexMarker(canv)
            
                marker.setPenWidth(3)
                marker.setIconType(QgsVertexMarker.ICON_CROSS) # or, ICON_X ICON_BOX
                point = QgsPoint(x,y)
         
                marker.setCenter(point)
                self.markers.append(marker)

                scale = 100

                # Create a rectangle to cover the new extent
                rect = QgsRectangle(doc["result"][0]["extent"]['xmin'],doc["result"][0]["extent"]['ymin'],doc["result"][0]["extent"]['xmax'],doc["result"][0]["extent"]['ymax'])
                # Set the extent to our new rectangle
                canv.setExtent(rect)

                canv.refresh()

                # QMessageBox.information( self.iface.mainWindow(),"Info", "x, y = %s" %str(x) + ", " + str(y) )

                # keeps the window alive

                self.run()
            
            else:


                QMessageBox.information( self.iface.mainWindow(),"Info", "Geen locatie gevonden voor: %s" % inputtext )

        except:

            QMessageBox.warning( self.iface.mainWindow(),"Warning", "error: %s" % sys.exc_info()[0] )




    def millis(self,time1,time2):
        dt = time2 - time1
        ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
        return ms

    def changedData(self):

        try:
            
            if self.millis(self.now,datetime.now()) > 500:
            
                textboxtext =  self.dlg.lineEdit.text().encode('utf8').strip()
                if textboxtext:
                    params = urllib.urlencode({ "address" :textboxtext,"_dc":"1386168044443","language":"en" })
            
                    result2 = urllib2.urlopen(self.getaddresses + params).read()
                    list =[]
                    doc = json.loads(result2)
                
                    #resylt = {"result":[{"language":"en","address":{"street":{"name":"Rue Sombre","postCode":"1200","municipality":"Woluwe-Saint-Lambert","id":"4549"},"number":""},"score":21,"point":{"x":154441.834808387,"y":169982.660384498},"extent":{"xmin":154414,"ymin":169869,"xmax":154455,"ymax":170104}},{"language":"en","address":{"street":{"name":"Rue Sombre","postCode":"1150","municipality":"Woluwe-Saint-Pierre","id":"4550"},"number":""},"score":21,"point":{"x":154410.342604642,"y":169865.168898663},"extent":{"xmin":154372,"ymin":169768,"xmax":154443,"ymax":169960}}],"error":false,"status":"success"});
                    if len(doc) > 0:

                            test = doc["result"]
                            for item in test:
                                list.append(item["address"]["street"]["name"] + " " + item["address"]["number"]  + " " + item["address"]["street"]["postCode"] + " " + item["address"]["street"]["municipality"])
                        
                            self.model.setStringList(list)

                    self.now =datetime.now()

                result = 0

        except:

            QMessageBox.warning( self.iface.mainWindow(),"Warning", "error: %s" % sys.exc_info()[0] )


     
                # keeps the window alive
            
        pass

    def changedDataFlanders(self):

        try:
            
            if self.millis(self.now,datetime.now()) > 500:
            
                textboxtext =  self.dlg.lineEditFlanders.text().encode('utf8').strip()
                if textboxtext:
                    params = urllib.urlencode({ "q" :textboxtext })
            
                    result2 = urllib2.urlopen(self.suggestion + params).read()
                    list =[]
                    doc = json.loads(result2)
                
                    #resylt = {"SuggestionResult":["Louis Andriesstraat, Kortenberg","Louis Artanweg, Knokke-Heist","Louis Blériotlaan, Gent","Louis Buelenslaan, Tervuren","Louis Callebautstraat, Aalst"]}
                    if len(doc) > 0:

                            test = doc["SuggestionResult"]
                            for item in test:
                                list.append(item)
                        
                            self.model.setStringList(list)

                    self.now =datetime.now()

                result = 0

        except:

            QMessageBox.warning( self.iface.mainWindow(),"Warning", "error: %s" % sys.exc_info()[0] )


     
                # keeps the window alive
            
        pass

    def showFlandersPointOnCanvas(self):

        try:

            self.__setMapSrs()

            inputtext = self.dlg.lineEditFlanders.text().encode('utf8').strip()
            
            params = urllib.urlencode({ "q" : inputtext })

            result2 = urllib2.urlopen(self.location + params).read()

            doc = json.loads(result2)

            if len(doc) >0 and  len(doc["LocationResult"]) > 0 :

                
                x = doc["LocationResult"][0]["Location"]['X_Lambert72']
                y = doc["LocationResult"][0]["Location"]['Y_Lambert72']

                canv = self.iface.mapCanvas()

                canv.clear()

                marker = QgsVertexMarker(canv)
            
                marker.setPenWidth(3)
                marker.setIconType(QgsVertexMarker.ICON_CROSS) # or, ICON_X ICON_BOX
                point = QgsPoint(x,y)
         
                marker.setCenter(point)
                self.markers.append(marker)

                scale = 100

                # Create a rectangle to cover the new extent
                rect = QgsRectangle(doc["LocationResult"][0]["BoundingBox"]["LowerLeft"]['X_Lambert72'],doc["LocationResult"][0]["BoundingBox"]["LowerLeft"]['Y_Lambert72'],doc["LocationResult"][0]["BoundingBox"]["UpperRight"]['X_Lambert72'],doc["LocationResult"][0]["BoundingBox"]["UpperRight"]['Y_Lambert72'])
                # Set the extent to our new rectangle
                canv.setExtent(rect)

                canv.refresh()

                # QMessageBox.information( self.iface.mainWindow(),"Info", "x, y = %s" %str(x) + ", " + str(y) )

                # keeps the window alive

                self.run()
            
            else:


                QMessageBox.information( self.iface.mainWindow(),"Info", "Geen locatie gevonden voor: %s" % inputtext )

        except:

            QMessageBox.warning( self.iface.mainWindow(),"Warning", "error: %s" % sys.exc_info()[0] )

    def __setMapSrs(self):

        mapCanvas =self.iface.mapCanvas()

            # On the fly
        mapCanvas.mapRenderer().setProjectionsEnabled(True) 
 

        my_crs = QgsCoordinateReferenceSystem(31370, QgsCoordinateReferenceSystem.EpsgCrsId)
        
        mapCanvas.mapRenderer().setDestinationCrs(my_crs)
    
        mapCanvas.freeze(False)
        mapCanvas.setMapUnits(0)
        mapCanvas.refresh()

    def clearMarkers(self):
        try:

            mapCanvas =self.iface.mapCanvas()
            for m in self.markers:
                mapCanvas.scene().removeItem(m)
            mapCanvas.refresh()
        except:

            QMessageBox.warning( self.iface.mainWindow(),"Warning", "error: %s" % sys.exc_info()[0] )
