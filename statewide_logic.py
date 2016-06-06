import arcpy
from arcpy import env
import re
import csv

#first commit of python file 20160603

#0 Pre-Process

#Get input parameters
in_fc = arcpy.GetParameterAsText(1)
outDir = arcpy.GetParameterAsText(2)
outName = arcpy.GetParameterAsText(3)

#Create copy of feature class in memory
arcpy.AddMessage("WRITING TO MEMORY")
output_fc_temp = in_fc + "_WORKING"
arcpy.Delete_management("in_memory")
arcpy.FeatureClassToFeatureClass_conversion(in_fc,"in_memory",output_fc_temp)

#Add double fields for processing
arcpy.AddMessage("ADDING DOUBLE FIELDS")
arcpy.AddField_management(output_fc_temp,"CNTASSDVALUE_DBL", "DOUBLE")
arcpy.AddField_management(output_fc_temp,"LNDVALUE_DBL", "DOUBLE")
arcpy.AddField_management(output_fc_temp,"IMPVALUE_DBL", "DOUBLE")
arcpy.AddField_management(output_fc_temp,"FORESTVALUE_DBL", "DOUBLE")
arcpy.AddField_management(output_fc_temp,"ESTFMKVALUE_DBL", "DOUBLE")
arcpy.AddField_management(output_fc_temp,"NETPRPTA_DBL", "DOUBLE")
arcpy.AddField_management(output_fc_temp,"GRSPRPTA_DBL", "DOUBLE")
arcpy.AddField_management(output_fc_temp,"ASSDACRES_DBL", "DOUBLE")
arcpy.AddField_management(output_fc_temp,"DEEDACRES_DBL", "DOUBLE")
arcpy.AddField_management(output_fc_temp,"GISACRES_DBL", "DOUBLE")

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
def calcStateid(row,cursor):
	if row.getValue("PARCELID") == None:
	    row.setValue("STATEID", row.getValue("PARCELFIPS"))
	else:
		calculated = row.getValue("PARCELFIPS") + row.getValue("PARCELID")
		row.setValue("STATEID", calculated)
	cursor.updateRow(row)

#SchoolDist
def processSchoolDist(row,cursor,nameNoDict,noNameDict):
	schoolDistName = row.getValue("SCHOOLDIST")
	schoolDistNo = row.getValue("SCHOOLDISTNO")

	if schoolDistNo is None:
		for key, value in d.iteritems():
	else if schoolDistName is None:



#Numeric Value Cast
#If field value in sci notation, run a convert function (might be challenging)
#Else if field contains anything chars that aren't number related, throw a flag
#Else place number in the appropriate double field

#Unusual AUXCLASS: Returns 1 if an unusual AUXCLASS is found, else 0 (for a running tally)
#Split field based on comma
#compare to accepted domains
#If no match is found, write unusual aux class to a csv or text file with the parcel's stateID

#EstFmkVal (save until end)


updateCursor = arcpy.UpdateCursor(output_fc_temp)
for row in updateCursor:
	calcStateid(row, updateCursor)
	processSchoolDist(row,updateCursor,schoolDist_nameNo_dict,schoolDist_noName_dict)
	



#2 Column operations

#Run summaries on certain fields


#3 Misc operations (could be in separate script)

#ROW/Hydro Standardization


#4 Post-Process

#Field map 
#Run a merge into the template schema
#Clear workspace