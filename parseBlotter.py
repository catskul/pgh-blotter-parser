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
    'Gender'}

multifield_set = {
    'Section',
    'Description'}
    
discard_set = {
    'PITTSBURGH BUREAU OF POLICE',
    'Sorted by:',
    'DISCLAIMER', }
    
terminal_field = "Description"
               
               


class BlotterProcessor:
    zone = ""
    date = ""

    @coroutine
    def processDocument(self):
    #     blotterFile = open( "blotter_tuesday.txt", 'r' )
        processContentCoro = self.processContent()

        while True:
            line = (yield)
            # process header
            if line:
                line = line.strip()
                if line.startswith("PITTSBURGH BUREAU OF POLICE"):
                    print "passing [" + line + "]"
                    continue
                elif line.startswith("Sorted by:"):
                    print "passing [" + line + "]"
                    line = (yield)
                    continue
                elif line.startswith("DISCLAIMER"):
                    print "passing [" + line + "]"
                    line = (yield)
                    print "passing [" + line + "]"
                    continue
    #             elif line.startswith("Incident Blotter"):
    #                 print "passing [" + line + "]"
    #                 continue
                elif line.startswith("Incident Blotter"):
                    line = (yield)
                    self.date = line

                elif line.startswith("Zone"):
        #             zone  = line.strip()
                    print "Pre zone-line: " + line
                    self.zone = (yield)
                    print "Zone line: " + self.zone

            else:
                line = ""

            processContentCoro.send(line)

    @coroutine
    def processContent(self):
        line = ""
        record = {}
        storeDataCoro = self.storeData()

        while True:
            line = (yield)
            if not line:
#                 print "NOT LINE"
                continue
    #         print "received [" + line + "]"

            elif line in field_set:
                field = line.strip()
                record[field] = (yield)

            elif line in multifield_set:
                field         = line.strip()
                record[field] = []
                data          = (yield)
                while True:
                    data = (yield)
                    if data == "":
                        break
                    record[field].append( data )

                if field == terminal_field:                   
                    record['zone'] = self.zone
                    record['date'] = self.date                    
                    storeDataCoro.send(record)
                    record = {}
                    
    @coroutine
    def storeData(self):
        import json
        while True:
            record = (yield)
            print
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
