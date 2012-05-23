'''
Created on 22.05.2012

@author: peter
'''
import os
from xml.dom.minidom import parse
from pprint import pprint
import re

class Types(object):
    ITEM_TYPE_DIMEN   = 1
    ITEM_TYPE_COLOR   = 2
    ITEM_TYPE_INTEGER = 3
    ITEM_TYPE_OTHER   = 0
    
    
    

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

class Entry(object):
    def __init__(self, filename, name, value_type, value):
        self._filename = filename
        self._name = name
        self._type = value_type
        self._value = value
        
    def __str__(self):
        if self._type == Types.ITEM_TYPE_DIMEN:
            return "<dimen name=\"%s\">%s</dimen>"%(self._name, self._value)
        elif self._type == Types.ITEM_TYPE_COLOR:
            return "<color name=\"%s\">%s</color>"%(self._name, self._value)
        elif self._type == Types.ITEM_TYPE_INTEGER:
            return "<item name=\"%s\" type=\"integer\">%s</item>"%(self._name, self._value)
        return ""
    def __repr__(self):
        return self.__str__()

class Style(dict):
    '''
    
    '''
    
    def __init__(self, filename, element=None, name=None, parent=None):
        self.filename = filename
        if element:        
            self.name = element.getAttribute("name")
            self.parent = element.getAttribute("parent")
            
            item_elements = element.getElementsByTagName("item")
            for item_element in item_elements:
                self.__setitem__(item_element.getAttribute("name"), getText(item_element.childNodes))
        else:
            self.name = name
            self.parent = parent
            
        #print self._name, self._parent
        #print self._items

    
    def __str__(self):
        return "TODO"
    

class StyleOptimizer(object):
    '''
    
    '''
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
            style_name = style.name
            # check if there was already a equally named style for that qualified resource type
            if style_name in self._styles[res_type]:
                self._warning("the style %s is already defined in %s."%(style_name, self._styles[res_type][style_name].name))
            self._styles[res_type][style_name] = style
            
            if not style_name in self._style_locations:
                self._style_locations[style_name] = []
            self._style_locations[style_name].append(res_type)
            
        
    def _get_item_type(self, value):
        if self._dimen_rex.match(value):
            return Types.ITEM_TYPE_DIMEN
        if self._color_rex.match(value):
            return Types.ITEM_TYPE_COLOR
        if self._int_rex.match(value):
            return Types.ITEM_TYPE_INTEGER
        return Types.ITEM_TYPE_OTHER

    
    def _merge_style(self, style_name):
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
                # append to outfile
                self._write_style_unchanged(style_name)
                return 
            
        
        found_style = None
        for style_loc in locs:
            style = self._styles[style_loc][style_name]
            found_style = style
            same_value = True
            for name, value in style.items():
                item_type = self._get_item_type(value)
                for check_loc in locs:
                    if check_loc == style_loc:
                        continue
                    check_style = self._styles[check_loc][style_name]
                    check_value = check_style[name] 
                    if self._get_item_type(check_value) != item_type:
                        self._warning("item types for %s differ in %s and %s (%s vs %s)"%(name, style_loc, check_loc, value, check_value))
                        self._write_style_unchanged(style_name)
                        return 
                    
                    if value!=check_value:
                        if item_type==Types.ITEM_TYPE_OTHER:
                            self._warning("style not mergable. values differ for item %s (%s vs %s)"%(name, value, check_value))
                            self._write_style_unchanged(style_name)
                            return
                        else:
                            same_value = False 
                    
                        
                if not same_value and item_type in [Types.ITEM_TYPE_COLOR, Types.ITEM_TYPE_DIMEN, Types.ITEM_TYPE_INTEGER]:
                    mergable_items.add((name, item_type))

        merged_style = Style(found_style.filename, name=found_style.name, parent=found_style.parent)
        merged_style.filename = found_style.filename
        merged_style.update(found_style)
        for item, item_type in mergable_items:
            varname = ""
            if item_type == Types.ITEM_TYPE_COLOR:
                varname = "@color/"
            elif item_type == Types.ITEM_TYPE_DIMEN:
                varname = "@dimen/"
            elif item_type == Types.ITEM_TYPE_INTEGER:
                varname = "@integer/"
            varname += self._get_save_varname(merged_style.name+"_"+item.replace("android:", ""))
            merged_style[item] = varname 
            
            for style_loc in locs:
                style = self._styles[style_loc][style_name]
                if not style_loc in self._out_files:
                    self._out_files[style_loc] = []
                self._out_files[style_loc].append(Entry(style.filename, varname, item_type, style[item]))
                
        if not "values" in self._out_files:
            self._out_files["values"] = []
        self._out_files["values"].append(merged_style)
        print "  ",mergable_items
        
    def _write_style_unchanged(self, style_name):
        locs = self._style_locations[style_name]
        for style_loc in locs:
            if not style_loc in self._out_files:
                self._out_files[style_loc] = []
            self._out_files[style_loc].append(self._styles[style_loc][style_name]) 
        
    
    def _get_save_varname(self, name):
        name = name.replace(".", "_")
        while True:
            i = name.find("_")
            if i==-1:
                break
            if i>=len(name)-1:
                break
            name = name[:i]+name[i+1].upper()+name[i+2:]
        return name
    
    def _optimize(self):
        self._out_files = dict()
        
        for style_name, locs in self._style_locations.items():
            if len(locs)==1 and locs[0]!="values":
                self._warning("style %s is not defined in the main values file but only in %s"%(style_name, locs[0]))
                self._write_style_unchanged(style_name)
                
            self._merge_style(style_name)
                
                
        pprint (self._out_files)
                
    def _warning(self, msg):
        self._warnings += 1
        print "WARNING>",msg
