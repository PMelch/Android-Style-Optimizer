'''
Created on 22.05.2012

@author: Peter Melchart
'''

import os
from xml.dom.minidom import parse
from pprint import pprint
import re


__version__ = "0.1"

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

class Variable(object):
    '''
    holds one value item used to refactor out the different values from one common style.
    can be either a dimen, color or integer value.
    
    '''
    
    def __init__(self, filename, name, value_type, value):
        self._filename = filename
        self._name = name
        self._type = value_type
        self._value = value
        
    def __str__(self):
        return "%s, %s, %s, %s"%(self._filename, self._name, self._value, self._type)
    
    def out(self):
        if self._type == Types.ITEM_TYPE_DIMEN:
            return "    <dimen name=\"%s\">%s</dimen>"%(self._name, self._value)
        elif self._type == Types.ITEM_TYPE_COLOR:
            return "    <color name=\"%s\">%s</color>"%(self._name, self._value)
        elif self._type == Types.ITEM_TYPE_INTEGER:
            return "    <item name=\"%s\" type=\"integer\">%s</item>"%(self._name, self._value)
        return ""
    
    def __repr__(self):
        return self.__str__()

class Style(dict):
    '''
    holds the elements of one style entry.
    with information about the filename(the xml file the style was defined in), the
    name and the parent (if defined)
     
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
        return "%s (%s) @ %s :\n  %s"%(self.name, self.parent, self.filename, ",\n  ".join([key+" "+val for key, val in self.items()]))
    
    def out(self):
        out = "    <style name=\"%s\" "%self.name
        if self.parent:
            out += "parent=\"%s\""%self.parent
        out += " >\n"
        for item, value in self.items():
            out += "        <item name=\"%s\">%s</item>\n"%(item, value)
        out += "    </style>\n"
        return out
    
    def __repr__(self):
        return self.__str__()
    

class StyleOptimizer(object):
    '''
    Handles the style optimization process.
    
    call optimize(resfolder, options), where
      resfolder is the folder where there are the values[-xxxx] folders.
      outfolder: the path where the optimized xml files should be generated.
      options is the object holding:
          verbose: if true, verbose output is generated
          overwrite: if true, already present file will get overwritten, other an warning is shown
          
          
    the optimizer tries to handle sitations where you have the same style defined in different 
    xml files containing different size, color or integer values.
    
    example:
    
     in values-xlarge/styles.xml:
         <style name="sample_style">
             <item name="android:layout_width">100dp</item>
             <item name="android:layout_height">100dp</item>
         <style>
         
     in values-xhadpi/styles.xml
         <style name="sample_style">
             <item name="android:layout_width">200dp</item>
             <item name="android:layout_height">100dp</item>
         <style>
    
    
     the optimize process would create a styles.xml file in values containing:
         <style name="sample_style">
             <item name="android:layout_width">@dimen/SampleStyle_layoutWidth</item>
             <item name="android:layout_height">100dp</item>
         <style>
         
        and two styles.xml file in values-xlarge and values-xhdpi, resp.
        
        values-xlarge/styles.xml:
             <dimen name="SampleStyle_layoutWidth">100dp</dimen>
         
        values-xhdpi/styles.xml:
             <dimen name="SampleStyle_layoutWidth">200dp</dimen>
         
     
     
     Style declarations where one version has - say - a dimension as layout width, but the other
     version has "match_parent" cannot be merged, since a dimen item cannot hold the value "match_parent".
     
     Same goes for styles that have different items defined.
    
    '''
    
    _dimen_rex = re.compile(r"^(?:@.*?dimen.*|-?\d+\s*(?:sd?|dp?|pt|px|mm|in)$)")
    _color_rex = re.compile(r"^(?:@.*?color.*|#[\da-f]{3}|#[\da-f]{4}|#[\da-f]{6}|#[\da-f]{8})$", re.I)
    _int_rex = re.compile(r"^-?\d+$")

    def optimize(self, resfolder, outfolder, options):
        '''
        call this method.
        
        '''

        absresfolder = os.path.abspath(resfolder)

        if not os.path.exists(absresfolder):
            print "ERROR: Folder does not exists:",absresfolder
            return
        
        self._outfolder = outfolder
        self._options = options
        if options.verbose:
            print "Root folder: ",absresfolder
            
        
        self._styles = dict()
        self._style_locations = dict()
        self._warnings = 0
        self._extra_nodes = dict()
        
                    
        self._fetch_styles(resfolder)
        self._optimize()
        
        print "Warnings:",self._warnings


    def _fetch_styles(self, resfolder):
        '''
        retrieves all style declarations in all values subfolder in the given resfolder.        
        
        '''
        
        for folder, _, files in os.walk(resfolder):
            foldername = os.path.basename(folder)
            if not foldername.startswith("values"):
                continue
            if self._options.verbose:
                print foldername
                
            self._extra_nodes[foldername] = dict()
            
            for filename in files:
                if filename.endswith(".xml"):
                    self._extract_content(foldername, os.path.join(folder, filename))

    def _extract_content(self, res_type, filepath):
        '''
        extracts styles from one xml file and stores them in self._styles and self._style_locations
        
        '''
        
        try:
            dom = parse(filepath)
        except:
            return 
        
        style_file = os.path.basename(filepath)
        self._extra_nodes[res_type][style_file] = []
        
        if self._options.verbose:
            print "   ",style_file
        
        if dom.documentElement.nodeName != "resources":
            return
        
        
        for n in dom.documentElement.childNodes:
            if n.nodeName=="style":
                self._extract_style(res_type, style_file, n)
            else:
                if n.nodeType == n.ELEMENT_NODE:
                    self._extra_nodes[res_type][style_file].append(n)
            
    def _extract_style(self, res_type, style_file, style_element):
            if not res_type in self._styles:
                self._styles[res_type] = dict()
            style = Style(style_file, style_element)
            style_name = style.name
            # check if there was already a equally named style for that qualified resource type
            if style_name in self._styles[res_type]:
                self._warning("%s: the style is already defined in %s."%(style_name, self._styles[res_type][style_name].name))
            self._styles[res_type][style_name] = style
            
            if not style_name in self._style_locations:
                self._style_locations[style_name] = []
            self._style_locations[style_name].append(res_type)
            
        
    def _get_item_type(self, value):
        '''
        returns the value type for the given type. possible values are:
        
        Types.ITEM_TYPE_DIMEN (1)
        Types.ITEM_TYPE_COLOR (2)
        Types.ITEM_TYPE_INTEGER (3)
        Types.ITEM_TYPE_OTHER (0)
        
        
        '''
        
        if self._dimen_rex.match(value):
            return Types.ITEM_TYPE_DIMEN
        if self._color_rex.match(value):
            return Types.ITEM_TYPE_COLOR
        if self._int_rex.match(value):
            return Types.ITEM_TYPE_INTEGER
        return Types.ITEM_TYPE_OTHER

    
    def _merge_style(self, style_name):
        '''
        tries to merge the style with the given name.
        if the style cannot get merged into one style the 
        style will be written to it's style file in the output folder.
        
        '''
        
        
        mergable_items = set()
        if self._options.verbose:
            print "Trying to merge",style_name
        
        locs = self._style_locations[style_name]
        
        if len(locs)==1 and locs[0]=="values":
            # it's already a central style. skip
            self._write_style_unchanged(style_name)
            return
        
        num_items = None
        for style_loc in locs:
            style = self._styles[style_loc][style_name]
            if num_items is None:
                num_items = len(style)
            elif len(style) != num_items:
                # different amount of items, cannot be merged automatically (for now).
                self._warning("%s: number of items differ"%style_name)
                # append to outfile
                self._write_style_unchanged(style_name)
                return 
            
        
        found_style = None
        for style_loc in locs:
            style = self._styles[style_loc][style_name]
            found_style = style
            for name, value in style.items():
                same_value = True
                item_type = self._get_item_type(value)
                for check_loc in locs:
                    if check_loc == style_loc:
                        continue
                    check_style = self._styles[check_loc][style_name]
                    check_value = check_style[name] 
                    if self._get_item_type(check_value) != item_type:
                        self._warning("%s: item types for %s differ in %s and %s (%s vs %s)"%(style_name, name, style_loc, check_loc, value, check_value))
                        self._write_style_unchanged(style_name)
                        return 
                    
                    if value!=check_value:
                        if item_type==Types.ITEM_TYPE_OTHER:
                            self._warning("%s: style not mergable. values differ for item %s (%s vs %s)"%(style_name, name, value, check_value))
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
            res_type_prefix = ""
            if item_type == Types.ITEM_TYPE_COLOR:
                res_type_prefix = "@color/"
            elif item_type == Types.ITEM_TYPE_DIMEN:
                res_type_prefix = "@dimen/"
            elif item_type == Types.ITEM_TYPE_INTEGER:
                res_type_prefix = "@integer/"
            varname = self._get_save_varname(merged_style.name+"-"+item.replace("android:", ""))
            merged_style[item] = res_type_prefix+varname 
            
            for style_loc in locs:
                style = self._styles[style_loc][style_name]
                self._prepare_dict(style_loc, style.filename)
                self._out_files[style_loc][style.filename].append(Variable(style.filename, varname, item_type, style[item]))
                
        self._prepare_dict("values", merged_style.filename)
        self._out_files["values"][merged_style.filename].append(merged_style)
        if self._options.verbose:
            print "Mergable:  ",mergable_items
        
    def _prepare_dict(self, style_loc, filename):
        '''
        makes sure that self._out_files contains a key for style_loc
        and that the value of style_loc contains a key for filename.
        
        '''
        
        if not style_loc in self._out_files:
            self._out_files[style_loc] = dict()
        if not filename in self._out_files[style_loc]:
            self._out_files[style_loc][filename] = []
             
    def _write_style_unchanged(self, style_name):
        '''
        writes the style with the given name to all the files where it is defined.
        this happens when a style cannot get merged
        
        '''
        
        locs = self._style_locations[style_name]
        for style_loc in locs:
            style = self._styles[style_loc][style_name]
            #self._prepare_dict(style_loc, style.filename)
            #self._out_files[style_loc][style.filename].append(style)
            self._extra_nodes[style_loc][style.filename].append(style) 
        
    
    def _get_save_varname(self, name):
        '''
        returns a readable version of name.
        converts names containing "_" into camel case names
        with the last part ( the item name ) separated by a _
        
        '''
        
        name = name.replace(".", "_")
        if len(name)>0:
            name = name[0].upper()+name[1:]
        while True:
            i = name.find("_")
            if i==-1:
                break
            if i>=len(name)-1:
                break
            name = name[:i]+name[i+1].upper()+name[i+2:]
        return name.replace("-","_")
    
    def _optimize(self):
        '''
        tries to merge all styles and writes the files to the output folder (if present)
        
        '''
        
        self._out_files = dict()
        
        for style_name, locs in self._style_locations.items():
            if len(locs)==1 and locs[0]!="values":
                self._warning("style %s is not defined in the main values file but only in %s"%(style_name, locs[0]))
                self._write_style_unchanged(style_name)
                
            self._merge_style(style_name)
                
                
        if self._options.verbose:
            pprint (self._out_files)

        self._write_files()

    def _write_files(self):            
        if self._outfolder:
            outbase = self._outfolder
            for value_folder, filenames in self._out_files.items():
                for filename in filenames:
                    outfilename = os.path.join(outbase, value_folder, filename)
                    try:
                        os.makedirs(os.path.dirname(outfilename))
                    except: pass
                    if os.path.exists(outfilename) and not self._options.overwrite:
                        self._warning("target file %s already exists. skipping."%outfilename)
                        continue
                    outfile = open(outfilename, "wt")
                    outfile.write("""<?xml version="1.0" encoding="utf-8"?>\n""")
                    outfile.write("""<resources>\n""")
                    outfile.write("""\n\n\n    <!-- original elements -->\n\n\n""")
                    for node in self._extra_nodes[value_folder][filename]:
                        if isinstance(node, Style):
                            outfile.write(node.out())
                        else:
                            outfile.write("    "+node.toxml())
                        outfile.write("\n")
                    outfile.write("""\n\n\n    <!-- created elements --> \n\n\n""")
                    entries = self._out_files[value_folder][filename]
                    # write all variable entries
                    for entry in entries:
                        if isinstance(entry, Variable):
                            outfile.write(entry.out())
                            outfile.write("\n")
                    # write all style entries
                    outfile.write("\n\n")
                    for entry in entries:
                        if isinstance(entry, Style):
                            outfile.write(entry.out())
                            outfile.write("\n")
                    outfile.write("""</resources>\n""")
                    outfile.close()
                
    def _warning(self, msg):
        self._warnings += 1
        print "WARNING>",msg
