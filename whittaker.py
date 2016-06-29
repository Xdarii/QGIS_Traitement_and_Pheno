# -*- coding: utf-8 -*-
"""
Created on Tue May 10 10:43:51 2016

@author: U115-H016
"""
import scipy as sp


def whittaker(inY,inL=15,inD=2):
    
    """
    cette fonction permet de lisser le signal d'entrée en utilisant le filtre de Whittaker.
    ref: Eilers, P.H.C. (2003) "A perfect smoother", Analytical Chemistry, 75, 3631 – 3636.
    
    Entrée:
    inY: le signal à lisser
    
    inL: correspond au parmètre de lissage. Plus il est grand plus le lissage est élevé. par défaut à 15
    comme dans l'article : 
    Geng, L.; Ma, M.; Wang, X.; Yu, W.; Jia, S.; Wang, H.	Comparison of Eight Techniques 
    for Reconstructing Multi-Satellite Sensor Time-Series NDVI Data Sets in the Heihe River Basin, China. 
    Remote Sens. 2014, 6, 2024-2049.
    
    inD: ordre des differences de pénalités
    
    """
    
    m=sp.size(inY)
    E=sp.eye(m)
    D=sp.diff(E,inD)
    Z=E+ (inL*sp.dot(D,sp.transpose(D)))
    ws=sp.linalg.solve(Z,inY)
    
    return ws
    

