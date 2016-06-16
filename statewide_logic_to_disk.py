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
cs = arcpy.GetParameterAsText(3)
if not cs:
	cs = arcpy.env.outputCoordinateSystem

#Initialize Variables
rowCount = 0
logEveryN = 100000
string_field_list = ["CNTASSDVALUE","LNDVALUE","IMPVALUE","FORESTVALUE","ESTFMKVALUE",
	"NETPRPTA","GRSPRPTA","ASSDACRES","DEEDACRES","GISACRES"]
#THIS LIST NOT CURRENTLY BEING USED:
#double_field_list = ["CNTASSDVALUE_DBL","LNDVALUE_DBL","IMPVALUE_DBL","FORESTVALUE_DBL","ESTFMKVALUE_DBL",
#	"NETPRPTA_DBL","GRSPRPTA_DBL","ASSDACRES_DBL","DEEDACRES_DBL","GISACRES_DBL"]

#Create copy of feature class in memory
arcpy.AddMessage("WRITING TO DISK")
output_fc = os.path.join(outDir, outName)
auxClassTable = os.path.join(outDir,outName+"_unusualAuxClassTable")
arcpy.FeatureClassToFeatureClass_conversion(in_fc,outDir,outName)

#Add double fields for processing
arcpy.AddMessage("ADDING FIELDS")
arcpy.AddField_management(output_fc,"CNTASSDVALUE_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"LNDVALUE_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"IMPVALUE_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"FORESTVALUE_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"ESTFMKVALUE_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"NETPRPTA_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"GRSPRPTA_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"ASSDACRES_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"DEEDACRES_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"GISACRES_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"NUM_CAST_FLAG", "TEXT", "", "", 50)
arcpy.AddField_management(output_fc,"LONGITUDE", "DOUBLE")
arcpy.AddField_management(output_fc,"LATITUDE", "DOUBLE")

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
arcpy.CreateTable_management(outDir,outName+"_unusualAuxClassTable")
arcpy.AddField_management(auxClassTable,"STATEID", "TEXT", "", "", 100)
arcpy.AddField_management(auxClassTable,"UNAUXCLASS", "TEXT", "", "", 150)

#1 Row operations

#Clean Case and Trim (plus carriage returns)

#State ID
def calcStateid(row,cursor):
	if row.getValue("PARCELID") is None:
		row.setValue("STATEID", row.getValue("PARCELFIPS"))
		cursor.updateRow(row)
	elif row.getValue("PARCELFIPS") is None:
		arcpy.AddMessage("PARCEL FIPS Null "+ str(row.getValue("PARCELID")))
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
	stringValue = re.sub("[^0-9.]", "", str(row.getValue("IMPVALUE")))
	if stringValue is None or stringValue == "":
		row.setValue("IMPROVED", None)
	elif float(stringValue) <= 0:
		row.setValue("IMPROVED", "NO")
	elif float(stringValue) > 0:
		row.setValue("IMPROVED", "YES")
	cursor.updateRow(row)

#Numeric Value Cast
def numValCast(row,cursor,field_list):
	for field in field_list:
		stringValue = re.sub("[^0-9.]", "", str(row.getValue(field)))
		matchObj = re.search( r'[E|e][-+][0-9]*', str(row.getValue(field)), re.M|re.I)# regex to test if the value is in exponential notation (test here: http://bit.ly/1UhXD7z)
		if matchObj is not None:
			stringValue = str(row.getValue(field))
			#arcpy.AddMessage(matchObj.group())
		if row.getValue(field) is not None and stringValue != "":
			#elif regexp.search(word) is not None:
			#	row.setValue("NUM_CAST_FLAG",field)
			row.setValue(field + "_DBL", float(stringValue))
		cursor.updateRow(row)

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

def Update(field, value):
	if value:
		if not math.isnan(value):
			row[ucurFields.index(field)] = value
	
def writeLatLng():
	arcpy.AddMessage("Using the following CRS to construct Lat Longs: \n" + cs)
	fields = ["OBJECTID","LONGITUDE","LATITUDE"]	
	with arcpy.da.UpdateCursor(output_fc,fields + ["SHAPE@"],"",cs) as ucur:
		ucurFields = ucur.fields
		global ucurFields
		for row in ucur:
			global row
			geom = row[ucurFields.index("SHAPE@")]
			if geom:
				try:
					Update("LONGITUDE", geom.centroid.X)
					Update("LATITUDE", geom.centroid.Y)
				except:
					arcpy.AddMessage("FAILING LAT LONG CONSTRUCT ON OID: " + str(row[ucurFields.index("OBJECTID")]))
			ucur.updateRow(row)
		arcpy.SetProgressorPosition()

arcpy.AddMessage("PROCESSING ROWS")
updateCursor = arcpy.UpdateCursor(output_fc)

for row in updateCursor:
	rowCount += 1
	calcStateid(row, updateCursor)
	processSchoolDist(row,updateCursor,schoolDist_nameNo_dict,schoolDist_noName_dict)
	calcImproved(row, updateCursor)
	numValCast(row, updateCursor,string_field_list)
	#Unusual AUXCLASS
	cantThinkOfName(row,updateCursor,auxClassTable)
	if (rowCount % logEveryN) == 0:
		arcpy.AddMessage("PROCESSED "+str(rowCount)+" RECORDS")
del(updateCursor)

writeLatLng()	

#2 Column operations
arcpy.AddMessage("PROCESSING COLUMNS")
#Run summaries on certain fields
def createSummarytables(output_fc,outDir,outName):
	fieldList = ["PREFIX","STREETNAME","STREETTYPE","SUFFIX"]
	for i in fieldList:
		arcpy.Frequency_analysis(output_fc,outDir +"/"+outName+i+"_Summary",i)
		
#Case and trim		
def cleanCaseTrim(field,nullList,output_fc):
	query = '("' + field + '" IS NOT ' + "" + "NULL" + ')'
	cursor = arcpy.UpdateCursor(output_fc, query)
	
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
fieldList = arcpy.ListFields(output_fc)
for field in fieldList:
	if field.name != "OBJECTID" and field.name != "SHAPE" and field.name != "SHAPE_LENGTH" and field.name != "SHAPE_AREA": 
		if field.type == "String":
			cleanCaseTrim(field.name,nullArray,output_fc);

#3 Post-Process

#Field map 
#Run a merge into the template schema
#Clear workspace
createSummarytables(in_fc,outDir,outName)