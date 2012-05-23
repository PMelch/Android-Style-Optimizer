'''
Created on 22.05.2012

@author: peter
'''
import os

class StyleOptimizer(object):
    '''
    
    '''


    def optimize(self, resfolder, options):
        print(resfolder)
        print(os.path.abspath(resfolder))
        
        for folder, subfolders, files in os.walk(resfolder):
            print(folder, subfolders, files)

