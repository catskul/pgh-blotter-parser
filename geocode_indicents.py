#!/usr/bin/python
from __future__ import print_function
import geopy
import json
import os
import sys
import getopt
import time

def geocode_incidents(ifilename,ofilename):

    geocoder = geopy.geocoders.GoogleV3()
    geocoded_incident_file = open( ofilename + ".out", 'w' )
    geocoded_incident_file.write( "[" ) 
    
    incident_file          = open( ifilename )
    incidents = json.load( incident_file )
    
    for incident in incidents:
        try:
            if not "geocode" in incident and incident['Location of Occurrence'] != "" :
                query = incident['Location of Occurrence'] + "," + incident['Neighborhood']
                address, (lat, lng) = geocoder.geocode(query)
                incident['geocode'] = {
                    'address': address, 
                    'lat'    : lat, 
                    'lng'    : lng,
                    'query'  : query
                    }
                time.sleep(0.5)#delay to avoid maxing out geocode limit
                print( incident['geocode'], file=sys.stderr )
        except TypeError:
            print( "Type error in geocode of: %s"%incident, file=sys.stderr )
        geocoded_incident_file.write( str( incident ) )
   
    incident_file.close()
     
    geocoded_incident_file.write( "]" ) 
    geocoded_incident_file.close()
     
    os.rename( ofilename + ".out", ofilename )

class Usage(Exception):

    def __init__(self, msg):
            self.msg = msg

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hi:o:", ["ifile=", "ofile="])
            
            inputfile  = None
            outputfile = None
            for opt, arg in opts:
                if opt == '-h':
                    sys.stderr.write( '%s -i <inputfile> -o <outputfile>\n'%argv[0] )
                    sys.exit()
                elif opt in ("-i", "--ifile"):
                    inputfile = arg
                elif opt in ("-o", "--ofile"):
                    outputfile = arg
            
            if outputfile is None:
                outputfile = inputfile + ".out"
                    
            sys.stderr.write( 'Input file is %s\n'%inputfile   )
            sys.stderr.write( 'Output file is %s\n'%outputfile )          
                        
            geocode_incidents(inputfile,outputfile)

        except getopt.error, msg:
            raise Usage(msg)

    except Usage, err:
        sys.stderr.write( err.msg + "\n" )
        sys.stderr.write( "for help use --help" )
        return 2

if __name__ == "__main__":
    sys.exit(main())
