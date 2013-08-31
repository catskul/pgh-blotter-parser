import sys
import getopt
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter, PDFConverter, LTContainer, LTText, LTTextBox, LTImage
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, process_pdf


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
              'Location of Occurence',
              'Neighborhood',
              'Incident',
              'Age',
              'Gender' }

multifield_set = {
              'Section',
              'Description' }        
        

@coroutine
def grabAndFilter():
    line = (yield)
    if line.strip().startswith("PITTSBURGH BUREAU OF POLICE"):
        while not (yield).strip().startswith("DISCLAIMER"):
            print "passing"
            pass
        while (yield).strip() != "":
            print "passing"
            pass
    return line
        
@coroutine
def processBlotter():
#     blotterFile = open( "blotter_tuesday.txt", 'r' )
    line=""
    date=""
    zone=""
    record={}
    
    while True:
        line = (yield).strip()
        if not line:
#             print "NOT LINE"
            continue
#         print "received [" + line + "]"
        

            
        if line.startswith("Zone"):
#             zone  = line.strip()
            zone = (yield).strip()
            
        elif line.startswith("Incident Blotter"):
            line  = (yield).strip()
            date = line
            
        elif line in field_set :
            field = line.strip()
            record[field] = (yield)
            
        elif line in multifield_set:
            field = line.strip()
            record[field] = ""    
            data = (yield).strip()
            while True:
                data = (yield).strip()
                if data == "":
                    break
                record[field] += "\n[" + data + "]"    
            
            if field == "Description":
                sys.stdout.write("zone=%s\n"%(zone) )    
                sys.stdout.write("date=%s\n"%(date) )    
                for key in record:
                    sys.stdout.write("%s=%s\n"%(key,record[key]) )
                print
                record = {}


class TextLineConverter(PDFConverter):

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1, laparams=None,
                 showpageno=False, imagewriter=None):
        PDFConverter.__init__(self, rsrcmgr, outfp, codec=codec, pageno=pageno, laparams=laparams)
        self.showpageno = showpageno
        self.imagewriter = imagewriter
        self.coro = processBlotter()
        return

    line=""

    def write_text(self, text):
#         self.outfp.write(text.encode(self.codec, 'ignore'))
#         print "{" + text + "}"
        if text == "\n":
#             print "sending [" + self.line + "]"
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


def parsePdf( fname ):

    password = ''
    pagenos = set()
    maxpages = 0
    # output option
    outfile = None
    outtype = None
    layoutmode = 'normal'
    codec = 'utf-8'
    caching = True
    laparams = LAParams()

    rsrcmgr = PDFResourceManager(caching=caching)
    if not outtype:
        outtype = 'text'

    if outfile:
        outfp = file(outfile, 'w')
    else:
        outfp = sys.stdout
    if outtype == 'text':
        device = TextLineConverter(rsrcmgr, outfp, codec=codec, laparams=laparams )
    else:
        return usage()
    
    fp = file(fname, 'rb')
    process_pdf(rsrcmgr, device, fp, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True)
    fp.close()
  
    device.close()
    outfp.close()
    return


        


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "h", ["help"])
#             processBlotter()
            parsePdf( "blotter_tuesday.pdf" )
            
        except getopt.error, msg:
             raise Usage(msg)
        # more code, unchanged
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())
