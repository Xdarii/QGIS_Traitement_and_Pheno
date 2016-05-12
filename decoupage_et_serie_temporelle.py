# -*- coding: utf-8 -*-
"""
Created on Thu Mar 24 10:41:03 2016

@author: U115-H016
"""

from osgeo import gdal, gdalnumeric, ogr, osr
import os, sys
import scipy as sp
from clip import *
from function_data_raster import*
from PIL import Image, ImageDraw
gdal.UseExceptions()



def decoupage_et_serie_temporelle(lienDonnee,lienZoneEtudes,lienSave,debutYear,nomDonnee,pluriAnnuelle=0):
    
    
    nL=388
    nC=349
    dt='int16'

    if not (os.path.exists(lienDonnee)) or not (os.path.exists(lienZoneEtudes)) :
        #teste si le lien fournit pour le NDVI et /ou du DOY existe
        print  "Verifier les liens des données et de la zone d'etudes"
    else:
        if not (os.path.exists(lienSave)): #Création du lien d'enregistrement si il n'existe pas
            os.makedirs(lienSave)
            print "création du lien d'enregistrement"
        
        
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
           
           nZ=23 # Nous avons 23 images par annee, donc 23 bandes
           serie=sp.empty((nL,nC,nZ),dtype=dt)
           for element in liste:
               if (k<22) : 
                   serie[:,:,k],minX,maxY=clipRaster(element,lienZoneEtudes)
                
                   k=k+1
               else : 
                    serie[:,:,k],minX,maxY=clipRaster(element,lienZoneEtudes)
                    
                    data = gdal.Open(liste[0],gdal.GA_ReadOnly) # pour recuperer les parametres des images entrées
                       
                    GeoTransform = data.GetGeoTransform()
                    GeoTransform=list(GeoTransform)
                    #on modifie Geotransform pour l'adapter à l'emprise de notre zone d'etudes
                    GeoTransform[0]=minX # 
                    GeoTransform[3]=maxY #
                    
                    Projection = data.GetProjection()
                    outputName=lienSave+'\\serie_tempo_'+nomDonnee+'_'+str(annee)+'.tif' #nom des images de sorties
                    #
                    annee=annee+1 
                    
                    write_data(outputName,serie,GeoTransform,Projection) # Enregistrement du NDVI
                    k=0 #on reinitialise k
                    serie=sp.empty((nL,nC,nZ),dtype=dt) #on crée une nouvelle serie
                    print(compt)
                    compt=compt+1 #pour verifier le nombre d'image considéré par année
        else:#création d'une image multi_bande et pluriannuelle
            nZ=len(liste)# le nombre de bandes correspond aux nombres d'images contenues liste                 
            serie=sp.empty((nL,nC,nZ),dtype=dt)            
            k=0
            
            for element in liste:
                print k
                serie[:,:,k],minX,maxY=clipRaster(element,lienZoneEtudes)
                k=k+1
                
                if( k>=len(liste)):
                    data = gdal.Open(liste[0],gdal.GA_ReadOnly) # pour recuperer les parametres des images entrées
                    GeoTransform = data.GetGeoTransform()
                    GeoTransform=list(GeoTransform)
                    #on modifie Geotransform pour l'adapter à l'emprise de notre zone d'etudes
                    GeoTransform[0]=minX # 
                    GeoTransform[3]=maxY #
                    
                    Projection = data.GetProjection()
                    outputName=lienSave+'\\serie_tempo_'+nomDonnee+'_'+str(debutYear)+'_sur_'+str(nYear)+'ans.tif' #nom des images de sorties
                                  
                    write_data(outputName,serie,GeoTransform,Projection) # Enregistrement du NDVI
                    print 'image enregistrée avec succès sous le nom : '+str(outputName)
