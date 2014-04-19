#!/usr/bin/python
#-------------------------------------------------------------------------------
# Name:        Police Blotter
# Purpose:     Read and convert Pittsburgh Police Blotter pdf to text
#
# Authors:      Andy Somerville, Mark Howe
# Created:     01/04/2014
#
# License:
# The MIT License (MIT)
# 
# Copyright (c) 2014 Andy Somerville, Mark Howe
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#-------------------------------------------------------------------------

import sys
import getopt

from pdfminer.converter import TextConverter 
from pdfminer.converter import PDFConverter 
from pdfminer.converter import LTContainer
from pdfminer.converter import LTText
from pdfminer.converter import LTTextBox 
from pdfminer.converter import LTImage
from pdfminer.layout    import LAParams
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import process_pdf


def coroutine(func):
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        cr.next()
        return cr
    return start


field_set = {
    'Report Name',
    'Incident Time',
    'Location of Occurrence',
    'Neighborhood',
    'Incident',
    'Age',
    'Gender'
    }

multifield_set = {
    'Section',
    'Description'
    }
    
discard_set = {
    'PITTSBURGH BUREAU OF POLICE' : 1,
    'Sorted by:' : 2,
    'DISCLAIMER' : 2,
    'Page' : 2,
    }
    
class DiscardFound(Exception):
    pass

    
terminal_field = "Description"
               
persistent_field_dict = {
    'Zone'             : 'zone',
    'Incident Blotter' : 'date', }
                   


class BlotterProcessor:
    persistent_fields = {}

    @coroutine
    def processDocument(self):
    #     blotterFile = open( "blotter_tuesday.txt", 'r' )
        processContentCoro = self.processLine()

        while True:
            line = (yield)
            # process header
            if line:
                line = line.strip()
                
                try:
                    for discard_string in discard_set:
                        if line.startswith( discard_string ):
                            print "discarding [" + line + "]"
                        
                            for x in range(1,discard_set[discard_string]):
                                line = (yield)
                                print "discarding [" + line + "]"
                            
                            raise DiscardFound() # have to use this because breaking out
                                                 # functions is hard in coroutines
                    for key in persistent_field_dict:
                        if line.startswith( key ):
                            line = (yield)
                            self.persistent_fields[persistent_field_dict[key]] = line
                            
                            raise DiscardFound()

                except DiscardFound, e:
                    continue                    
            else:
                line = ""

            print "passing line: ", line
            processContentCoro.send(line)

    @coroutine
    def processLine(self):
        line   = ""
        record = {}
        last_record    = None
        empty_fields   = []
        parse_failures = []
        storeDataCoro = self.storeData()

        while True:
            line  = (yield)
            field = ""
            if not line:
                print "NOT LINE"
                continue
    #         print "received [" + line + "]"

            elif line in field_set:
                field = line.strip()
                print "found field: [%s]"%field                
                record[field] = ""
                line = (yield)
                while line != "":
                    record[field] += line  
                    print "storing: [%s]"%line           
                    line = (yield)

            elif line in multifield_set:
                field         = line.strip()
                print "found field: [%s]"%field
                record[field] = []
                line          = (yield) # consume empty line
                print "consuming empty line: [%s]"%line
                while True:
                    line = (yield)
                    print "storing: [%s]"%line
                    if line == "":
                        break
                    record[field].append( line )
            else:
                print "Failed to parse: [%s]"%line
                parse_failures.append( line )
                while True:
                    line = (yield)
                    print "Failed to parse: [%s]"%line
                    if line == "":
                        print parse_failures[-1]
                        break
                    if not isinstance(parse_failures[-1],list):
                        parse_failures[-1] = [ parse_failures[-1], ]
                    else:
                        parse_failures[-1].append(line)
                continue
                

            if record[field] == "":
                empty_fields.append( field )
                
            if field == terminal_field:                   
                record['zone'] = self.persistent_fields['zone']
                record['date'] = self.persistent_fields['date']                
                storeDataCoro.send((record,empty_fields,parse_failures))
                last_record  = record
                record       = {}
                empty_fields = []
                parse_failures = []
                
    @coroutine
    def storeField(self):
        
                    
    @coroutine
    def storeData(self):
        import json
        last_record       = None
        empty_fields      = None
        last_empty_fields = None
        parse_failures    = None
        while True:
            record, empty_fields, parse_failures = (yield)
            if parse_failures and empty_fields and len( parse_failures ) != 0 and len( empty_fields ) != 0:
                print "Attempting to fix empty record fields: [%s]\n with parse failures: [%s]"%(empty_fields,parse_failures)
                idx = 0
                for field in empty_fields:
                    print "Treating field [%s]"%(field)
                    if idx < len( parse_failures ):
                        if field == "Age" and len( parse_failures[idx] ) > 2 :
                            continue
                        if field == "Gender" and len( parse_failures[idx] ) > 1 :
                            continue
                        
                        record[field] = parse_failures[idx]
                        print "attaching to %s parse failures %s"%(field,parse_failures[idx])
                        idx += 1
                
            print record
            print json.dumps(record, sort_keys=True, indent=4, separators=(',', ': '))



