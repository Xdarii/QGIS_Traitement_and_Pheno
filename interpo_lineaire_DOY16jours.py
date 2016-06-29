# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 11:21:13 2016

@author: U115-H016
"""


import scipy as sp
from scipy.signal import savgol_filter
from scipy import interpolate
import matplotlib.pyplot as plt
import os
from function_data_raster import*
from clip import *



def interpo_lineaire_DOY16jours(lienNdvi,lienDoy,lienSave,debutYear,finYear,save,pluriannuelle,sg=0,prefixe='serie_temporelle_interpol_2708'):
    
    
    """
    Cette fonction permet d'interpoler les images de NDVI afin de les ramener à 16 jours.
    Elle permet d'avoir des images de NDVI prises tous les 16 jours en utilisant le vrai DOY et un autre DOY 
    appelé DOY  théorique (1, 17, 33, ..).
    
    
    lienNdvi: lien complet des series temporelles du NDVI
    lienDoy:  lien complet des series temporelles du DOY
    lienSave: lien complet qui pointe vers le repertoire d'enregistrement des images en sortie
    debutYear: date de debut 
    finYear: date de fin (superieur à debutYear)
    save: 1 pour enregistrer et 0 sinon
    sg=filtre SG (1 pour le filtrage et 0 sinon)
    
    """

    #======================================================================
    #======================================================================
    nYear=finYear-debutYear; #nombre d'années
             
    
    if nYear<=0 : #teste si la date de de fin est supérieur  à la date de debut
        print "l'année de debut "+str(debutYear)+" doit être inferieure à l'année de fin "+str(finYear)
    elif not (os.path.exists(lienNdvi)) or not (os.path.exists(lienDoy)) :
        #teste si le lien fournit pour le NDVI et /ou du DOY existe
        print  "Verifier les liens du DOY et/ou du NDVI"
    else:
        try:        
            annee=debutYear;
            listeNdvi=[]; #Initialisation de la liste qui stock les NDVI
            listeDoy=[];  #Initialisation de la liste qui stock les DOY
          
            
            if not (os.path.exists(lienSave)): #Création du lien d'enregistrement si il n'existe pas
                os.makedirs(lienSave)
                
            donneeNdvi= os.listdir(lienNdvi)
            
            for element in donneeNdvi:
                if element.endswith('.tif'):     # stocker dans la liste que des fichiers images  
                    
                    listeNdvi.append(element);
                    
                    
            donneeDoy= os.listdir(lienDoy)
            for element in donneeDoy:
                if element.endswith('.tif'):     # stocker dans la liste que des fichiers images      
                    
                    listeDoy.append(element);
                    
        except:
            
            print "problème lors de la récuperation des données"
                
        #======================================================================
        #======================================================================
        if pluriannuelle==0: #une image par année
            
            print "création d'une image par année"
            for k in range(nYear+1):
                
                imageNDVI=lienNdvi +'\\'+ listeNdvi[k];#lien qui permet d'acceder à la k-ième image
                
                imageDOY= lienDoy +'\\'+ listeDoy[k]; #lien qui permet d'acceder au k-ième DOY
                
                output_name=lienSave +'\\'+prefixe+str(annee)+'.tif' #lien d'enregistrement de la serie de l'année (année)
                
                [NDVI,GeoTransform,Projection]=open_data(imageNDVI) #stockage du NDVI dans un tableau
                [DOY,GeoTransform,Projection]=open_data(imageDOY)   #stockage du DOY dans un tableau
                
                doyTheorique=sp.arange(25)*16+1    # Creation du DOY theorique
                
                
                [nl,nc,z]=NDVI.shape
                
                #newDoy=sp.empty(NDVI.shape,dtype='int16')
                newNdvi=sp.empty(NDVI.shape,dtype='float16') #variable qui stocke le  NDVI après interpolation
                
                ndviXY=sp.empty((25),dtype='int16')  #recupère les 23 valeurs de la serie à la position (x,y)
                doyXY=sp.empty((25),dtype='int16')  #recupère les 23 valeurs de la serie à la position (x,y)
                
                #print nl,nc,z
                annee=annee+1
                for l in range(nl) :
                    for c in range(nc):
                        
                       ## réalisation de l'interpolation cyclique
                    
                        doyXY[1:-1]=DOY[l,c,:]+16 
                        ndviXY[1:-1]=NDVI[l,c,:]
                        
                        ndviXY[0]=NDVI[l,c,-1]
                        ndviXY[-1]=NDVI[l,c,0]        
                        doyXY[-1]= 385
                        doyXY[0]=1
                       
                
                        interpolation=interpolate.interp1d(doyXY,ndviXY)#création de la fonction d'interpolation
                        newNDVIXY=interpolation(doyTheorique) #interpolation
                        if sg==1 :
                            newNdvi[l,c,:]=savgol_filter(newNDVIXY[1:-1], 9, 6);
                            
                        else:
                            newNdvi[l,c,:]=newNDVIXY[1:-1] +0.0#recuperation des valeurs utiles
                        
                print k
                if save==1: #enregistrement de la serie après interpolation
                    write_data(output_name,newNdvi,GeoTransform,Projection)
             #======================================================================
             #======================================================================
        else: #une image dont nombre de bandes est égale à nombre d'année
            print "création d'une image dont nombre de bandes est égale à nombre d'année"
            imageNDVI=lienNdvi +'\\'+ listeNdvi[0];
            [NDVI,GeoTransform,Projection]=open_data(imageNDVI)
            [nL,nC,i]=NDVI.shape
            print nL,nC
                
            nZ=len(listeNdvi)*23 #23images par années * le nombre d'années
             #newDoy=sp.empty(NDVI.shape,dtype='int16')
            print "________"
            newNdvi=sp.empty((nL,nC,nZ),dtype='float16') #variable qui stocke le  NDVI après interpolation
            print "_________"
            ndviXY=sp.empty((25),dtype='int16')  #recupère les 23 valeurs de la serie à la position (x,y)
            doyXY=sp.empty((25),dtype='int16')  #recupère les 23 valeurs de la serie à la position (x,y)
            print nL,nC,nZ
            for k in range(nYear+1):
                 try:
                     print k
                     imageNDVI=lienNdvi +'\\'+ listeNdvi[k];#lien qui permet d'acceder à la k-ième image
                     
                     imageDOY= lienDoy +'\\'+ listeDoy[k]; #lien qui permet d'acceder au k-ième DOY
                     
                     
                     [NDVI,GeoTransform,Projection]=open_data(imageNDVI) #stockage du NDVI dans un tableau
                     [DOY,GeoTransform,Projection]=open_data(imageDOY)   #stockage du DOY dans un tableau
                     
                     doyTheorique=sp.arange(25)*16+1    # Creation du DOY theorique     
                     
                      
                     for l in range(nL) :
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
                                 
                                 if (sg==1):
                                     
                                     newNdvi[l,c,deb:fin]=savgol_filter(newNDVIXY[1:-1], 9, 6);
                                 else:
                                     newNdvi[l,c,deb:fin]=newNDVIXY[1:-1] +0.0 #recuperation des valeurs utiles                            
                 except: 
                    print 'pluriannuelle'
               
                
            if save==1: #enregistrement de la serie après interpolation
                 output_name=lienSave+'\\'+prefixe +str(debutYear)+'_a_'+str(finYear)+'ans.tif' #lien d'enregistrement de la serie de l'année (année)
                 write_data(output_name,newNdvi,GeoTransform,Projection) 
#==============================================================================
