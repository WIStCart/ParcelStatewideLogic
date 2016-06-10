import arcpy
from arcpy import env
import re
import csv
import os

#0 Pre-Process

#Get input parameters
in_fc = arcpy.GetParameterAsText(0)
outDir = arcpy.GetParameterAsText(1)
outName = arcpy.GetParameterAsText(2)

#Initialize Variables
rowCount = 0
logEveryN = 100000
double_field_list = ["CNTASSDVALUE_DBL","LNDVALUE_DBL","IMPVALUE_DBL","FORESTVALUE_DBL","ESTFMKVALUE_DBL",
	"NETPRPTA_DBL","GRSPRPTA_DBL","ASSDACRES_DBL","DEEDACRES_DBL","GISACRES_DBL"]

#Create copy of feature class in memory
arcpy.AddMessage("WRITING TO MEMORY")
output_fc_temp = os.path.join("in_memory", "WORKING")
auxClassTable = os.path.join(outDir,"unusualAuxClassTable")
arcpy.AddMessage(output_fc_temp)
arcpy.Delete_management("in_memory")
dynamic_workspace = "in_memory"
arcpy.FeatureClassToFeatureClass_conversion(in_fc,dynamic_workspace,"WORKING")

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
reader = csv.reader(open(os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])),'school_district_codes.csv'), 'r'))
schoolDist_nameNo_dict = {}
schoolDist_noName_dict = {}
for row in reader:
   k, v = row
   schoolDist_noName_dict[k] = v
   schoolDist_nameNo_dict[v] = k
#Create a table for the unusual AUXCLASS
arcpy.AddMessage("CREATING AUXCLASS TABLE")
arcpy.CreateTable_management(outDir,"unusualAuxClassTable")
arcpy.AddField_management(auxClassTable,"STATEID", "TEXT", "", "", 100)
arcpy.AddField_management(auxClassTable,"UNAUXCLASS", "TEXT", "", "", 150)

#1 Row operations

#Clean Case and Trim (plus carriage returns)

#State ID
def calcStateid(row,cursor):
	parcelid = row.getValue("PARCELID")
	if parcelid == None:
	    row.setValue("STATEID", row.getValue("PARCELFIPS"))
	else:
		calculated = row.getValue("PARCELFIPS") + row.getValue("PARCELID")
		row.setValue("STATEID", calculated)
	cursor.updateRow(row)

#SchoolDist
def processSchoolDist(row,cursor,nameNoDict,noNameDict):
	schoolDistName = row.getValue("SCHOOLDIST")
	schoolDistNo = row.getValue("SCHOOLDISTNO")
	if schoolDistNo is None and schoolDistName is None:
		row.getValue("SCHOOLDISTNO")
	elif schoolDistNo is None:
		for key, value in nameNoDict.iteritems():
			if key in schoolDistName:
				row.setValue("SCHOOLDISTNO", value)
		cursor.updateRow(row)
	elif schoolDistName is None:
		for key, value in noNameDict.iteritems():
			if key in schoolDistNo:
				row.setValue("SCHOOLDIST", value)
		cursor.updateRow(row)

#Calculate Improved
def calcImproved(row,cursor):
	if row.getValue("IMPVALUE") is None:
		row.setValue("IMPROVED", None)
	elif int(row.getValue("IMPVALUE")) <= 0:
		row.setValue("IMPROVED", "NO")
	elif int(row.getValue("IMPVALUE")) > 0:
		row.setValue("IMPROVED", "YES")
	cursor.updateRow(row)

#Numeric Value Cast
def numValCast(row,cursor,field_list):
	regexp = re.compile("[^0-9.]")
	for field in field_list:
		if row.getValue(field) is not None:
			if "e" in row.getValue(field) or "E" in row.getValue(field):
				row.setValue(field + "_DBL", float(row.getValue(field)))
			elif regexp.search(word) is not None:
				row.setValue("NUM_CAST_FLAG",field)
			else:
				row.setValue(field + "_DBL", float(row.getValue(field)))

#Unusual AUXCLASS: 
def unusualAuxClass(row,cursor):
	auxClassDef = ["W1","W2","W3","W4","W5","W6","W7","W8","X1","X2","X3","X4"]
	auxClass = row.getValue("AUXCLASS")
	auxClass.replace(" ","")
	auxClassList = auxClass.split(",")
	unusualAuxClass = []
	for aClass in auxClassList:
		if not any(aClass in s for s in auxClassDef):
			unusualAuxClass.append(aClass)
	if len(unusualAuxClass) > 0:
		return ",".join(unusualAuxClass)
	else:
		return None

def cantThinkOfName(row,cursor,auxClassTable):		
	if row.getValue("AUXCLASS") is not None:
		auxClass = unusualAuxClass(row,updateCursor)
		if auxClass is not None:
			insertCursor = arcpy.InsertCursor(auxClassTable)
			inRow = insertCursor.newRow()
			inRow.setValue("STATEID",row.getValue("STATEID"))
			inRow.setValue("UNAUXCLASS",auxClass)
			insertCursor.insertRow(inRow)
			del(insertCursor)

arcpy.AddMessage("PROCESSING ROWS")
updateCursor = arcpy.UpdateCursor(output_fc_temp)

for row in updateCursor:
	rowCount += 1
	calcStateid(row, updateCursor)
	processSchoolDist(row,updateCursor,schoolDist_nameNo_dict,schoolDist_noName_dict)
	calcImproved(row, updateCursor)
	numValCast(row, updateCursor,double_field_list)
	#Unusual AUXCLASS
	cantThinkOfName(row,updateCursor,auxClassTable)
	if (rowCount % logEveryN) == 0:
		arcpy.AddMessage("PROCESSED "+str(rowCount)+" RECORDS")
del(updateCursor)
	

#2 Column operations
arcpy.AddMessage("PROCESSING COLUMNS")
#Run summaries on certain fields
def createSummarytables(output_fc_temp,outDir,outName):
	fieldList = ["PREFIX","STREETNAME","STREETTYPE","SUFFIX"]
	for i in fieldList:
		arcpy.Frequency_analysis(output_fc_temp,outDir +"/"+outName+i+"_Summary",i)
		
#Case and trim		
def cleanCaseTrim(field,nullList,output_fc_temp):
	query = '("' + field + '" IS NOT ' + "" + "NULL" + ')'
	cursor = arcpy.UpdateCursor(output_fc_temp, query)
	
	#Loop through each row in a given field
	for row in cursor:
		#Strip whitespace, uppercase alpha characters, remove carriage returns
		row.setValue(field, (row.getValue(field).strip().upper().strip('\r')))
		cursor.updateRow(row)
		#Check for null values
		count = 0
		found = False
		while (found == False) and (count < len(nullList)):
			if row.getValue(field) == nullList[count]:
				row.setValue(field, None)
				cursor.updateRow(row)
				found = True
			else:
				count += 1
					
#null array 
nullArray = ["<Null>", "<NULL>", "NULL", ""]

#Get fields in feature class and loop through them
fieldList = arcpy.ListFields(output_fc_temp)
for field in fieldList:
    if field.name != "OBJECTID" and field.name != "SHAPE" and field.name != "SHAPE_LENGTH" and field.name != "SHAPE_AREA": 
        if field.type == "String":
            cleanCaseTrim(field.name,nullArray,output_fc_temp);

#3 Post-Process

#Field map 
#Run a merge into the template schema
#Clear workspace
createSummarytables(in_fc,outDir,outName)

#3 Post-Process
#Return a feature class
arcpy.FeatureClassToFeatureClass_conversion(output_fc_temp, outDir, outName)
