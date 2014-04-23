#!/usr/bin/python
import urllib
import os
import sys
import getopt
import parse_blotter
import geocode_incidents
import datetime
from datetime import timedelta

days = [ 'monday',
         'tuesday',
         'wednesday',
         'thursday',
         'friday',
         'saturday',
         'sunday',
         ]

def pull_and_parse(offset,pdf_dir,json_dir):
    yesterday = (datetime.datetime.now() + timedelta(days=int(offset)))
    yesterday_name = yesterday.strftime('%A').lower()
    yesterday_str  = yesterday.strftime("%Y%m%d")

    blotter_filename = "blotter_%s.pdf"%yesterday_name
    blotter_url      = "http://www.city.pittsburgh.pa.us/police/blotter/%s"%blotter_filename

    blotter_basename = "blotter_%s_%s"%(yesterday_name,yesterday_str)
    pdf_path  = os.path.join( pdf_dir, "%s.pdf"%blotter_basename )
    json_path = os.path.join( json_dir, "%s.json"%blotter_basename )

    sys.stderr.write( '\n' )
    sys.stderr.write( "Downloading: [%s]\n"%blotter_url )
    sys.stderr.write( "...to [%s]\n"%json_path )
    
    urllib.urlretrieve(blotter_url, filename=pdf_path)
    parse_blotter.parsePdf(pdf_path,json_path)
    geocode_incidents.geocode_incidents(json_path,json_path)


class Usage(Exception):

    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "ad:r:i:o:", ["--all","--day-offset", "--range","--pdf-dir","--json-dir"])
            day_offset = -1
            num_days   =  1
            pdf_dir    = "./pdf"
            json_dir   = "./json"
                   
            for opt, arg in opts:
                if opt == '-h':
                    sys.stderr.writeline( '%s [--day-offset offset from today=%s] [--all] [--pdf-dir=%s] [--json-dir=%s]'%(argv[0],day_offset,pdf_dir,json_dir) )
                    sys.exit()
                    
                if opt == '-a':
                    num_days = 7
                    
                if opt == '-r':
                    num_days = int(arg)

                if opt == '-d':
                    day_offset = int(arg)

                if opt == '-i':
                    pdf_dir = arg

                if opt == '-o':
                    json_dir = arg

            sys.stderr.write( 'using offset: %s\n'    %day_offset )
            sys.stderr.write( 'pulling %s days\n'     %num_days   )
            sys.stderr.write( 'storing pdfs in %s\n'  %pdf_dir    )
            sys.stderr.write( 'putting output in %s\n'%json_dir   )
            
            if not os.path.exists(pdf_dir):
                os.makedirs(pdf_dir)
                
            if not os.path.exists(json_dir):
                os.makedirs(json_dir)                            
            
            for offset in range(day_offset,day_offset-num_days,-1):
                pull_and_parse(offset,pdf_dir,json_dir)
                print                        

        except getopt.error, msg:
            raise Usage(msg)

    except Usage, err:
        sys.stderr.write( err.msg + '\n' )
        sys.stderr.write( "for help use --help\n" )
        return 2

if __name__ == "__main__":
    sys.exit(main())
