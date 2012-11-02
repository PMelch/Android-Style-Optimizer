'''
Created on 22.05.2012

@author: Peter Melchart

'''

import styleoptimizer
import sys


if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser(usage="usage: %prog [options] res_folder outfolder", version=styleoptimizer.__version__)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="if set, enables verbose output.")
    parser.add_option("-o", "--overwrite", dest="overwrite", action="store_true", default=False, help="if set, generated files will overwrite already present files.")
    options, args = parser.parse_args()
    
    if not args:
        parser.print_usage()
        sys.exit(-1)
    
    resfolder = args[0]
    outfolder = args[1] if len(args)>1 else None        
    
    if not args:
        parser.print_usage()
        sys.exit(-1)
    
    optimizer = styleoptimizer.StyleOptimizer()
    optimizer.optimize(resfolder, outfolder, options)
