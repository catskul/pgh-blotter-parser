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

    blotter_filename = "arrest_blotter_%s.pdf"%yesterday_name
    #blotter_url      = "http://www.city.pittsburgh.pa.us/police/blotter/%s"%blotter_filename
    blotter_url      = "http://apps.pittsburghpa.gov/police/arrest_blotter/%s"%blotter_filename

    #blotter_basename = "blotter_%s_%s"%(yesterday_name,yesterday_str)
    blotter_basename = "%s"%(yesterday_str)
    pdf_path  = os.path.join( pdf_dir, "%s.pdf"%blotter_basename )
    json_path = os.path.join( json_dir, "%s.json"%blotter_basename )

    sys.stderr.write( '\n' )
    sys.stderr.write( "Downloading: [%s]\n"%blotter_url )
    sys.stderr.write( "...to [%s]\n"%pdf_path )
    sys.stderr.write( "and converting into to [%s]\n"%json_path )
    
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
            opts, args = getopt.getopt(argv[1:], "had:r:i:o:", ["help","all","day-offset=", "range=","pdf-dir=","json-dir="])
            day_offset = -1
            num_days   =  1
            pdf_dir    = "./pdf"
            json_dir   = "./json"
                   
            for opt, arg in opts:
                if opt in ('-h', '--help'):
                    sys.stderr.write( '%s [--day-offset(offset from today)=%s] [--all] [--pdf-dir=%s] [--json-dir=%s]\n'%(argv[0],day_offset,pdf_dir,json_dir) )
                    sys.exit()
                    
                if opt in ('-a', '--all'):
                    num_days = 7
                    
                if opt in ('-r', '--range'):
                    num_days = int(arg)

                if opt in ('-d', '--day-offset'):
                    day_offset = int(arg)

                if opt in ('-i', '--pdf-dir'):
                    pdf_dir = arg

                if opt in ('-o', '--json-dir'):
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
        sys.stderr.write( "error: %s\n"%(err.msg) )
        sys.stderr.write( "for help use --help\n" )
        return 2

if __name__ == "__main__":
    sys.exit(main())
