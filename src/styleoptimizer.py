'''
Created on 22.05.2012

@author: peter
'''
import os
from xml.dom.minidom import parse
from pprint import pprint
import re

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

class Style(dict):
    '''
    
    '''
    
    def __init__(self, filename, element):
        self._filename = filename        
        self._name = element.getAttribute("name")
        self._parent = element.getAttribute("parent")
        
        item_elements = element.getElementsByTagName("item")
        for item_element in item_elements:
            self.__setitem__(item_element.getAttribute("name"), getText(item_element.childNodes))
            
        #print self._name, self._parent
        #print self._items

    def get_name(self):
        return self._name
    

class StyleOptimizer(object):
    '''
    
    '''

    ITEM_TYPE_DIMEN   = 1
    ITEM_TYPE_COLOR   = 2
    ITEM_TYPE_INTEGER = 3
    ITEM_TYPE_OTHER   = 0

    _dimen_rex = re.compile(r"^(?:@.*?dimen.*|-?\d+\s*(?:sd?|dp?|pt|px|mm|in)$)")
    _color_rex = re.compile(r"^(?:@.*?color.*|#[\da-f]{3}|#[\da-f]{4}|#[\da-f]{6}|#[\da-f]{8})$", re.I)
    _int_rex = re.compile(r"^-?\d+$")

    def optimize(self, resfolder, options):
        self._options = options
        if options.verbose:
            print "Root folder: ",os.path.abspath(resfolder)
        
        self._styles = dict()
        self._style_locations = dict()
        self._warnings = 0
        
        for folder, _, files in os.walk(resfolder):
            foldername = os.path.basename(folder)
            if not foldername.startswith("values"):
                continue
            if options.verbose:
                print foldername
            for filename in files:
                if filename.endswith(".xml"):
                    self._extract_styles(foldername, os.path.join(folder, filename))
                    
                    
        #pprint (self._style_locations)  
        self._optimize()
        
        print "Warnings:",self._warnings



    def _extract_styles(self, res_type, filepath):
        try:
            dom = parse(filepath)
        except:
            return 
        
        style_file = os.path.basename(filepath)
        
        if self._options.verbose:
            print "   ",style_file
        
        style_elements = dom.getElementsByTagName("style")
        for style_element in style_elements:
            if not res_type in self._styles:
                self._styles[res_type] = dict()
            style = Style(style_file, style_element)
            style_name = style.get_name()
            # check if there was already a equally named style for that qualified resource type
            if style_name in self._styles[res_type]:
                self._warning("the style %s is already defined in %s."%(style_name, self._styles[res_type][style_name].get_name()))
            self._styles[res_type][style_name] = style
            
            if not style_name in self._style_locations:
                self._style_locations[style_name] = []
            self._style_locations[style_name].append(res_type)
            
        
    def _get_item_type(self, value):
        if self._dimen_rex.match(value):
            return self.ITEM_TYPE_DIMEN
        if self._color_rex.match(value):
            return self.ITEM_TYPE_COLOR
        if self._int_rex.match(value):
            return self.ITEM_TYPE_INTEGER
        return self.ITEM_TYPE_OTHER
    
    def _is_style_mergable(self, style_name):
        mergable_items = set()
        print style_name
        
        locs = self._style_locations[style_name]
        num_items = None
        for style_loc in locs:
            style = self._styles[style_loc][style_name]
            if num_items is None:
                num_items = len(style)
            elif len(style) != num_items:
                # different amount of items, cannot be merged automatically (for now).
                if self._options.verbose:
                    print "number of items differ for",style_name 
                return False
            
        
        for style_loc in locs:
            style = self._styles[style_loc][style_name]
            for name, value in style.items():
                item_type = self._get_item_type(value)
                for check_loc in locs:
                    if check_loc == style_loc:
                        continue
                    check_style = self._styles[check_loc][style_name]
                    check_value = check_style[name] 
                    if self._get_item_type(check_value) != item_type:
                        self._warning("item types for %s differ in %s and %s (%s vs %s)"%(name, style_loc, check_loc, value, check_value))
                        return False
                    
                    if value!=check_value and item_type==self.ITEM_TYPE_OTHER:
                        self._warning("style not mergable. values differ for item %s (%s vs %s)"%(name, value, check_value))
                        return False
                        
                if item_type in [self.ITEM_TYPE_COLOR, self.ITEM_TYPE_DIMEN, self.ITEM_TYPE_INTEGER]:
                    mergable_items.add(name)

        print "  ",mergable_items
        
    
    
    def _merge_style(self, syle_name):
        pass
    
    
    def _optimize(self):
        for style_name, locs in self._style_locations.items():
            if len(locs)==1 and locs[0]!="values":
                self._warning("style %s is not defined in the main values file but only in %s"%(style_name, locs[0]))
                
            if self._is_style_mergable(style_name):
                self._merge_style(syle_name)
                
                
    def _warning(self, msg):
        self._warnings += 1
        print "WARNING>",msg
