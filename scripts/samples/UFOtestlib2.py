#!/usr/bin/env python
'UFO handling script under development'
__url__ = 'http://github.com/silnrsi/pysilfont'
__copyright__ = 'Copyright (c) 2014, SIL International  (http://www.sil.org)'
__license__ = 'Released under the MIT License (http://opensource.org/licenses/MIT)'
__author__ = 'David Raymond'
__version__ = '0.0.1'

from xml.etree import ElementTree as ET
import sys, os
from UFOtestlib1 import *

class _Ucontainer(object) :
    # Parent class for other objects (eg Ulayer)
    def __init_(self) :
        self._contents = {}
    # Define methods so it acts like an imutable container
    # (changes should be made via object functions etc)
    def __len__(self):
        return len(self._contents)
    def __getitem__(self, key):
        return self._contents[key]
    def __iter__(self):
        return iter(self._contents)
    def keys(self) :
        return self._contents.keys()

class Uelement(_Ucontainer) :
    # Class for an etree element. Mainly used as a parent class
    # For each tag in the element, returns list of sub-elements with that tag
    def __init__(self,element) :
        self.element = element
        self.reindex()
        
    def reindex(self) :
        self._contents = {}
        element = self.element
        for i in range(len(element)) :
            tag = element[i].tag
            if tag in self._contents :
                self._contents[tag].append(element[i])
            else :
                self._contents[tag] = [element[i]]

    def remove(self,subelement) :
        self._contents[subelement.tag].remove(subelement)
        self.element.remove(subelement)
        
    def append(self,element) :
        self._contents[subelement.tag].append(subelement)
        self.element.append(subelement)
        
    def insert(self,index,element) :
        self._contents[subelement.tag].insert(index,subelement)
        self.element.insert(index,subelement)

class Ufont(object) :
    """ Object to hold all the data from a UFO"""
    
    def __init__(self, ufodir = None ) :
        if ufodir:
            self.ufodir = ufodir
            print 'Opening UFO for input: ',ufodir
            if not os.path.isdir(ufodir) :
                print ufodir + " not a directory"
                sys.exit()
            # Read list of files and folders in top 2 levels; anything at lower levels just needs copying
            self.tree=dirTree(ufodir)
            #self.path,base) = os.path.split(ufodir)
            self.metainfo = self._readPlist("metainfo.plist")
            self.UFOversion = self.metainfo["formatVersion"][1].text
            # Read other top-level plists
            if "fontinfo.plist" in self.tree : self.fontinfo = self._readPlist("fontinfo.plist")
            if "groups.plist" in self.tree : self.groups = self._readPlist("groups.plist")
            if "kerning.plist" in self.tree : self.kerning = self._readPlist("kerning.plist")
            if "lib.plist" in self.tree : self.lib = self._readPlist("lib.plist")
            if self.UFOversion == "2" : # Create a dummy layer contents so 2 & 3 can be handled the same
                self.layercontents = Uplist(font = self)
                dummylc = "<plist>\n<array>\n<array>\n<string>public.default</string>\n<string>glyphs</string>\n</array>\n</array>\n</plist>"
                self.layercontents.etree = ET.fromstring(dummylc)
                self.layercontents.populate_dict()
            else :
                self.layercontents = self._readPlist("layercontents.plist")
            # Process the glyphs directories)
            self.layers = []
            for i in sorted(self.layercontents.keys() ) :
                layername = self.layercontents[i][0].text
                layerdir = self.layercontents[i][1].text
                print "Processing Glyph Layer " + str(i) + ": " + layername,layerdir
                if layerdir in self.tree:
                    self.layers.append( Ulayer(layername, layerdir, self) )
                else :
                    print "Glyph directory",layerdir, "missing"
                    sys.exit()
            # Set initial defaults for outparams            
            self.outparams = { "indentIncr" : "  ", "indentFirst" : "  ", "plistIndentFirst" : "", 'sortPlists' : True }
            self.outparams["UFOversion"] = self.UFOversion
            self.outparams["attribOrders"] = {
                'glif' : makeAttribOrder([
                    'pos', 'width', 'height', 'fileName', 'base', 'xScale', 'xyScale', 'yxScale', 
                    'yScale', 'xOffset', 'yOffset', 'x', 'y', 'angle', 'type', 'smooth', 'name', 
                    'format', 'color', 'identifier'])
                }

    def _readPlist(self, filen) :
        if filen in self.tree :
            return Uplist(font = self, filen = filen)
        else :
            print ufodir,filen, "does not exist2"
            sys.exit()
    
    def write(self, outdir) :
        ''' Write UFO out to disk, based on values set in self.outparams'''
        
        if not os.path.exists(outdir) :
            try:
                os.mkdir(outdir)
            except Exception as e :
                print e
                sys.exit()
        if not os.path.isdir(outdir) :
            print outdir + " not a directory"
            sys.exit()
        UFOversion = self.outparams["UFOversion"]
        # Update metainfo.plist and write out
        self.metainfo["formatVersion"][1].text = str(UFOversion)
        self.metainfo["creator"][1].text = "org.sil.sripts" # What should this be? pysilfont?
        writeXMLobject(self.metainfo, self.outparams, outdir, "metainfo.plist")
        # Write out other plists
        if "fontinfo" in self.__dict__ : writeXMLobject(self.fontinfo, self.outparams, outdir, "fontinfo.plist")
        if "groups" in self.__dict__ : writeXMLobject(self.groups, self.outparams, outdir, "groups.plist")
        if "kerning" in self.__dict__ : writeXMLobject(self.kerning, self.outparams, outdir, "kerning.plist")
        if "lib" in self.__dict__ : writeXMLobject(self.lib, self.outparams, outdir, "lib.plist")
        if UFOversion == 3 : writeXMLobject(self.layercontents, self.outparams, outdir, "layercontents.plist")
        # Write out glyph layers
        for layer in self.layers : layer.write(outdir,self.outparams)
        # Copy other files and directories


