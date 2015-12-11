# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MapsheetDownloadDialog
                                 A QGIS plugin
 Download CanVec, NTDB, DEM, Topo data for Canada
                             -------------------
        begin                : 2013-01-31
        copyright            : (C) 2013 by Casey Vandenberg / SJ Geophysics
        email                : casey.vandenberg@sjgeophysics.com
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
import os, zipfile, shutil, time
from urllib2 import urlopen

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from qgis.core import *
from qgis.gui import *

import nts

from ui_mapsheetdownload import Ui_MapsheetDownload
# create the dialog for zoom to point

FTPHOST = 'ftp2.cits.rncan.gc.ca'
THEME_DICT={'BS':'Buildings_Structures',
             'EN':'Energy',
             'FO':'Relief_Landforms',
             'HD':'Hydrography',
             'IC':'Industrial_Commercial',
             'LA':'Administrative_Limit',
             'LI':'MapSheet_Limit',
             'LX':'Places_of_Interest',
             'SS':'Water_Saturated_Soils',
             'TO':'Toponomy',
             'TR':'Transportation',
             'VE':'Vegetation',
            }  

class MapsheetException(Exception):
    pass

KEY_OUTDIR = '/CanVecDownloader/lastSaveFileDir'
KEY_LASTSHEET50 = '/CanVecDownloader/lastSheets50k'
KEY_LASTSHEET250 = '/CanVecDownloader/lastSheets250k'

class MapsheetDownloadDialog(QDialog, Ui_MapsheetDownload):
    def __init__(self, qgisinterface):
        QDialog.__init__(self)
        self.setupUi(self)
        self.iface = qgisinterface
        
        self.connect(self.browserButton, SIGNAL("clicked()"), self.setOutputDirectory)
        self.connect(self.fromExtent50k, SIGNAL("clicked()"), self.autoFillMapsheetsBox50k)
        self.connect(self.fromExtent250k, SIGNAL("clicked()"), self.autoFillMapsheetsBox250k)
        
        #set output dir text from saved value
        settings = QSettings()
        self.outputDir.setText(settings.value(KEY_OUTDIR))
        self.input50k.setText(settings.value(KEY_LASTSHEET50))
        self.input250k.setText(settings.value(KEY_LASTSHEET250))
        
    def setOutputDirectory(self):
        """Open a browser dialog and set the output path"""
        settings = QSettings()
        lastOutDir = settings.value(KEY_OUTDIR)

        outputDir = unicode(QFileDialog.getExistingDirectory(self, self.tr('Specify output directory'), lastOutDir))
        if outputDir:
            settings.setValue(KEY_OUTDIR, outputDir)
        else:
            return
        self.outputDir.setText(outputDir)
        #TODO save output directory to prefs

    def accept(self):
        self.status.clear()
        input50k = str(self.input50k.text())
        input250k = str(self.input250k.text())
        outputDir = str(self.outputDir.text())
        
        #TODO do downloading
        self.download("product", "sheets", outputDir)
        
        #add layers to map
        if self.addMapLayers.isChecked():
            pass
    
    def autoFillMapsheetsBox50k(self):
        extent = self.iface.mapCanvas().extent()
        sheetslist = getMapsheetIdsFromExtent(nts.SCALE_50K, extent)
        self.input50k.setText(", ".join(sheetslist))
        
    def autoFillMapsheetsBox250k(self):
        extent = self.iface.mapCanvas().extent()
        sheetslist = getMapsheetIdsFromExtent(nts.SCALE_250K, extent)
        self.input250k.setText(", ".join(sheetslist))        

    def download(self, product, sheets, outputDir):
        #dummy download to test download thread
        url = "http://ftp2.cits.rncan.gc.ca/pub/canvec/50k_shp/021/h/canvec_021h01_shp.zip"
        dlthread = DownloaderThread(self, url, outputDir, key="021h01")
        dlthread.setOnProgress(self.onDownloadProgress)
        dlthread.setOnFinished(self.onDownlonadFinish)
        dlthread.setOnError(self.onDownloadError)
        dlthread.start()
    
    def onDownloadError(self, key, errorString):
        self.status.insertPlainText("error (" + key + ")! " + str(errorString))
    
    def onDownlonadFinish(self, key):
        self.status.insertPlainText("done! " + key)
    
    def onDownloadProgress(self, key, current, total):
        self.progressBar.setMaximum(total)
        self.progressBar.setValue(current)
    
    def extract(self, product, sheets):
        pass

    def addToLayers(self,DestinationDirectory,NTS_50k_Sheets,NTS_250k_Sheets,downloadFlags):
        pass


