# -*- coding: utf-8 -*-
"""
/***************************************************************************
 metriquePhenologique
                                 A QGIS plugin
 calcul de metrique phenologique et pretraitement
                              -------------------
        begin                : 2016-04-29
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Dian
        email                : bah.mamadian@yahoo.fr
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication,Qt
from PyQt4.QtGui import QAction, QIcon,QWidget, QPushButton, QApplication, QFileDialog, QMessageBox
from qgis.core import QgsMessageLog
from PyQt4 import QtGui
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from metrique_phenologique_dialog import metriquePhenologiqueDialog
import os.path
import os
from interpo_lineaire_DOY16jours import interpo_lineaire_DOY16jours
from decoupage_et_serie_temporelle import decoupage_et_serie_temporelle
from function_data_raster import*
from metriquePheno import metrique_pheno_Tang,metrique_pheno_vito,metrique_pheno_greenbrown,metrique_pheno_param
from clip import *
from scipy.signal import savgol_filter
from scipy import interpolate
from whittaker import whittaker


class metriquePhenologique:
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
            'metriquePhenologique_{}.qm'.format(locale))
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = metriquePhenologiqueDialog()
        QApplication.restoreOverrideCursor()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&pretraitement et pheno')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'metriquePhenologique')
        self.toolbar.setObjectName(u'metriquePhenologique')
		
        self.dlg.pushButton_cheminNDVI.clicked.connect(self.accesRepertoireNdvi)
        self.dlg.pushButton_cheminDOY.clicked.connect(self.accesRepertoireDoy)
        self.dlg.pushButton_cheminOut.clicked.connect(self.accesCheminSave)
        self.dlg.pushButton_cheminNDVI_metrique.clicked.connect(self.accesRepertoireNdviMetrique)
        self.dlg.pushButton_cheminNDVI_metrique_fichier.clicked.connect(self.accesFichierNdviMetriqueMultiannuelle)
        self.dlg.pushButton_cheminOut_metrique.clicked.connect(self.accesCheminSaveMetrique)
        self.dlg.pushButton_cheminZoneEtudes.clicked.connect(self.accesZoneEtudes)
        
        self.dlg.pushButton_execution.clicked.connect(self.active_progressbar,1)
        self.dlg.pushButton_execution.clicked.connect(self.validation)
        
        self.dlg.pushButton_execution_metrique.clicked.connect(self.active_progressbar,1)
        self.dlg.pushButton_execution_metrique.clicked.connect(self.validationMetrique)
        
        self.dlg.radioButton_DOY.clicked.connect(self.selectionDOY)
        self.dlg.radioButton_NDVI.clicked.connect(self.selectionNDVI)
        self.dlg.radioButton_default.clicked.connect(self.selectionDefault)
        self.dlg.radioButton_seuil.clicked.connect(self.selectionSeuil)
        
        self.dlg.MOD13Q1.currentChanged[int].connect(self.choixTab)
        #permet de réaliser une tache en fonction de l'option de pretraitement choisie
        self.dlg.outilPretraitement.currentChanged[int].connect(self.choix)
        
        
    def choixTab(self,index):
        """
        Permet de gerer les differentes options déja choisies par l'utilisateur ou les paramètres par défaut
        """
        if self.dlg.radioButton_default.isChecked():
            self.dlg.frame_seuil.setEnabled(0)
        if self.dlg.radioButton_seuil.isChecked():
            self.dlg.frame_seuil.setEnabled(1)
            
    def choix(self,index):
        """
        permet de réaliser une tache en fonction de l'option de prétraitement choisie
        """
        if self.dlg.outilPretraitement.currentIndex()==1:            
            self.dlg.cheminDOY.setEnabled(1)
            self.dlg.cheminNDVI.setEnabled(1)
            self.dlg.pushButton_cheminDOY.setEnabled(1)
            self.dlg.pushButton_cheminNDVI.setEnabled(1)
        if self.dlg.outilPretraitement.currentIndex()==0:            
            if self.dlg.radioButton_DOY.isChecked():
                self.dlg.cheminNDVI.clear()
                self.dlg.cheminNDVI.setEnabled(0)
                self.dlg.pushButton_cheminNDVI.setEnabled(0)
                self.dlg.cheminDOY.setEnabled(1)
                
            if self.dlg.radioButton_NDVI.isChecked():
                self.dlg.cheminDOY.clear()
                self.dlg.cheminDOY.setEnabled(0)
                self.dlg.pushButton_cheminDOY.setEnabled(0)
                self.dlg.cheminNDVI.setEnabled(1)
                
        if self.dlg.outilPretraitement.currentIndex()==2:            
            self.dlg.cheminDOY.clear()
            self.dlg.cheminDOY.setEnabled(0)
            self.dlg.cheminNDVI.setEnabled(1)
            self.dlg.pushButton_cheminDOY.setEnabled(0)

    def accesRepertoireNdvi(self):

        """! \brief cette fonction permet de selectionner le lien du répertoire
        dans lequel se trouve le NDVI
        
        
        """
        ndviPath = QFileDialog.getExistingDirectory(self.dlg,u'Repertoire du NDVI','.')
          
        if ndviPath:
          
          self.dlg.cheminNDVI.setText(ndviPath)


    def accesRepertoireNdviMetrique(self):
        
        """
         cette fonction permet de selectionner le lien du répertoire
        dans lequel se trouve le NDVI
       
        
        """
        ndviPath = QFileDialog.getExistingDirectory(self.dlg,u'Répertoire du NDVI','.')
          
        if ndviPath:
          
          self.dlg.cheminNDVI_metrique.setText(ndviPath)

    def accesFichierNdviMetriqueMultiannuelle(self):
        
        """
        !\brief cette fonction permet de selectionner le lien du repertoire
        dans lequel se trouve le NDVI       
        
        """
        ndviPath = QFileDialog.getOpenFileName(self.dlg, 
                                            u"Ouvrir le fichier NDVI multiannuelle", 
                                            u"/home/puiseux/images", 
                                            u"Images (*.tif )")
          
        if ndviPath:
          
          self.dlg.cheminNDVI_metriqueFichier.setText(ndviPath)
              
              
    def accesRepertoireDoy(self):
        
        """
         cette fonction permet de selectionner le lien du repertoire
        dans lequel se trouve le DOY

        """
        
        
        doyPath = QFileDialog.getExistingDirectory(self.dlg,u'Repertoire du DOY','.')
          
        if doyPath:
          
          self.dlg.cheminDOY.setText(doyPath)

    def accesCheminSave(self,var):
        """
        cette fonction permet de selectionner le repertoire d'enregistrement des fichiers
        
        """
        savePath = QFileDialog.getExistingDirectory(self.dlg,u'Repertoire d''enregistrement','.')
              
        if savePath:
                      
                      self.dlg.cheminOut.setText(savePath)
                      
    def accesCheminSaveMetrique(self,var):
        """
        cette fonction permet de selectionner le repertoire d'enregistrement des fichiers
        
        """
        savePath = QFileDialog.getExistingDirectory(self.dlg,u'Repertoire d''enregistrement des parametres','.')
                  
        if savePath:
                      
                      self.dlg.cheminOut_metrique.setText(savePath)



    def accesZoneEtudes(self):
        """
        cette fonction permet de selectionner le lien du repertoire
        dans lequel se trouve le NDVI
        
        """
        
        
        zonePath = QFileDialog.getOpenFileName(self.dlg, u"Enregistrer", 
                                               u"/home/puiseux/", 
                                               u"Images (*.shp )")
          
        if zonePath:
          
          self.dlg.zoneEmprise.setText(zonePath)

    def selectionDefault(self):
        """
        Permet de verrouiller le changement de seuil et permettre l'utilisation des  valeurs de seuils par défaut 
        en fonction de la fonction choisie
        """
        self.dlg.frame_seuil.setEnabled(0)
        
    def selectionSeuil(self):
        """
        Permet de deverrouiller le changement de seuil et permettre à l'utilisateur de saisir ses propres seuils
        """
        self.dlg.frame_seuil.setEnabled(1)
        
    def selectionNDVI(self):
        """
        permet de charger le lien du repertoire du NDVI et verrouiller celui du DOY      
        """
        if self.dlg.outilPretraitement.currentIndex()==0:
            self.dlg.cheminDOY.setEnabled(0)
            self.dlg.cheminNDVI.setEnabled(1)

        
    def selectionDOY(self):
        """
        /** permet de charger le lien du repertoire du DOY et verrouiller celui du NDVI        */
        """
        if self.dlg.outilPretraitement.currentIndex()==0:
            self.dlg.cheminNDVI.setEnabled(0)
            self.dlg.cheminDOY.setEnabled(1)

    def active_progressbar(self,inY):
        """
        permet d'activer la barre de progression. Il desactive ensuite le bouton de validation
        afin d'eviter à l'utilisateur de lancer une validation pendant que le programme tourne.
        Elle permet aussi d'eviter de géler l'application.
        
        Entree:
        inY: un booléen qui permet de dire si on active ou on desactive la barre.
        
        """
        self.dlg.progressBar.setEnabled(inY)
        if inY==1:
            
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.dlg.pushButton_execution.setEnabled(0)
            QApplication.processEvents()
        if inY==0:
            QApplication.restoreOverrideCursor()
            self.dlg.pushButton_execution.setEnabled(1)
            QApplication.processEvents()
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
        return QCoreApplication.translate('metriquePhenologique', message)


    def validation(self):
        
        """
        cette fonction permet de determiner l'action à réaliser quand on clique sur 
        Valider
        
        """
        #________si le decoupage est selectionné______________
#==============================================================================
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        self.active_progressbar(1)
        if self.dlg.outilPretraitement.currentIndex()==0:
             
              zoneEtudes=self.dlg.zoneEmprise.text() #zone d'etude
            
              self.dlg.progressBar.setTextVisible(1)
              debutYear=int(self.dlg.spinBox_debut.value()) #annee de debut
              
              lienSave=self.dlg.cheminOut.text()     #lien d'enregistrement
              
              if self.dlg.radioButton_NDVI.isChecked():
                  nomDonnee='NDVI' # type de données
                  lienDonnee=self.dlg.cheminNDVI.text()  # repertoire des données
                  
              if self.dlg.radioButton_DOY.isChecked():
                  nomDonnee='DOY' # type de données
                  lienDonnee=self.dlg.cheminDOY.text()   # repertoire des données
              if self.dlg.radioButton_imageParAn.isChecked():
                  pluriAnnuelle=0
              
              if self.dlg.radioButton_pluriAnnuelle.isChecked():
                  pluriAnnuelle=1

              dt='int16'
              lienZoneEtudes= str(zoneEtudes)
              progress=0
              if not (os.path.exists(lienDonnee)) or not os.path.exists(lienZoneEtudes) or not (os.path.exists(lienSave)) :
                #teste si le lien fournit pour le NDVI et /ou du DOY existe
                  try:
                      if not os.path.exists(lienDonnee):
                          QMessageBox.warning(self.dlg, u'Problème de lien ', u"le lien du répertoire contenant les images à decouper est inexistant ")
                          QApplication.restoreOverrideCursor()
                          return
                          
                      if not os.path.exists(lienZoneEtudes):
                          QMessageBox.warning(self.dlg, u'Problème de lien ', u"le lien de la zone d'etudes est inexistant ")
                          QApplication.restoreOverrideCursor()
                          return
                          
                      if not os.path.exists(lienSave):
                          QMessageBox.warning(self.dlg, u'Problème de lien ', u"le lien du répertoire d'enregistrement est inexistant ")
                          QApplication.restoreOverrideCursor()
                          return
                          
                  except:
                      QMessageBox.warning(self.dlg, u'Problème de lien ', u"problème avec un ou plusieurs liens")
                      QApplication.restoreOverrideCursor()
                      return
              else:
                self.dlg.progressBar.setValue(0)
                verifie=0
                liste=[];
                os.chdir(lienDonnee)
                donnee= os.listdir(lienDonnee)
                annee=debutYear
                for element in donnee:
                    if element.endswith('.tif'):
                       
                        liste.append(element);
                if len(liste)>=23:
                    k=0
                    compt=0
                    nYear=len(liste)/23
                    
                       
                if (pluriAnnuelle==0): #création d'une image multibande par année
                    try:                

                       T,minX,maxY,nL,nC=clipRaster(liste[0],lienZoneEtudes)
                       T=[]
                       nZ=23 # Nous avons 23 images par annee, donc 23 bandes
                       serie=sp.empty((nL,nC,nZ),dtype=dt)
                       for element in liste:
                           QApplication.processEvents()
                           if (k<22) : 
                               serie[:,:,k],minX,maxY,nL,nC=clipRaster(element,lienZoneEtudes)
                               progress=progress+(1.0/len(liste)*95)
                               self.dlg.progressBar.setValue(progress)
                               k=k+1
                           else : 
                                serie[:,:,k],minX,maxY,nL,nC=clipRaster(element,lienZoneEtudes)
                                
                                data = gdal.Open(liste[0],gdal.GA_ReadOnly) # pour recuperer les parametres des images entrées
                                   
                                GeoTransform = data.GetGeoTransform()
                                GeoTransform=list(GeoTransform)
                                #on modifie Geotransform pour l'adapter à l'emprise de notre zone d'etudes
                                GeoTransform[0]=minX # 
                                GeoTransform[3]=maxY #
                                
                                Projection = data.GetProjection()
                                outputName=os.path.join(lienSave,'serie_tempo_'+nomDonnee+'_'+str(annee)+'.tif') #nom des images de sorties
                                annee=annee+1 
                                
                                write_data(outputName,serie,GeoTransform,Projection) # Enregistrement du NDVI
                                k=0 #on reinitialise k
                                serie=sp.empty((nL,nC,nZ),dtype=dt) #on crée une nouvelle serie
                                compt=compt+1 #pour verifier le nombre d'image considéré par année
                                verifie=1.
                    except:           
                       QApplication.restoreOverrideCursor()
                       QMessageBox.warning(self.dlg, u'Problème découpage', u"problème lors du découpage avec une sortie 1 image/an")
                       return
                else:#création d'une image multi_bande et pluriannuelle
                    
                    try:
                        nZ=len(liste)# le nombre de bandes correspond aux nombres d'images contenues liste                 
                        T,minX,maxY,nL,nC=clipRaster(liste[0],lienZoneEtudes)
                        T=[]
                        serie=sp.empty((nL,nC,nZ),dtype=dt)
                        k=0
                        progress=0
                        self.dlg.progressBar.setValue(0)
                        for element in liste:
                            QApplication.processEvents()
                            serie[:,:,k],minX,maxY,L,C=clipRaster(element,lienZoneEtudes)
                            k=k+1
                            progress=progress+(1.0/len(liste)*98)
                            self.dlg.progressBar.setValue(progress)
                          
                            if( k>=len(liste)):
                                data = gdal.Open(liste[0],gdal.GA_ReadOnly) # pour recuperer les parametres des images entrées
                                GeoTransform = data.GetGeoTransform()
                                GeoTransform=list(GeoTransform)
                                #on modifie Geotransform pour l'adapter à l'emprise de notre zone d'etudes
                                GeoTransform[0]=minX # 
                                GeoTransform[3]=maxY #
                                
                                Projection = data.GetProjection()
                                outputName=os.path(lienSave,'serie_tempo_'+nomDonnee+'_'+str(debutYear)+'_sur_'+str(nYear)+'ans.tif') #nom des images de sorties
                                              
                                write_data(outputName,serie,GeoTransform,Projection) # Enregistrement du NDVI
                                verifie=1
                    except:
                         QMessageBox.warning(self.dlg, u'Problème découpage', u"problème lors du découpage avec une sortie multi-annuelle")
                         QApplication.restoreOverrideCursor()
                         QApplication.processEvents()
                         return
              if verifie==1:
                  self.dlg.progressBar.setValue(100)
                  QApplication.restoreOverrideCursor()




        if self.dlg.outilPretraitement.currentIndex()==1:
            
            verifie=0
            lienNdvi=self.dlg.cheminNDVI.text()
            lienDoy=self.dlg.cheminDOY.text()
            lienSave=self.dlg.cheminOut.text() 
            debutYear=int(self.dlg.spinBox_debut.value())
            finYear=int(self.dlg.spinBox_fin.value())
            save=1
            
            lissage=self.dlg.filtreInterpol.currentIndex() #determine si l'image de sortie sera lissé ou pas et avec quelle filtre          
            if self.dlg.radioButton_imageParAn_interpol.isChecked():
                pluriAnnuelle=0
              
            if self.dlg.radioButton_pluriAnnuelle_interpol.isChecked():
                pluriAnnuelle=1

#==============================================================================
            nYear=finYear-debutYear #nombre d'années
            
            if (not (os.path.exists(lienNdvi)) or not os.path.exists(lienDoy) or not os.path.exists(lienSave)) or nYear<0:
                #teste si le lien fournit pour le NDVI et /ou du DOY existe
                  try:
                      if not os.path.exists(lienNdvi):
                          QMessageBox.warning(self.dlg, u'Problème de lien ', u"le lien du répertoire contenant les images du NDVI est inexistant ")
                          QApplication.restoreOverrideCursor()
                          return
                          
                      if not os.path.exists(lienDoy):
                          QMessageBox.warning(self.dlg, u'Problème de lien ', u"le lien du répertoire contenant les images du DOY est inexistant ")
                          QApplication.restoreOverrideCursor()
                          return
    
                      if not os.path.exists(lienSave):
                          QMessageBox.warning(self.dlg, u'Problème de lien ', u"le lien du répertoire d'enregistrement est inexistant ")
                          QApplication.restoreOverrideCursor()
                          return
    
                      if nYear<0:
                          message=u"l'année de debut "+str(debutYear)+u" doit être inferieure à l'année de fin "+str(finYear)
                          QMessageBox.warning(self.dlg, u'Problème de periode ', message)
                          QApplication.restoreOverrideCursor()
                          return
                  except:
                      QMessageBox.warning(self.dlg, u'Interpolation', "Problème au niveau des liens")
                      QApplication.restoreOverrideCursor()
                      return


            else:
                annee=debutYear;
                listeNdvi=[]; #Initialisation de la liste qui stock les NDVI
                listeDoy=[];  #Initialisation de la liste qui stock les DOY

                donneeNdvi= os.listdir(lienNdvi)
                if len(donneeNdvi)>0:
                    for element in donneeNdvi:
                        if element.endswith('.tif'):     # stocker dans la liste que des fichiers images  
                            
                            listeNdvi.append(element)
                else:
                     QMessageBox.warning(self.dlg, u'Répertoire vide ', u"le répertoire du NDVI est vide")
                     QApplication.restoreOverrideCursor()
                     return
                        
                        
                donneeDoy= os.listdir(lienDoy)
                if len(donneeNdvi)>0:
                    for element in donneeDoy:
                        if element.endswith('.tif'):     # stocker dans la liste que des fichiers images  
                            
                            listeDoy.append(element)
                else:
                     QMessageBox.warning(self.dlg, u'Répertoire vide ', u"le répertoire du DOY est vide")
                     QApplication.restoreOverrideCursor()                    
                     return
                            
                if len(listeDoy)==0:
                     QMessageBox.warning(self.dlg, u'Fichier .tif ', u"le répertoire du DOY ne contient pas de données .tif")
                     QApplication.restoreOverrideCursor()
                     return
                     
                if len(listeNdvi)==0:
                     QMessageBox.warning(self.dlg, u'Fichier .tif ', u"le répertoire du NDVI ne contient pas de données .tif")
                     QApplication.restoreOverrideCursor()
                     return



                
                #======================================================================
                #======================================================================
                imageNDVI=os.path.join(lienNdvi , listeNdvi[0]);#lien qui permet d'acceder à la k-ième image
                        
                [NDVI,GeoTransform,Projection]=open_data(imageNDVI) #stockage du NDVI dans un tableau
                        
                doyTheorique=sp.arange(25)*16+1    # Creation du DOY theorique
                    
                [nl,nc,z]=NDVI.shape
                self.dlg.progressBar.setValue(0)
                pas=(1./(nYear+1))*95/nl
                progress=0        
                if pluriAnnuelle==0: #une image par année
                    
                    try:
                        verifie=1
                        for k in range(nYear+1):
                            QApplication.processEvents()
                            QApplication.processEvents()
                            imageNDVI=os.path.join(lienNdvi ,listeNdvi[k]);#lien qui permet d'acceder à la k-ième image
                            
                            imageDOY= os.path.join(lienDoy , listeDoy[k]); #lien qui permet d'acceder au k-ième DOY
                            
                            
                            [NDVI,GeoTransform,Projection]=open_data(imageNDVI) #stockage du NDVI dans un tableau
                            [DOY,GeoTransform,Projection]=open_data(imageDOY)   #stockage du DOY dans un tableau
                            #newDoy=sp.empty(NDVI.shape,dtype='int16')
                            newNdvi=sp.empty(NDVI.shape,dtype='float16') #variable qui stocke le  NDVI après interpolation
                            
                            ndviXY=sp.empty((25),dtype='int16')  #recupère les 23 valeurs de la serie à la position (x,y)
                            doyXY=sp.empty((25),dtype='int16')  #recupère les 23 valeurs de la serie à la position (x,y)
                            
                            annee=annee+1
                            for l in range(nl) :
                                progress=progress+pas
                                self.dlg.progressBar.setValue(progress)
                                for c in range(nc):
                                    
                                
                                    doyXY[1:-1]=DOY[l,c,:]+16 
                                    ndviXY[1:-1]=NDVI[l,c,:]
                                    
                                    ndviXY[0]=NDVI[l,c,-1]
                                    ndviXY[-1]=NDVI[l,c,0]        
                                    doyXY[-1]= 385
                                    doyXY[0]=1
                            
                                    interpolation=interpolate.interp1d(doyXY,ndviXY)#création de la fonction d'interpolation
                                    newNDVIXY=interpolation(doyTheorique) #interpolation
                                    
                                    if (lissage==1):
                                         
                                        newNdvi[l,c,:]=savgol_filter(newNDVIXY[1:-1], 9, 6);
                                        prefixe='interpolation_SG_'
                                    if(lissage==2):
                                         
                                        newNdvi[l,c,:]=whittaker(newNDVIXY[1:-1]) #recuperation des valeurs utiles                            
                                        prefixe='interpolation_WS_'
                                    if(lissage==0):
                                        newNdvi[l,c,:]=newNDVIXY[1:-1] +0.0 #recuperation des valeurs utiles                            
                                        prefixe='interpolation_noFilter_'
                            if save==1: #enregistrement de la serie après interpolation
                                output_name=os.path.join(lienSave ,prefixe+str(annee)+'.tif') #lien d'enregistrement de la serie de l'année (année)
                                write_data(output_name,newNdvi,GeoTransform,Projection)
                    except:
                            QMessageBox.warning(self.dlg, u'Interpolation', u"problème lors de l'interpolation avec une sortie image par an")
                            QApplication.restoreOverrideCursor()
                            return


                     #======================================================================
                else: #une image dont nombre de bandes est égale à nombre d'année
                    imageNDVI=os.path.join(lienNdvi , listeNdvi[0])
                    [NDVI,GeoTransform,Projection]=open_data(imageNDVI)
                    [nL,nC,i]=NDVI.shape
                        
                    nZ=len(listeNdvi)*23 #23images par années * le nombre d'années
                     #newDoy=sp.empty(NDVI.shape,dtype='int16')
                    newNdvi=sp.empty((nL,nC,nZ),dtype='float16') #variable qui stocke le  NDVI après interpolation
                    ndviXY=sp.empty((25),dtype='int16')  #recupère les 23 valeurs de la serie à la position (x,y)
                    doyXY=sp.empty((25),dtype='int16')  #recupère les 23 valeurs de la serie à la position (x,y)

                    for k in range(nYear+1):
                         try:
                             QApplication.processEvents()
                             verifie=1

                             imageNDVI=os.path.join(lienNdvi , listeNdvi[k]);#lien qui permet d'acceder à la k-ième image
                             
                             imageDOY= os.path.join(lienDoy , listeDoy[k]); #lien qui permet d'acceder au k-ième DOY
                             
                             
                             [NDVI,GeoTransform,Projection]=open_data(imageNDVI) #stockage du NDVI dans un tableau
                             [DOY,GeoTransform,Projection]=open_data(imageDOY)   #stockage du DOY dans un tableau
                             
                             doyTheorique=sp.arange(25)*16+1    # Creation du DOY theorique     
                             
                              
                             for l in range(nL) :
                                 QApplication.processEvents()
                                 progress=progress+pas
                                 self.dlg.progressBar.setValue(progress)
                                 for c in range(nC):
                                     
                                    ## réalisation de l'interpolation cyclique
                                 
                                     doyXY[1:-1]=DOY[l,c,:]+16 
                                     ndviXY[1:-1]=NDVI[l,c,:]
                                     
                                     ndviXY[0]=NDVI[l,c,-1]
                                     ndviXY[-1]=NDVI[l,c,0]        
                                     doyXY[-1]= 385
                                     doyXY[0]=1
                                    
                             
                                     interpolation=interpolate.interp1d(doyXY,ndviXY)#création de la fonction d'interpolation
                                     newNDVIXY=interpolation(doyTheorique) #interpolation
                                     
                                     deb=k*23
                                     fin=(k+1)*23
                                     
                                     if (lissage==1):
                                         
                                        newNdvi[l,c,deb:fin]=savgol_filter(newNDVIXY[1:-1], 9, 6);
                                        prefixe='interpolation_SG_'
                                     if(lissage==2):
                                         
                                        newNdvi[l,c,deb:fin]=whittaker(newNDVIXY[1:-1]) #recuperation des valeurs utiles                            
                                        prefixe='interpolation_WS_'
                                     if(lissage==0):
                                        newNdvi[l,c,deb:fin]=newNDVIXY[1:-1] +0.0 #recuperation des valeurs utiles                            
                                        prefixe='interpolation_noFilter_'
                                         
                         except: 
                            QMessageBox.warning(self.dlg, u'Interpolation', u"problème lors de l'interpolation avec une sortie pluriannuelle")
                            QApplication.restoreOverrideCursor()

                            return
                       
                        
                    if save==1: #enregistrement de la serie après interpolation
                         output_name=os.path.join(lienSave,prefixe +str(debutYear)+'_a_'+str(finYear)+'ans.tif') #lien d'enregistrement de la serie de l'année (année)
                         write_data(output_name,newNdvi,GeoTransform,Projection) 
            if verifie==1:
                self.dlg.progressBar.setValue(100)
                self.active_progressbar(0)

#==============================================================================


#            interpo_lineaire_DOY16jours(lienNdvi,lienDoy,lienSave,debutYear,finYear,save,pluriAnnuelle,lissage)
            
    def validationMetrique(self):
        """
        cette fonction permet de determiner l'action à réaliser quand on clique sur 
        Valider
        
        """
        self.dlg.progressBar_metrique.setValue(0)
        chemin=str(self.dlg.cheminNDVI_metriqueFichier.text() )
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        
        if not os.path.exists(chemin) or not os.path.exists(self.dlg.cheminOut_metrique.text()):
            if not os.path.exists(chemin):
                QMessageBox.warning(self.dlg, u'Problème de lien ', u"le lien du fichier contenant les images du NDVI est inexistant ")
                QApplication.restoreOverrideCursor()
                return
            if not os.path.exists(self.dlg.cheminOut_metrique.text()):
                QMessageBox.warning(self.dlg, u'Problème de lien ', u"le lien d'enregistrement est inexistant ")
                QApplication.restoreOverrideCursor()

                return
        else:

#            try:

                [NDVI,GeoTransform,Projection]=open_data(chemin)
                [L,C,r]=NDVI.shape
                duree=int(self.dlg.spinBox_fin__metrique.value())-int(self.dlg.spinBox_debut__metrique.value())+1
                
                self.dlg.progressBar_metrique.setValue(1)
                
                pas=(1./duree)*88/L
                progress=1
                seuil1=self.dlg.seuilSOS.value()
                seuil2=self.dlg.seuilEOS.value()
                #variable qui stocke les 10 metriques pour chaque années 
                metrique=sp.empty((L,C,10),dtype='float16') 
                #tableaux dans les quelles les differentes metriques seront stockées séparemment
                sos=sp.empty((L,C,duree),dtype='float16')
                eos=sp.empty((L,C,duree),dtype='float16')
                los=sp.empty((L,C,duree),dtype='float16')
                
                area=sp.empty((L,C,duree),dtype='float16')
                areaBef=sp.empty((L,C,duree),dtype='float16')
                areaAft=sp.empty((L,C,duree),dtype='float16')
                self.dlg.progressBar_metrique.setValue(2)

                anomalieSos=sp.empty((L,C,duree),dtype='float16')
                anomalieEos=sp.empty((L,C,duree),dtype='float16')
                anomalieLos=sp.empty((L,C,duree),dtype='float16')
                
                anomalieArea=sp.empty((L,C,duree),dtype='float16')
                anomalieAreaBef=sp.empty((L,C,duree),dtype='float16')
                anomalieAreaAft=sp.empty((L,C,duree),dtype='float16')
#            except:
#               QMessageBox.warning(self.dlg, u'Déclaration ', u"Erreur lors de la déclaration des paramètres")
#                QApplication.restoreOverrideCursor()

#               return
#            try:
                for k in range (duree):

                     deb=k*23
                     fin=deb+23
                     annee=int(self.dlg.spinBox_debut__metrique.value())+k
                     
                     for x in range(L):
                         QApplication.processEvents()
                         progress=progress+pas
                         self.dlg.progressBar_metrique.setValue(progress)
                         for y in range(C):
                             
                             ndvi=NDVI[x,y,deb:fin]*0.0001
    
                             if self.dlg.methode.currentIndex()==0:
                                 
                                 out1= metrique_pheno_greenbrown(ndvi,"white",seuil1,seuil2)
                                 
                             if self.dlg.methode.currentIndex()==1:
                                 if self.dlg.radioButton_default.isChecked():
                                      out1= metrique_pheno_greenbrown(ndvi,"trs")
                                 else:
                                      out1= metrique_pheno_greenbrown(ndvi,"trs",seuil1,seuil2)
                             
                             if self.dlg.methode.currentIndex()==2:
                                 if self.dlg.radioButton_default.isChecked():
                                     out1= metrique_pheno_vito(ndvi)
                                 else:
                                     out1= metrique_pheno_vito(ndvi,seuil1,seuil2)
                                 
                             if self.dlg.methode.currentIndex()==3:     
                                 if self.dlg.radioButton_default.isChecked():
                                     out1=metrique_pheno_Tang(ndvi)
                                 else:
                                     out1=metrique_pheno_Tang(ndvi,seuil1,seuil2)
                                 
                             outListe=metrique_pheno_param(ndvi,out1[0],out1[1],out1[4])
                             parametre=out1[0:3]+outListe
                             progress=progress+0.00001
                             self.dlg.progressBar_metrique.setValue(progress)
                             metrique[x,y,:]=sp.array(parametre)
                     sos[:,:,k]=metrique[:,:,1]
                     eos[:,:,k]=metrique[:,:,2]
                     los[:,:,k]=metrique[:,:,3]
                     area[:,:,k]=metrique[:,:,4]
                     areaBef[:,:,k]=metrique[:,:,5]
                     areaAft[:,:,k]=metrique[:,:,6]
                     
                     if self.dlg.prefixe.text()=='':
                         prefixe="parametre"
                         self.dlg.prefixe.setText(prefixe)
                     else:
                         prefixe=self.dlg.prefixe.text()
                    
                     #Enregistrement des metriques année/année
                     output_name=os.path.join(self.dlg.cheminOut_metrique.text(),prefixe+str(annee)+'.tif')
                     write_data(output_name,metrique,GeoTransform,Projection)
                name=str(self.dlg.spinBox_debut__metrique.value())+'-'+str(self.dlg.spinBox_fin__metrique.value())+".tif"
                
    #=================moyenne et ecart type=============================================================
                moySos=sos.mean(2)
                moyEos=eos.mean(2)
                moyLos=los.mean(2)
                moyArea=area.mean(2)
                moyAreaBef=areaBef.mean(2)
                moyAreaAft=areaAft.mean(2)
                 
                stdSos=sos.std(2)
                stdEos=eos.std(2)
                stdLos=los.std(2)
                stdArea=area.std(2)
                stdAreaBef=areaBef.std(2)
                stdAreaAft=areaAft.std(2)
    #==============================================================================
                pas2=8/duree
                for k in range(duree):
                    QApplication.processEvents()

                    anomalieSos[:,:,k]=(sos[:,:,k]-moySos)/stdSos
                    anomalieEos[:,:,k]=(eos[:,:,k]-moyEos)/stdEos
                    anomalieLos[:,:,k]=(los[:,:,k]-moyLos)/stdLos
                    
                    anomalieArea[:,:,k]=(area[:,:,k]-moyArea)/stdArea
                    anomalieAreaBef[:,:,k]=(areaBef[:,:,k]-moyAreaBef)/stdAreaBef
                    anomalieAreaAft[:,:,k]=(areaAft[:,:,k]-moyAreaAft)/stdAreaAft
    
                    progress=progress+pas2
                    self.dlg.progressBar_metrique.setValue(progress)
    
                #enregistrement de sos
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"SOS_"+name),sos,GeoTransform,Projection)
                #enregistrement eos
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"EOS_"+name), eos,GeoTransform,Projection)
                #enregistrement los
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"LOS_"+name),los,GeoTransform,Projection)
                #enregistrement area
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"area_"+name),area,GeoTransform,Projection)
                #enregistrement areaAft
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"areaAfter_max_"+name),areaAft,GeoTransform,Projection)
                #enregistrement areaBef
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"areaBefore_max_"+name),areaBef,GeoTransform,Projection)
    
                #enregistrement de anomalie sos
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"anomalie_SOS_"+name),anomalieSos,GeoTransform,Projection)
                #enregistrement anomalie eos
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"anomalie_EOS_"+name), anomalieEos,GeoTransform,Projection)
                #enregistrement anomalielos
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"anomalie_LOS_"+name),anomalieLos,GeoTransform,Projection)
                #enregistrement anomalie area
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"anomalie_area_"+name),anomalieArea,GeoTransform,Projection)
                #enregistrement anomalie areaAft
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"anomalie_areaAfter_max_"+name),anomalieAreaBef,GeoTransform,Projection)
                #enregistrement anomalie AreaAFT
                write_data(os.path.join(self.dlg.cheminOut_metrique.text(),"anomalie_areaBefore_max_"+name),anomalieAreaAft,GeoTransform,Projection)
    
    
                self.dlg.progressBar_metrique.setValue(100)
#            except:
#               QMessageBox.warning(self.dlg, u'calcul de paramètre ', u"Erreur lors du calcul des parmaètres")
#                QApplication.restoreOverrideCursor()
                return

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

    def showDlg(self):
        self.dlg.show()

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/metriquePhenologique/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'pretraite et calcul pheno'),
            callback=self.showDlg,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&pretraitement et pheno'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


#==============================================================================
#     def run(self):
#         """Run method that performs all the real work"""
#         # show the dialog
#         self.dlg.show()
#         # Run the dialog event loop
#         result = self.dlg.exec_()
#         # See if OK was pressed
#         if result:
#             # Do something useful here - delete the line containing pass and
#             # substitute with your code.
#             pass
#==============================================================================
