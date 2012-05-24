'''
Created on 22.05.2012

@author: Peter Melchart

'''

import styleoptimizer
import sys


if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser(usage="usage: %prog [options] res_folder", version=styleoptimizer.__version__)
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="if set, enables verbose output.")
    parser.add_option("-o", "--outfolder", dest="outfolder", action="store", default=None, help="if set, writes the generated files to the specified out folder. if no folder is specified, no output is generated.")
    options, args = parser.parse_args()
    
    if not args:
        parser.print_usage()
        sys.exit(-1)
    
    optimizer = styleoptimizer.StyleOptimizer()
    resfolder = args[0]
    optimizer.optimize(resfolder, options)