class DownloaderThread(QThread):
    
    def __init__(self, parent, url, outdir, key=None):
        QThread.__init__(self, parent)
        self.keyobj = key
        self.url = url
        self.outdir = outdir
        self.cancel = False
    
    def setOnFinished(self, slot):
        if self.keyobj is None:
            self.connect(self, SIGNAL("finished()"), slot)
        else:
            self.connect(self, SIGNAL("finished()"), lambda: slot(self.keyobj))
    
    def setOnError(self, slot):
        if self.keyobj is None:
            self.connect(self, SIGNAL("error(QString)"), slot)
        else:
            self.connect(self, SIGNAL("error(QString)"), lambda string: slot(self.keyobj, string))
    
    def setOnProgress(self, slot):
        if self.keyobj is None:
            self.connect(self, SIGNAL("progress(int, int)"), slot)
        else:
            self.connect(self, SIGNAL("progress(int, int)"), lambda current, total: slot(self.keyobj, current, total))
    
    def run(self):
        try:
            filename = os.path.join(self.outdir, self.url.split("/")[-1])
            fo = open(filename, "wb")
            urlhandle = urlopen(self.url)
            totalsize = int(urlhandle.info()["Content-Length"])
            actualsize = 0
            blocksize = 64*1024
            
            while not self.cancel:
                block = urlhandle.read(blocksize)
                actualsize += len(block)
                self.emit(SIGNAL("progress(int, int)"), actualsize, totalsize)
                if len(block) == 0:
                    break
                fo.write(block)
            
            fo.close()
            
        except Exception as e:
            self.emit(SIGNAL("error(QString)"), str(e))
        finally:
            fo.close()
        

def createThemeLists(NTS_50k_Sheet,DestinationDirectory):
    """
    Iterates over all .shp in the NTS_50k_Sheet download directory and
    creates a set of themes that are present which belong to the theme dictionary

    The theme dictionary includes:
    _______________________________
    BS - Buildings and Structures
    EN - Energy
    FO - Relief and Landforms
    HD - Hydrography
    IC - Industrial and Commercial
    LA - Adminstrative Limit
    LI - Map Coverage Limit
    LX - Places of Interest
    SS - Water Saturated Soils
    TO - Toponomy
    TR - Transportation
    VE - Vegetation

    The themes can later be organized by feature type if desired (not yet implemented)
    Feature Types:
    0 - Point
    1 - Line
    2 - Area
    _______________________________

    Themes are defined here: ftp://ftp2.cits.rncan.gc.ca/pub/canvec/doc/CanVec_feature_catalogue_en.pdf
    """
    lowerCase50kMapSheet = str.lower(NTS_50k_Sheet)
    d = os.path.join(DestinationDirectory,'CanVecData',NTS_50k_Sheet)
    shpList = getShpList(d)[0]
    shpHeadList = getShpList(d)[1]
    themes = set()
    for shpFile in shpHeadList:
        Theme = shpFile.split('_')[3]
        if Theme not in THEME_DICT:
            print '\nVector layer:',shpFile,'does not belong to a theme\n'
        else:
            themes.add(Theme)
    return themes