class Ulayer(_Ucontainer) :
    
    def __init__(self, layername, layerdir, font) :
        self._contents = {}
        self.layername = layername
        self.layerdir = layerdir
        self.font = font
        layertree = font.tree[layerdir]['tree']
        fulldir = os.path.join(font.ufodir,layerdir)
        self.contents = Uplist( font = font, dirn = fulldir, filen = "contents.plist" )
        for glyphn in sorted(self.contents.keys()) :
            glifn = self.contents[glyphn][1].text
            if glifn in layertree :
                self._contents[glyphn] = Uglif(layer = self, filen = glifn)
            else :
                print "Missing glif ",glifn, "in", fulldir
                sys.exit()
                
    def write(self,outdir,params) :
        print "Processing layer", self.layername
        fulldir = os.path.join(outdir,self.layerdir)
        if not os.path.exists(fulldir) :
            try:
                os.mkdir(fulldir)
            except Exception as e :
                print e
                sys.exit()
        if not os.path.isdir(fulldir) :
            print fulldir + " not a directory"
            sys.exit()
        writeXMLobject(self.contents, params, fulldir, "contents.plist")
        for glyphn in self :
            glyph = self._contents[glyphn]
            writeXMLobject(glyph, params, fulldir, glyph.filen)
        # Need to check UFO version and outpur corret glif version
            
class Uplist(xmlitem) :
    
    def __init__(self, font = None, dirn = None, filen = None, parse = True) :
        if dirn is None :
            if font : dirn = font.ufodir
        xmlitem.__init__(self, dirn, filen, parse)
        self.type = "plist"
        self.font = font
        self.outparams = None
        if filen and dirn : self.populate_dict()
    
    def populate_dict(self) :
        self._contents.clear() # Clear existing contents, if any
        pl = self.etree[0]
        if pl.tag == "dict" :
            for i in range(0,len(pl),2):
                key = pl[i].text
                self._contents[key] = [pl[i],pl[i+1]] # The two elements for the item
        else : # Assume array of 2 element arrays (eg layercontents.plist)
            for i in range(len(pl)) :
                self._contents[i] = pl[i]
    
    def sort(self) : # For dict-based plists sort keys alphabetically
        if self.etree[0].tag == "dict" :
            self.populate_dict() # Recreate dict in case changes have been made
            i=0
            for key in sorted(self.keys()):
                self.etree[0][i]=self._contents[key][0]
                self.etree[0][i+1]=self._contents[key][1]
                i=i+2
    
class Uglif(xmlitem) :
    # Unlike plists, glifs can have multiples of some sub-elements (eg anchors) so create lists for those
    
    def __init__(self, layer = None, filen = None, parse = True) :
        if layer is None :
            dirn = None
        else :
            dirn = os.path.join(layer.font.ufodir, layer.layerdir)
        xmlitem.__init__(self, dirn, filen, parse)
        self.type="glif"
        self.layer = layer
        self.outparams = None
        self.advance = None
        self.unicodes = []
        self.note = None
        self.image = None
        self.guideline = None
        self.anchors = []
        self.outline = None
        self.lib = None

        if self.etree is not None : self.process_etree()

    def process_etree(self) :
        et = self.etree
        self.name = getattrib(et,"name")
        self.format = getattrib(et,"format")
        if self.format is None :
            if self.layer.font.UFOversion == 3 :
                self.format = '2'
            else : self.format = '1'
        for i in range(len(et)) :
            element = et[i]
            tag = element.tag
            if tag == 'advance' : self.advance = Uadvance(self,element)
            if tag == 'unicode' : self.unicodes.append(Uunicode(self,element))
            if tag == 'outline' : self.outline = Uoutline(self,element)
            if tag == 'lib' : self.lib = Ulib(self,element)
            if self.format == 2 :
                if tag == 'note' : self.note = Unote(self,element)
                if tag == 'image' : self.image = Uimage(self,element)
                if tag == 'guideline' : self.guideline = Uguideline(self,element)
                if tag == 'anchor' : self.anchors.append(Uanchor(self,element))
        # Convert UFO2 style anchors to UFO3 anchors
        if self.outline is not None and self.format == "1":
            for contour in self.outline.contours :
                if contour.UFO2anchor :
                    self.outline.glif.addanchor(contour.UFO2anchor)
                    self.outline.removeobject(contour, "contour")
        self.format = "2"
        et.set("format",str(2))

    def addanchor(self,anchor) :
        # Add an anchor to glif
        # Needs to be before any outline or lib elements if they exist
        element = ET.Element("anchor",anchor)
        if self.outline is None and self.lib is None :
            self.etree.append(element)
            self.anchors.append(Uanchor(self,element))
        else :    
            if self.outline is not None :
                index = self.etree.getchildren().index(self.outline.element)
            else :
                index = self.etree.getchildren().index(self.lib.element)
            self.etree.insert(index,element)
            self.anchors.append(Uanchor(self,element))
    
    def setUFO2anchors(self) :
        # Convert UFO3 anchors to UFO2 contour-style anchors
        for anchor in self.anchors :
            pass
         
