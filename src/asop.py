'''
Created on 22.05.2012

@author: peter
'''
import styleoptimizer
import sys




if __name__ == '__main__':
    import optparse
    parser = optparse.OptionParser(usage="usage: %prog [options] res_folder")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False, help="if set, enables verbose output.")
    parser.add_option("-t", "--test", dest="test", action="store_true", default=False, help="if set, just print the changes, without actually applying them.")
    options, args = parser.parse_args()
    
    if not args:
        parser.print_usage()
        sys.exit(-1)
    
    optimizer = styleoptimizer.StyleOptimizer()
    resfolder = args[0]
    optimizer.optimize(resfolder, options)
