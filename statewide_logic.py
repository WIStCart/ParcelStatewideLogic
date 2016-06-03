import arcpy
from arcpy import env
import re
import csv

#0 Pre-Process

#Get input parameters
#Create copy of feature class in memory?
#Add new fields for processing (dbls)

#Parse SchoolDist csv to create two lists
reader = csv.reader(open('school_district_codes.csv', 'r'))
schoolDist_nameNo_dict = {}
schoolDist_noName_dict = {}
for row in reader:
   k, v = row
   schoolDist_noName_dict[k] = v
   schoolDist_nameNo_dict[v] = k


#1 Row operations

#Clean Case and Trim (plus carriage returns)

#State ID

#SchoolDist
#If num is null and name is not, loop through names to find matching num
#Else If name is null and num is not, loop through nums to find matching name 

#Numeric Value Cast
#If field value in sci notation, run a convert function (might be challenging)
#Else if field contains anything chars that aren't number related, throw a flag
#Else place number in the appropriate double field

#Unusual AUXCLASS: Returns 1 if an unusual AUXCLASS is found, else 0 (for a running tally)
#Split field based on comma
#compare to accepted domains
#If no match is found, write unusual aux class to a csv or text file with the parcel's stateID

#EstFmkVal (save until end)
#


#2 Column operations

#Run summaries on certain fields


#3 Misc operations (could be in separate script)

#ROW/Hydro Standardization


#4 Post-Process

#Field map 
#Run a merge into the template schema
#Clear workspace

