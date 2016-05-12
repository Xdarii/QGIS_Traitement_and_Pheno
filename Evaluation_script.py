# -*- coding: utf-8 -*-
"""
Created on Wed Apr 13 13:44:39 2016

@author: U115-H016
"""

import os
import matplotlib.pyplot as plot
from function_data_raster import*
from metriquePheno import*
import csv
import time
from clip import *
 
lien=r"D:\Mes Donnees\Dian_stage\Dian_scripts\Python\interpolation2_multi_sg\serie_temporelle_interpol_2000_a_2015ans.tif";

#lien=r"D:\Mes Donnees\Dian_stage\Dian_scripts\Python\interpolation2_multi_test_sg\serie_temporelle_interpol_2000_a_2015ans.tif";

[NDVI,GeoTransform,Projection]=open_data(lien)

#x=-3.70600
#y=11.25440

#x=-9.288
#y=10.376

#[x,y]=world2Pixel(GeoTransform, x, y)

#c=time.localtime()

sos1=[];eos1=[];los1=[]



m=sp.arange(16)
[L,C,r]=NDVI.shape
seuil1=0.35
seuil2=0.6
methode='trs'

metrique=sp.empty((L,C,10),dtype='float16') #variable qui stocke le  NDVI après interpolation

for k in range (6,7):
    
     deb=k*23
     fin=deb+23
     annee=2000+k
     print annee
     
     for x in range(L):
         for y in range(C):
             ndvi=NDVI[x,y,deb:fin]*0.0001
             liste=[]
            
             ndviMin=ndvi.min() #valeur minimale
             ndviMax=ndvi.max() #valeur maximale
              
             indMin=int(sp.median(sp.where(ndvi==ndviMin))) #indice du minimum
             indMax=int(sp.median(sp.where(ndvi==ndviMax))) #indice du max
              
             out1= metrique_pheno_vito(ndvi,seuil1,seuil2)
             outListe=metrique_pheno_param(ndvi,out1[0],out1[1],indMax+1)
             parametre=out1[0:3]+outListe
     
             metrique[x,y,:]=sp.array(parametre)
     output_name='D:\Mes Donnees\Dian_stage\Dian_scripts\Interface\parametre2\parametre2_'+str(annee)+'.tif'
     write_data(output_name,metrique,GeoTransform,Projection)
       
#         outListe=[area,areabef,areaaft,tsos_tmax,tmax_teos,pente1,pente2]
          

