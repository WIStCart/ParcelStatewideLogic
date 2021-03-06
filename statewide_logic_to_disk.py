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
string_field_list = ["CNTASSDVALUE","LNDVALUE","IMPVALUE","MFLVALUE","ESTFMKVALUE",
	"NETPRPTA","GRSPRPTA","ASSDACRES","DEEDACRES","GISACRES"]
string_field_alias_list = ["Total Assessed Value","Assessed Value of Land","Assessed Value of Improvements","Assessed Value of MFL/FCL Land","Estimated Fair Market Value",
	"Net Property Tax","Gross Property Tax","Assessed Acres","Deeded Acres","GIS Acres"]
double_field_list = ["CNTASSDVALUE_DBL","LNDVALUE_DBL","IMPVALUE_DBL","MFLVALUE_DBL","ESTFMKVALUE_DBL",
	"NETPRPTA_DBL","GRSPRPTA_DBL","ASSDACRES_DBL","DEEDACRES_DBL","GISACRES_DBL"]

#Create copy of feature class
arcpy.AddMessage("WRITING TO DISK")
output_fc = os.path.join(outDir, outName)
auxClassTable = os.path.join(outDir,outName+"_unusualAuxClassTable")
arcpy.FeatureClassToFeatureClass_conversion(in_fc,outDir,outName)

