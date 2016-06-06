import arcpy
from arcpy import env
import re
import csv

#0 Pre-Process

#Get input parameters
in_fc = arcpy.GetParameterAsText(1)
outDir = arcpy.GetParameterAsText(2)
outName = arcpy.GetParameterAsText(3)
template_fc = arcpy.GetParameterAsText(4)

#Initialize Variables
rowCount = 0
logEveryN = 100000
double_field_list = ["CNTASSDVALUE_DBL","LNDVALUE_DBL","IMPVALUE_DBL","FORESTVALUE_DBL","ESTFMKVALUE_DBL",
	"NETPRPTA_DBL","GRSPRPTA_DBL","ASSDACRES_DBL","DEEDACRES_DBL","GISACRES_DBL"]

#Create copy of feature class in memory
arcpy.AddMessage("WRITING TO MEMORY")
output_fc_temp = in_fc + "_WORKING"
arcpy.Delete_management("in_memory")
arcpy.FeatureClassToFeatureClass_conversion(in_fc,"in_memory",output_fc_temp)

#Add double fields for processing
arcpy.AddMessage("ADDING FIELDS")
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
arcpy.AddField_management(output_fc_temp,"NUM_CAST_FLAG", "TEXT", "", "", 50)

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
		for key, value in nameNoDict.iteritems():
			if key in schoolDistName:
				row.setValue("SCHOOLDISTNO", value)
		cursor.updateRow(row)
	else if schoolDistName is None:
		for key, value in noNameDict.iteritems():
			if key in schoolDistNo:
				row.setValue("SCHOOLDIST", value)
		cursor.updateRow(row)

#Numeric Value Cast
def numValCast(row,cursor, field_list):
	regexp = re.compile("[^0-9.]")
	for field in field_list:
		if "e" in row.getValue(field) or "E" in row.getValue(field):
			row.setValue(field + "_DBL", float(row.getValue(field)))
		else if regexp.search(word) is not None:
			row.setValue("NUM_CAST_FLAG",field)
		else:
			row.setValue(field + "_DBL", float(row.getValue(field)))

#Unusual AUXCLASS: Returns 1 if an unusual AUXCLASS is found, else 0 (for a running tally)
#Split field based on comma
#compare to accepted domains
#If no match is found, write unusual aux class to a csv or text file with the parcel's stateID

#EstFmkVal (save until end)

arcpy.AddMessage("PROCESSING ROWS")
updateCursor = arcpy.UpdateCursor(output_fc_temp)
for row in updateCursor:
	rowCount += 1
	calcStateid(row, updateCursor)
	processSchoolDist(row,updateCursor,schoolDist_nameNo_dict,schoolDist_noName_dict)
	numValCast(row, updateCursor,double_field_list)


	if (rowCount % logEveryN) == 0:
        arcpy.AddMessage("PROCESSED "+str(rowCount)+" RECORDS")
del(updateCursor)	


#2 Column operations

#Run summaries on certain fields

#I'm not sure if this will work.  I tried to use a list of fields as opposed to 
#hard coding the arcpy.Frequency... for each attribute field
def createSummarytables(in_fc,outDir,outName):
	fieldList = ["PREFIX","STREETNAME","STREETTYPE","SUFFIX"]
	for i in fieldList:
		arcpy.Frequency_analysis(in_fc,outDir +"/"+outName+i+"_Summary",i)
		
createSummarytables(in_fc,outDir,outName)

<<<<<<< HEAD

======
>>>>>>> origin/master
#3 Misc operations (could be in separate script)

#ROW/Hydro Standardization


#4 Post-Process

#Field map 
#Run a merge into the template schema
#Clear workspace