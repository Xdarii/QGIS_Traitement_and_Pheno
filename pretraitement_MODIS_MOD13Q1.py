# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 11:10:41 2016

@author: U115-H016
"""



from interpo_lineaire_DOY16jours import interpo_lineaire_DOY16jours
from decoupage_et_serie_temporelle import decoupage_et_serie_temporelle





var=int(input("faites un choix entre :\n-1 decoupage  \n-2 interpolation a 16 jours\n"))

if var==1: #decoupage
    print "decoupage"
    #==========================================================================
    debutYear=2000
    lienDonnee=r"D:\Mes Donnees\Dian_stage\Leroux\Dian\DOY";
    lienSave=r'D:\Mes Donnees\Dian_stage\Dian_scripts\Python\decoupage_emprise_Test\DOY'
    nomDonnee='DOY'
    zoneEtudes=r'D:\Mes Donnees\Dian_stage\Qgis\test\Zone_Test.shp'
    pluriAnnuelle=0
    decoupage_et_serie_temporelle(lienDonnee,zoneEtudes,lienSave,debutYear,nomDonnee,pluriAnnuelle)    
    print 'terminé'    
    #==========================================================================

elif (var==2):
    print "interpolation"
    #==========================================================================
    lienNdvi='D:\Mes Donnees\Dian_stage\Dian_scripts\Python\decoupage_emprise_Test\NDVI'
    lienDoy='D:\Mes Donnees\Dian_stage\Dian_scripts\Python\decoupage_emprise_Test\DOY'
    lienSave='D:\Mes Donnees\Dian_stage\Dian_scripts\Python\interpolation2_multi_test_sg'
    finYear=2015
    debutYear=2000
    save=1
    sg=1
    pluriAnnuelle=1        
    interpo_lineaire_DOY16jours(lienNdvi,lienDoy,lienSave,debutYear,finYear,save,pluriAnnuelle,sg)
    #==========================================================================
elif (var==3):
    print "calcul d'anomalie"
    
    
else:
    print "faites un choix entre 1 decoupage et 2 interpolation à 16 jours"