class Uadvance(Uelement) :
    
    def __init__(self, glif, element) :
        super(Uadvance,self).__init__(element)
        print ">>>> advance contents"
        for tag in self._contents :
            print tag, self._contents[tag]

class Uunicode(Uelement) :
    
    def __init__(self, glif, element) :
        super(Uunicode,self).__init__(element)
        print ">>>> unicode contents"
        for tag in self._contents :
            print tag, self._contents[tag]

class Unote(Uelement) :
    
    def __init__(self, glif, element) :
        super(Unote,self).__init__(element)
        print ">>>> note contents"
        for tag in self._contents :
            print tag, self._contents[tag]

class Uimage(Uelement) :
    
    def __init__(self, glif, element) :
        super(Uimage,self).__init__(element)
        print ">>>> image contents"
        for tag in self._contents :
            print tag, self._contents[tag]

class Uguideline(Uelement) :
    
    def __init__(self, glif, element) :
        super(Uguideline,self).__init__(element)
        print ">>>> guideline contents"
        for tag in self._contents :
            print tag, self._contents[tag]

class Uanchor(Uelement) :
    
    def __init__(self, glif, element) :
        super(Uanchor,self).__init__(element)
        print ">>>> anchor contents"
        for tag in self._contents :
            print tag, self._contents[tag]

class Uoutline(Uelement) :
    
    def __init__(self, glif, element) :
        super(Uoutline,self).__init__(element)
        print ">>>> outline contents", element
        self.glif = glif
        self.components = []
        self.contours = []
        for tag in self._contents :
            if tag == "component" :
                for component in self._contents[tag] :
                    self.components.append( Ucomponent(self,component) )
            if tag == "contour" :
                for contour in self._contents[tag] :
                    self.contours.append( Ucontour(self,contour) )

    def removeobject(self,object,type) :
        super(Uoutline,self).remove(object.element)
        if type == "component" : self.component.remove(object)
        if type == "contour" : self.contours.remove(object)
    
    # If an element is removed, need to also remove object

class Ucomponent(Uelement) :
    
    def __init__(self, outline, element) :
        super(Ucomponent,self).__init__(element)
        print ">>>> component contents"
        for tag in self._contents :
            print tag, self._contents[tag]

class Ucontour(Uelement) :
    
    def __init__(self, outline, element) :
        super(Ucontour,self).__init__(element)
        self.UFO2anchor = None
        print ">>>> contour contents",element
        points = self._contents['point']
        # Identify UFO2-style anchor points
        if len(points) == 1 and "type" in points[0].attrib :
            if points[0].attrib["type"] == "move" :
                self.UFO2anchor = points[0].attrib
        
class Ulib(Uelement) :
    # For glif lib elements; top-level lib files use Uplist
    def __init__(self, glif, element) :
        super(Ulib,self).__init__(element)
        print ">>>> lib contents"
        for tag in self._contents :
            print tag, self._contents[tag]

def writeXMLobject(object, params, dirn, filen) :
    if object.outparams : params = object.outparams # override default params with object-specific ones
    indentFirst = params["indentFirst"]
    attribOrder = {}
    if object.type in params['attribOrders'] : attribOrder = params['attribOrders'][object.type]
    if object.type == "plist" :
        indentFirst = params["plistIndentFirst"]
        object.etree.doctype = 'plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"'
        if params["sortPlists"] : object.sort()

    etw = ETWriter(object.etree, attributeOrder = attribOrder, indentIncr = params["indentIncr"], indentFirst = indentFirst)
    etw.serialize_xml(object.write_to_xml)
    object.write_to_file(dirn,filen)
    
def getattrib(element,attrib) :
    if attrib in element.attrib :
        return element.attrib[attrib]
    else: return None