def createThemeLists250k(NTS_250k_Sheet,DestinationDirectory):
    """
    Iterates over all .shp in the NTS_50k_Sheet download directory and
    creates a set of themes that are present which belong to the theme dictionary

    The theme dictionary includes:
    _______________________________
    BS - Buildings and Structures
    EN - Energy
    FO - Relief and Landforms
    HD - Hydrography
    IC - Industrial and Commercial
    LA - Adminstrative Limit
    LI - Map Coverage Limit
    LX - Places of Interest
    SS - Water Saturated Soils
    TO - Toponomy
    TR - Transportation
    VE - Vegetation

    The themes can later be organized by feature type if desired (not yet implemented)
    Feature Types:
    0 - Point
    1 - Line
    2 - Area
    _______________________________

    Themes are defined here: ftp://ftp2.cits.rncan.gc.ca/pub/canvec/doc/CanVec_feature_catalogue_en.pdf
    """
    lowerCase250kMapSheet = str.lower(NTS_250k_Sheet)
    d = os.path.join(DestinationDirectory,'CanVec+',NTS_250k_Sheet)
    shpList = getShpList(d)[0]
    shpHeadList = getShpList(d)[1]
    themes = set()
    for shpFile in shpHeadList:
        Theme = shpFile.split('_')[0].upper()
        if Theme not in THEME_DICT:
            print '\nVector layer:',shpFile,'does not belong to a theme\n'
        else:
            themes.add(Theme)
    return themes
    
def organizeByTheme(NTS_50k_Sheet,DestinationDirectory):
    """
    For each theme present that exists in the theme dictionary, a sub-directory
    representing that themes value will be created if it does not already exist.
    Each file that is part of that theme is then moved into the appropriate sub-directory
    
    Currently this function is done automatically. A flag to organize by theme may be created in the future.
    """
    themes = createThemeLists(NTS_50k_Sheet,DestinationDirectory)
    downloadDir=str(os.path.join(DestinationDirectory,'CanVecData',NTS_50k_Sheet))
    for Theme in themes:
        d=os.path.join(DestinationDirectory,'CanVecData',NTS_50k_Sheet,THEME_DICT[Theme])
        if not os.path.exists(d):
            os.makedirs(d)        
    for fileName in os.listdir(downloadDir):
        fileHead = os.path.splitext(fileName)[0]
        if fileName.endswith('.html') or fileName.endswith('.xml') or fileName.find('.')<0:
            continue
        try:
            Theme = fileHead.split('_')[3]
            if Theme not in THEME_DICT:
                continue
            dst=(os.path.join(downloadDir,THEME_DICT[Theme],fileName))
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.move(os.path.join(downloadDir,fileName),dst)
        except KeyError, IndexError:
            print "Exception", dst,fileHead,Theme

def organizeByTheme250k(NTS_250k_Sheet,DestinationDirectory):
    """
    For each theme present that exists in the theme dictionary, a sub-directory
    representing that themes value will be created if it does not already exist.
    Each file that is part of that theme is then moved into the appropriate sub-directory
    
    Currently this function is done automatically. A flag to organize by theme may be created in the future.
    """
    themes = createThemeLists250k(NTS_250k_Sheet,DestinationDirectory)
    downloadDir=str(os.path.join(DestinationDirectory,'CanVec+',NTS_250k_Sheet))
    for Theme in themes:
        d=os.path.join(DestinationDirectory,'CanVec+',NTS_250k_Sheet,THEME_DICT[Theme])
        if not os.path.exists(d):
            os.makedirs(d)        
    for fileName in os.listdir(downloadDir):
        fileHead = os.path.splitext(fileName)[0]
        if fileName.endswith('.html') or fileName.endswith('.xml') or fileName.find('.')<0:
            continue
        try:
            Theme = fileHead.split('_')[0].upper()
            if Theme not in THEME_DICT:
                continue
            dst=(os.path.join(downloadDir,THEME_DICT[Theme],fileName))
            if os.path.exists(dst):
                os.unlink(dst)
            shutil.move(os.path.join(downloadDir,fileName),dst)
        except KeyError, IndexError:
            print "Exception", dst,fileHead,Theme
            