class TextLineConverter(PDFConverter):

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1, laparams=None, showpageno=False, imagewriter=None):
        PDFConverter.__init__(self, rsrcmgr, outfp, codec=codec, pageno=pageno, laparams=laparams)
        self.showpageno       = showpageno
        self.imagewriter      = imagewriter
        self.blotterProcessor = BlotterProcessor()
        self.coro             = self.blotterProcessor.processDocument()
        return

    line = ""

    def write_text(self, text):
#         self.outfp.write(text.encode(self.codec, 'ignore'))
#         print "{" + text + "}"
        if text == "\n":
#             print "sending [" + self.line + "]"
            self.coro.send(self.line)
            self.line = ""
        else:
            self.line += text
        return

    def receive_layout(self, ltpage):
        def render(item):
            if isinstance(item, LTContainer):
                for child in item:
                    render(child)
            elif isinstance(item, LTText):
                self.write_text(item.get_text())
            if isinstance(item, LTTextBox):
                self.write_text('\n')
            elif isinstance(item, LTImage):
                if self.imagewriter is not None:
                    self.imagewriter.export_image(item)
        if self.showpageno:
            self.write_text('Page %s\n' % ltpage.pageid)
        render(ltpage)
        self.write_text('\f')
        return

    def render_image(self, name, stream):
        return

    def paint_path(self, gstate, stroke, fill, evenodd, path):
        return


def parsePdf(ifilename,ofilename):

    password   = ''
    pagenos    = set()
    maxpages   = 0
    outtype    = None
    layoutmode = 'normal'
    codec      = 'utf-8'
    caching    = True
    laparams   = LAParams()

    resourceManager = PDFResourceManager(caching=caching)

    if ofilename:
        outfile = file(ofilename, 'w')
    else:
        outfile = sys.stdout
        
    if not outtype:
        outtype = 'text'
        
    if outtype == 'text':
        device = TextLineConverter(resourceManager, 
                                   outfile, 
                                   codec=codec, 
                                   laparams=laparams)
    else:
        return usage()

    inputfile = file(ifilename, 'rb')
    process_pdf(resourceManager, 
                device, 
                inputfile, 
                pagenos, 
                maxpages=maxpages,
                password=password, 
                caching=caching, 
                check_extractable=True)
    inputfile.close()

    device.close()
    outfile.close()
    return


class Usage(Exception):

    def __init__(self, msg):
        self.msg = msg


def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            print argv
            opts, args = getopt.getopt(argv[1:], "hi:o:", ["ifile=", "ofile="])
            print opts, args
            
            inputfile  = None
            outputfile = None
            for opt, arg in opts:
                print opt, arg
                if opt == '-h':
                    print '%s -i <inputfile> -o <outputfile>'%argv[0]
                    sys.exit()
                elif opt in ("-i", "--ifile"):
                    inputfile = arg
                elif opt in ("-o", "--ofile"):
                    outputfile = arg
            print 'Input file is "', inputfile
            print 'Output file is "', outputfile            
                        
            parsePdf(inputfile,outputfile)

        except getopt.error, msg:
            raise Usage(msg)

    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())
