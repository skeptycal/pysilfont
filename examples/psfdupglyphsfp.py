#!/usr/bin/env python3
'''Duplicates glyphs in a UFO based on a csv definition: source,target.
Duplicates everything except unicodes.
Mainly a demonstration of using the fontParts library.'''
__url__ = 'http://github.com/silnrsi/pysilfont'
__copyright__ = 'Copyright (c) 2018 SIL International (http://www.sil.org)'
__license__ = 'Released under the MIT License (http://opensource.org/licenses/MIT)'
__author__ = 'Victor Gaultney'

from silfont.core import execute
from fontParts.world import *

# Setting input - Note that for fontParts you specify filenames for 
# input and output rather than infont or outfont. This script writes
# changes back to the original font.
argspec = [
    ('ifont', {'help': 'Input font filename'}, {'type': 'filename'}),
    ('-i','--input',{'help': 'Input csv file'}, {'type': 'incsv', 'def': 'duplicates.csv'}),
    ('-l','--log',{'help': 'Set log file name'}, {'type': 'outfile', 'def': '_duplicates.log'})]

def doit(args) :
    font = OpenFont(args.ifont)
    logger = args.logger

    # Process duplicates csv file into a dictionary structure
    args.input.numfields = 2
    duplicates = {}
    for line in args.input :
        duplicates[line[0]] = line[1]

    # Iterate through dictionary (unsorted)
    for source, target in duplicates.items() :
        # Check if source glyph is in font
        if source in font.keys() :
            # Give warning if target is already in font, but overwrite anyway
            if target in font.keys() :
                logger.log("Warning: " + target + " already in font and will be replaced")
            sourceglyph = font[source]
            # Make a copy of source into a new glyph object
            newglyph = sourceglyph.copy()
            # Modify that glyph object
            newglyph.unicodes = []
            # Add the new glyph object to the font with name target
            font.__setitem__(target,newglyph)
            logger.log(source + " duplicated to " + target)
        else :
            logger.log("Warning: " + source + " not in font")
    
    # Write the changes to a font directly rather than returning an object
    font.save()

    return

# Note the use of None rather than "UFO" in this execute()
def cmd() : execute(None,doit,argspec)
if __name__ == "__main__": cmd()
