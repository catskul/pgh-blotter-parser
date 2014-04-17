#-------------------------------------------------------------------------------
# Name:        Police Blotter
# Purpose:     Read and convert Pittsburgh Police Blotter pdf to text
#
# Author:      Andy Somerville
# Created:     01/04/2014
#
# Changed by:  Mark Howe
# Modified     04/16/2014
# Modifications: pdfminer didn't have process_pdf
#                used interpreter.process_page(page)
#                instead of process_pdf(rsrcmgr, device, fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True)
#                added argv for -i inputfile and -o outfile
#                hard coded (bad idea) path
# Copyright:   (c) Andy Somerville 2014
# Licence:     <MIT licensed (free to copy derive for any reason as long as the copyright info is preserved).>
#-------------------------------------------------------------------------------


import sys, getopt
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter, PDFConverter, LTContainer, LTText, LTTextBox, LTImage
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
#from pdfminer.pdfinterp import process_pdf

#def main():
#    pass
#if __name__ =='__main__':
#    main()

def coroutine(func):
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        cr.next()
        return cr
    return start

@coroutine
def doit():
    while True:
        line = (yield)
        print "HA: " + line


field_set = { 'Report Name',
              'Incident Time',
              'Location of Occurrence',
              'Neighborhood',
              'Incident',
              'Age',
              'Gender' }

multifield_set = {
              'Section',
              'Description' }



class BlotterProcessor:
    zone = ""
    date = ""

    @coroutine
    def processDocument(self):
    #     blotterFile = open( "blotter_tuesday.txt", 'r' )
        processContentCoro = self.processContent()

        while True:
            line = (yield)
            #process header
            if line:
                #line = line.strip()
                if line.startswith("PITTSBURGH BUREAU OF POLICE"):
                    print "passing> [" + line + "]"
                    continue
                elif line.startswith("Sorted by:"):
                    print "passing> [" + line + "]"
                    line = (yield)
                    continue
                elif line.startswith("DISCLAIMER"):
                    print "passing> [" + line + "]"
                    line = (yield)
                    print "passing>> [" + line + "]"
                    continue
    #             elif line.startswith("Incident Blotter"):
    #                 print "passing [" + line + "]"
    #                 continue
                elif line.startswith("Incident Blotter"):
                    line  = (yield)
                    self.date = line
                    continue

                elif ("Zone 1") in line :
        #             zone  = line.strip()
                    print "Pre zone-line: " + line
                    self.zone = (yield)
                    print "Zone line: " + self.zone
                    continue

            else:
                line = ""

            processContentCoro.send(line)

    @coroutine
    def processContent(self):
        line=""
        record={}

        while True:
            line = (yield)
            if not line:
#                 print "NOT LINE"
                continue
    #         print "received [" + line + "]"


            elif line in field_set :
                field = line.strip()
                record[field] = (yield)

            elif line in multifield_set:
                field = line.strip()
                record[field] = ""
                data = (yield)
                while True:
                    data = (yield)
                    if data == "":
                        break
                    record[field] += "\n\t[" + data + "]"

                if field == "Description":
                    sys.stdout.write("zone=%s\n"%(self.zone) )
                    sys.stdout.write("date=%s\n"%(self.date) )
                    for key in record:
                        sys.stdout.write("%s=%s\n"%(key,record[key]) )
                    print
                    print
                    record = {}


class TextLineConverter(PDFConverter):

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1, laparams=None,
                 showpageno=False, imagewriter=None):
        PDFConverter.__init__(self, rsrcmgr, outfp, codec=codec, pageno=pageno, laparams=laparams)
        self.showpageno = showpageno
        self.imagewriter = imagewriter
        self.blotterProcessor = BlotterProcessor()
        self.coro = self.blotterProcessor.processDocument()
        return

    line=""

    def write_text(self, text):
         self.outfp.write(text.encode(self.codec, 'ignore'))
         print "{" + text + "}"
         if text == "\n":
                     print "sending [" + self.line + "]"
                     self.coro.send(self.line)
                     self.line=""
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




def parsePdf(fname,outfile):

      password = ''
      pagenos = set()
      maxpages = 0
    # output option
    #outfile = "C:\\scripts\\"+outputfile
      print "[" + outfile + "]"
      outtype = 'text'
      layoutmode = 'normal'
      codec = 'utf-8'
      caching = True
      laparams = LAParams()

      rsrcmgr = PDFResourceManager(caching=caching)
      if not outtype:
        outtype = 'text'

      if outfile:
        outfp = file(outfile, 'w+')
      else:
        outfp = sys.stdout
      if outtype == 'text':
        device = TextLineConverter(rsrcmgr, outfp, codec=codec, laparams=laparams )
      else:
        return usage()

      fp = file(fname, 'rb')
      interpreter = PDFPageInterpreter(rsrcmgr, device)
      password = ""
      maxpages = 0
      caching = True
      pagenos=set()
      for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)
   # process_pdf(rsrcmgr, device, fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True)
      fp.close()

      device.close()
      outfp.close()
      return

class Usage(Exception):
    def __init__(self,msg):
        self.msg = msg

def main(argv):
    #if argv is None:
     #   argv=sys.argv
    try:
        try:
            inputfile = ''
            outputfile = ''
            pathname = 'C:\\scripts\\'

            opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])

            for opt, arg in opts:
             if opt == '-h':
              print 'PoliceBlotter.py -i <inputfile> -o <outputfile>'
              sys.exit()
             elif opt in ("-i", "--ifile"):
              inputfile = arg
             elif opt in ("-o", "--ofile"):
              outputfile = arg
            print 'Input file is ', inputfile
            print 'Output file is ', outputfile
            ifile = pathname + inputfile
            ofile = pathname + outputfile
            print 'ifile is ',ifile
            print 'ofile is ',ofile
            parsePdf(ifile,ofile)
        except getopt.GetoptError:
         print 'PoliceBlotter.py -i <inputfile> -o <outputfile>'
         sys.exit(2)
    except Usage, err:
      print >>sys.stderr, err.msg
      print >>sys.stderr, "for help use --help"
      return 2

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))





