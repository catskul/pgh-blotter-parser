import sys
import getopt
from pdfminer.converter import XMLConverter, HTMLConverter, TextConverter, PDFConverter, LTContainer, LTText, LTTextBox, LTImage
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, process_pdf


def coroutine(func):
    def start(*args, **kwargs):
        cr = func(*args, **kwargs)
        cr.next()
        return cr
    return start


@coroutine
def doit():
    while True:
        line = (yield)
        print "HA: " + line


field_set = {'Report Name',
             'Incident Time',
             'Location of Occurrence',
             'Neighborhood',
             'Incident',
             'Age',
             'Gender'}

multifield_set = {
    'Section',
    'Description'}


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
                field = line.strip()
                record[field] = ""
                data = (yield)
                while True:
                    data = (yield)
                    if data == "":
                        break
                    record[field] += "\n\t[" + data + "]"

                if field == "Description":
                    sys.stdout.write("zone=%s\n" % (self.zone))
                    sys.stdout.write("date=%s\n" % (self.date))
                    for key in record:
                        sys.stdout.write("%s=%s\n" % (key, record[key]))
                    print
                    print
                    record = {}


class TextLineConverter(PDFConverter):

    def __init__(self, rsrcmgr, outfp, codec='utf-8', pageno=1, laparams=None,
                 showpageno=False, imagewriter=None):
        PDFConverter.__init__(
            self, rsrcmgr, outfp, codec=codec, pageno=pageno, laparams=laparams)
        self.showpageno = showpageno
        self.imagewriter = imagewriter
        self.blotterProcessor = BlotterProcessor()
        self.coro = self.blotterProcessor.processDocument()
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


def parsePdf(fname):

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
        device = TextLineConverter(
            rsrcmgr, outfp, codec=codec, laparams=laparams)
    else:
        return usage()

    fp = file(fname, 'rb')
    process_pdf(rsrcmgr, device, fp, pagenos, maxpages=maxpages,
                password=password, caching=caching, check_extractable=True)
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
#             processDocument()
            parsePdf("blotter_tuesday.pdf")

        except getopt.error, msg:
            raise Usage(msg)
        # more code, unchanged
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())
