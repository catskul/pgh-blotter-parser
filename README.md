pgh-blotter-parser
==================

Everyday via cronjob, the application uses python, pdfminer and custom parsing to convert the data here:

 * http://communitysafety.pittsburghpa.gov/Blotter.aspx

...into json. It then uses geopy to geocode the locations from google's geocoding API.
The resulting json is pulled in via javascript and combined with googlemapsv3 to show everything on a map.

 * http://ec2-54-86-57-40.compute-1.amazonaws.com:8000/
 * http://ec2-54-86-57-40.compute-1.amazonaws.com:8000/test2.html

The entire system is available here:

 * https://github.com/catskul/pgh-blotter-parser.git