#Add double fields for processing
arcpy.AddMessage("ADDING FIELDS")
arcpy.AddField_management(output_fc,"CNTASSDVALUE_DBL", "DOUBLE","",2)
arcpy.AddField_management(output_fc,"LNDVALUE_DBL", "DOUBLE","",2)
arcpy.AddField_management(output_fc,"IMPVALUE_DBL", "DOUBLE","",2)
arcpy.AddField_management(output_fc,"MFLVALUE_DBL", "DOUBLE","",2)
arcpy.AddField_management(output_fc,"ESTFMKVALUE_DBL", "DOUBLE","",2)
arcpy.AddField_management(output_fc,"NETPRPTA_DBL", "DOUBLE","",2)
arcpy.AddField_management(output_fc,"GRSPRPTA_DBL", "DOUBLE","",2)
arcpy.AddField_management(output_fc,"ASSDACRES_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"DEEDACRES_DBL", "DOUBLE")
arcpy.AddField_management(output_fc,"GISACRES_DBL", "DOUBLE")
#arcpy.AddField_management(output_fc,"NUM_CAST_FLAG", "TEXT", "", "", 50) #doesn't look like we are using this
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
			row.setValue(field + "_DBL", round(float(stringValue),2))
		cursor.updateRow(row)

#Unusual AUXCLASS:
def unusualAuxClass(row,cursor):
	# domain w/exceptions from validation tool
	#auxClassDef = ['W1','W2','W3','W4','W5','W6','W7','W8','W9','X1','X2','X3','X4','X5','M','XTEL','S1', 'U', 'AWO', 'FM6', 'FM7', 'FM8', 'AW']
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

def taxrollForNewParcels(row,cursor):
	taxyearvalue = row.getValue("TAXROLLYEAR")
	if taxyearvalue == '2020' or taxyearvalue == '2021' :
		fieldList = ["CNTASSDVALUE_DBL","LNDVALUE_DBL","IMPVALUE_DBL","MFLVALUE_DBL","ESTFMKVALUE_DBL","NETPRPTA_DBL","GRSPRPTA_DBL","PROPCLASS","AUXCLASS","ASSDACRES_DBL"]
		for i in range(len(fieldList)):
			row.setValue(fieldList[i], None)
	cursor.updateRow(row)

def estfmkCorrection(row,cursor):
	propvalue = row.getValue("PROPCLASS")
	estvalue = row.getValue("ESTFMKVALUE_DBL")
	if estvalue is not None and propvalue is not None and (re.search('4', str(propvalue)) or re.search('5',str(propvalue))):
		#arcpy.AddMessage("propclass" + str(propvalue) )
		row.setValue("ESTFMKVALUE_DBL",None)
	cursor.updateRow(row)

def Update(field, value):
	if value:
		if not math.isnan(value):
			row[ucurFields.index(field)] = value

def writeLatLng():
	fields = ["OBJECTID","LONGITUDE","LATITUDE"]
	#Get field names for writing point FC
	schema_fields = [f.name for f in arcpy.ListFields(str(output_fc))]
	desc = arcpy.Describe(output_fc)
	for field in desc.fields:
		if field.name == 'Shape':
			schema_fields.remove(field.name)
		if field.editable == False:
			schema_fields.remove(field.name)
	sr = arcpy.SpatialReference(4326) # GCS_WGS_1984 WKID: 4326 Authority: EPSG - Use this to construct lat lng values in decimal degrees
	arcpy.AddMessage("\nUsing the following CRS to construct Lat Lng attributes: \n" + sr.name + "\n")
	# Was receiving a workspace conflict when nesting two arcpy.da cursors within one another, thus chose to perform two separate iterations (this is also beneficial of we want the CRS outputs to be different between the two)
	with arcpy.da.UpdateCursor(output_fc,fields + ["SHAPE@"],"",sr) as ucur:
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
					arcpy.AddMessage("FAILING LAT LNG ATTRIBUTE CONSTRUCT ON OID: " + str(row[ucurFields.index("OBJECTID")]))
			ucur.updateRow(row)
		arcpy.SetProgressorPosition()

	# Set variables for creating a parcel point layer
	out_path = outDir
	out_name = outName + "_points"
	geometry_type = "POINT"
	template = output_fc # the output polygon feature class is used as an attribute template (to copy the V2 schema into the point layer)
	has_m = "DISABLED"
	has_z = "DISABLED"

	# Use "Describe" to get a SpatialReference object of the output polygon feature class, then apply it to the point feature class.
	spatial_reference = arcpy.Describe(template).spatialReference
	arcpy.AddMessage("\nUsing the following CRS to construct a point file: \n" + spatial_reference.name + "\n")

	# Execute CreateFeatureclass in order to create the point layer
	arcpy.CreateFeatureclass_management(out_path, out_name, geometry_type, template, has_m, has_z, spatial_reference)

	# Create a search cursor for iterating parcels and an insert cursor for writing points to the point fc.
	point_fc = os.path.join(out_path, out_name)
	pt_cursor = arcpy.da.InsertCursor(point_fc, schema_fields + ["SHAPE@XY"])
	with arcpy.da.SearchCursor(output_fc,schema_fields + ["SHAPE@"] + ["OBJECTID"],"", spatial_reference) as ucur:
		ucurFields = ucur.fields
		for row in ucur:
			geom = row[ucurFields.index("SHAPE@")]
			if geom:
				try:
					#Get row values
					parcelRecordArray = list()
					for field in schema_fields:
						parcelRecordArray.append(row[ucurFields.index(field)])
					#Get point and insert new row
					xy = (geom.centroid.X, geom.centroid.Y)
					pt_cursor.insertRow(parcelRecordArray + [xy])
				except:
					arcpy.AddMessage("FAILING POINT CONSTRUCT ON OID: " + str(row[ucurFields.index("OBJECTID")]))
		arcpy.SetProgressorPosition()
		del(pt_cursor)



##  start processing rows
arcpy.AddMessage("PROCESSING ROWS")
updateCursor = arcpy.UpdateCursor(output_fc)

for row in updateCursor:
	rowCount += 1
	calcStateid(row, updateCursor)
	processSchoolDist(row,updateCursor,schoolDist_nameNo_dict,schoolDist_noName_dict)
	#calcImproved(row, updateCursor)
	numValCast(row, updateCursor,string_field_list)
	#Unusual AUXCLASS
	cantThinkOfName(row,updateCursor,auxClassTable)
	taxrollForNewParcels(row,updateCursor)
	estfmkCorrection(row,updateCursor)
	if (rowCount % logEveryN) == 0:
		arcpy.AddMessage("PROCESSED "+str(rowCount)+" RECORDS")
del(updateCursor)



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


##  start processing Columns
#null array
nullArray = ["<Null>", "<NULL>", "NULL", ""]

#Get fields in feature class and loop through them
fieldList = arcpy.ListFields(output_fc)
for field in fieldList:
	if field.name != "OBJECTID" and field.name != "SHAPE" and field.name != "SHAPE_LENGTH" and field.name != "SHAPE_AREA":
		if field.type == "String":
			cleanCaseTrim(field.name,nullArray,output_fc);


createSummarytables(output_fc,outDir,outName)
#3 Post-Process

#Delete String fields
arcpy.AddMessage("RENAMING FIELDS")
arcpy.DeleteField_management(output_fc, string_field_list)
#Rename double fields to schema names
for i in range(len(string_field_list)):
	arcpy.AlterField_management(output_fc,double_field_list[i] , string_field_list[i],
		string_field_alias_list[i])

#write lat lng to attribute fields, create point centroid file.
writeLatLng()