def addShapesToCanvas(shapeFilePath):
    layerName = os.path.basename(shapeFilePath)
    root, ext = os.path.splitext(layerName)
    if ext == '.shp':
        layerName = root
        vlayer_new = QgsVectorLayer(shapeFilePath, layerName, "ogr")
        try:
            QgsMapLayerRegistry.instance().addMapLayer(vlayer_new)
        except AttributeError:
            QgsMapLayerRegistry.instance().addMapLayers([vlayer_new])
    return True

def addDEMToCanvas(DEMFilePath):
    layerName = os.path.basename(DEMFilePath)
    root, ext = os.path.splitext(layerName)
    if ext == '.dem':
        layerName = root
        rlayer_new = QgsRasterLayer(DEMFilePath, layerName)
        try:
            QgsMapLayerRegistry.instance().addMapLayer(rlayer_new)
        except AttributeError:
            QgsMapLayerRegistry.instance().addMapLayers([rlayer_new])
    return True

def addTopoToCanvas(TopoFilePath):
    layerName = os.path.basename(TopoFilePath)
    root, ext = os.path.splitext(layerName)
    if ext == '.tif':
        layerName = root
        rlayer_new = QgsRasterLayer(TopoFilePath, layerName)
        try:
            QgsMapLayerRegistry.instance().addMapLayer(rlayer_new)
        except AttributeError:
            QgsMapLayerRegistry.instance().addMapLayers([rlayer_new])
    return True
       
def isvalid50k(string):
    inputValue = False
    if len(string)>0:
        inputValue = True
    returnValue = True
    if len(string)!=6:
        returnValue = False
    if returnValue and not string[0:3].isdigit():
        returnValue = False    
    if returnValue and not string[3:4].isalpha():        
        returnValue = False        
    if returnValue and not string[4:6].isdigit():
        returnValue = False
    return returnValue,inputValue
    
def isvalid250k(string):
    inputValue = False
    if len(string)>0:
        inputValue = True
    returnValue = True
    if len(string)!=4:
        returnValue = False
    if returnValue and not string[0:3].isdigit():
        returnValue = False    
    if returnValue and not string[3:4].isalpha():        
        returnValue = False        
    return returnValue,inputValue
    

def parse50kSheets(NTS_50k_Sheet):
        """
        Parses the NTS 50k mapsheet name, returns map series, map area, and map sheet

        Example: 092h12
        
        Series: 092
        Area:   h
        Sheet:  12
        """
        series50k = NTS_50k_Sheet[0:3]
        mapArea50k = NTS_50k_Sheet[3:4]
        sheet50k = NTS_50k_Sheet[4:6]
        
        return series50k,mapArea50k,sheet50k

def parse250kSheets(NTS_250k_Sheet):
        """
        Parses the NTS 250k mapsheet name, returns map series and map area

        Example: 092h12
        
        Series: 092
        Area:   h
        """
        series250k = NTS_250k_Sheet[0:3]
        mapArea250k = NTS_250k_Sheet[3:4]
        return series250k,mapArea250k
        
def getShpList(Dir):
    """
    Returns a list of shapefiles in the cwd
    """
    shpHeadList = []    
    shpList = []
    for fileName in os.listdir(Dir):
        fileHead = os.path.splitext(fileName)[0]
        fileTail = os.path.splitext(fileName)[1]
        if fileName.endswith('.shp'):
            shpHeadList.append(str(fileHead))
            shpList.append(str(fileName))
    return shpList,shpHeadList

def getMapsheetIdsFromExtent(scale, extent):
    '''Uses the nts module to get a list of nts ids based on the current extent.'''
    bounds = (extent.xMinimum(), extent.xMaximum(),
              extent.yMinimum(), extent.yMaximum())
    return ["".join(nts.ntsId(scale, tile)) for tile in nts.tilesBy(scale, bounds)]
    
