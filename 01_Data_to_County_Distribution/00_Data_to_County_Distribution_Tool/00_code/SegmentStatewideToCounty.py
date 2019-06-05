import os
import sys
import arcpy
import zipfile
from arcpy import env
from boxsdk import OAuth2
from boxsdk import Client
from boxsdk.exception import BoxAPIException

in_version_str = arcpy.GetParameterAsText(0)
input_dir = arcpy.GetParameterAsText(1)
input_fc = arcpy.GetParameterAsText(2)
phase_1 = arcpy.GetParameterAsText(3)
boxDir = arcpy.GetParameterAsText(4)
csvOut = arcpy.GetParameterAsText(5)
arcpy.AddMessage(phase_1)
# We need the following to do stuff with the box API, this can be created here: http://developers.box.com (https://uwmadison.app.box.com/developers/console/app/269462) ... to create a "Box application" ... the below specs are created by my UW madison account (csee@wisc.edu)
# A Box client ID for a Box application = 1wx8igxhzvoxnd3kup3c5mqlf92698du
# The corresponding Box client secret = ad9oTBoaerU6roD7PkcrFdCX2NuWNcx4
# A valid developer token for that application = UOruFNZV6AEbwTZXrfCBfUuvRbOmVHK2
# Api Key = 1wx8igxhzvoxnd3kup3c5mqlf92698du
if phase_1 == "true":
	arcpy.AddMessage("EXECUTING ***PHASE 1**** this is the phase where we create the GDBs and SHPs and zip em up.")
else:
	arcpy.AddMessage("EXECUTING ***PHASE 2**** THIS IS THE PART WHERE WE UPLOAD THINGS TO BOX AND MAKE NOTE OF THEIR SHARABLE LINK.")
	oauth = OAuth2(
	  client_id='1wx8igxhzvoxnd3kup3c5mqlf92698du',
	  client_secret='ad9oTBoaerU6roD7PkcrFdCX2NuWNcx4',
	  access_token='9VEMKZqY6NYAGxs10ifhf2ru0lXZoVyV' # Note, this token will expire within about an hour of it's creation - it appears there are sophisticated ways of not having to recreate this, but in lieu of that... the token should be created again @ https://uwmadison.app.box.com/developers/services/edit/269462
	)
	client = Client(oauth)
	#folder_to_use = client.folder(folder_id='V500_by_County_TEST')
	#results = client.search(boxDir, 2, 0)
	#matching_results = (r for r in results if r.id)
	#for m in matching_results:
	#	arcpy.AddMessage("Good news, we've got a Box folder...")
	#	arcpy.AddMessage(m.name)
		#arcpy.AddMessage(m.created_at)
	#	arcpy.AddMessage(m.id)
	#	folder_to_use = m.id
	#	break
	#else:
	#	arcpy.AddMessage('No Box folder match found, double check --> client.search(... line of code')

	root_folder = client.folder(folder_id= 'V500_by_County_TEST')
	#arcpy.AddMessage(root_folder)

# FULL STATE
countyArray = ["ADAMS","ASHLAND","BARRON","BAYFIELD","BROWN","BUFFALO","BURNETT","CALUMET","CHIPPEWA","CLARK","COLUMBIA","CRAWFORD","DANE","DODGE","DOOR","DOUGLAS","DUNN","EAU CLAIRE","FLORENCE","FOND DU LAC","FOREST","GRANT","GREEN","GREEN LAKE","IOWA","IRON","JACKSON","JEFFERSON","JUNEAU","KENOSHA","KEWAUNEE","LA CROSSE","LAFAYETTE","LANGLADE","LINCOLN","MANITOWOC","MARATHON","MARINETTE","MARQUETTE","MENOMINEE","MILWAUKEE","MONROE","OCONTO","ONEIDA","OUTAGAMIE","OZAUKEE","PEPIN","PIERCE","POLK","PORTAGE","PRICE","RACINE","RICHLAND","ROCK","RUSK","SAUK","SAWYER","SHAWANO","SHEBOYGAN","ST CROIX","TAYLOR","TREMPEALEAU","VERNON","VILAS","WALWORTH","WASHBURN","WASHINGTON","WAUKESHA","WAUPACA","WAUSHARA","WINNEBAGO","WOOD"]
arcpy.AddMessage('About to process ' + str(len(countyArray)) + ' counties.')

# FULL STATE BACKUP!!!
#countyArray = ["ADAMS","ASHLAND","BARRON","BAYFIELD","BROWN","BUFFALO","BURNETT","CALUMET","CHIPPEWA","CLARK","COLUMBIA","CRAWFORD","DANE","DODGE","DOOR","DOUGLAS","DUNN","EAU CLAIRE","FLORENCE","FOND DU LAC","FOREST","GRANT","GREEN","GREEN LAKE","IOWA","IRON","JACKSON","JEFFERSON","JUNEAU","KENOSHA","KEWAUNEE","LA CROSSE","LAFAYETTE","LANGLADE","LINCOLN","MANITOWOC","MARATHON","MARINETTE","MARQUETTE","MENOMINEE","MILWAUKEE","MONROE","OCONTO","ONEIDA","OUTAGAMIE","OZAUKEE","PEPIN","PIERCE","POLK","PORTAGE","PRICE","RACINE","RICHLAND","ROCK","RUSK","SAUK","SAWYER","SHAWANO","SHEBOYGAN","ST CROIX","TAYLOR","TREMPEALEAU","VERNON","VILAS","WALWORTH","WASHBURN","WASHINGTON","WAUKESHA","WAUPACA","WAUSHARA","WINNEBAGO","WOOD"]

def zip(src, dst):
	zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
	abs_src = os.path.abspath(src)
	for dirname, subdirs, files in os.walk(src):
		for filename in files:
			absname = os.path.abspath(os.path.join(dirname, filename))
			arcname = absname[len(abs_src) + 1:]
			print 'zipping %s as %s' % (os.path.join(dirname, filename),
										arcname)
			zf.write(absname, arcname)
	zf.close()

def exportZipUploadLink(in_str):
	if phase_1 == "true":
		in_str2 = in_str.replace(".", "")
		out_str = in_str2.replace(" ", "_")
		out_version_str = in_version_str + out_str

		arcpy.CreateFolder_management(input_dir, out_version_str)
		arcpy.CreateFolder_management(input_dir +"\\"+ out_version_str , out_version_str + "_GDB")
		arcpy.CreateFolder_management(input_dir +"\\"+ out_version_str , out_version_str + "_SHP")

		# Set local variables
		out_folder_path_GDB = input_dir +"\\"+ out_version_str +"\\"+ out_version_str + "_GDB"
		out_folder_path_SHP = input_dir +"\\"+ out_version_str +"\\"+ out_version_str + "_SHP"
		out_name = out_version_str +".gdb"

		# Execute CreateFileGDB
		arcpy.CreateFileGDB_management(out_folder_path_GDB, out_name, "CURRENT")
		 
		# Set local variables
		inFeatures = input_fc
		outLocationGDB = out_folder_path_GDB +"\\"+ out_version_str +".gdb"
		outLocationSHP = out_folder_path_SHP
		outFeatureClass = out_version_str
		delimitedField = "CONAME"
		expression = delimitedField + " = '"+ in_str +"'"
		# Execute FeatureClassToFeatureClass
		arcpy.FeatureClassToFeatureClass_conversion(inFeatures, outLocationGDB, outFeatureClass, expression)
		outLocation = input_dir +"\\"+ out_version_str +"\\"+ out_version_str
		arcpy.FeatureClassToFeatureClass_conversion(inFeatures, outLocationSHP, outFeatureClass, expression)

		zip(out_folder_path_SHP, out_folder_path_SHP)
		zip(out_folder_path_GDB, out_folder_path_GDB)
	else:
		in_str2 = in_str.replace(".", "")
		out_str = in_str2.replace(" ", "_")
		out_version_str = in_version_str + out_str
		out_folder_path_GDB = input_dir +"\\"+ out_version_str +"\\"+ out_version_str + "_GDB"
		out_folder_path_SHP = input_dir +"\\"+ out_version_str +"\\"+ out_version_str + "_SHP"
		
		uploaded_file = root_folder.upload(out_folder_path_GDB + '.zip')
		download_url = uploaded_file.get_shared_link_download_url()
		arcpy.AddMessage(download_url)
		myCsvRow =  in_str + "," + input_fc + ",GDB," + download_url
		uploaded_file = root_folder.upload(out_folder_path_SHP + '.zip')
		download_url = uploaded_file.get_shared_link_download_url()
		myCsvRow = myCsvRow + ",SHP," + download_url
		arcpy.AddMessage(download_url)
		fd = open(csvOut,'a')
		fd.write(myCsvRow)
		fd.write('\n')
		fd.close()

for coName in countyArray:
	if phase_1 == "true":
		arcpy.AddMessage("ABOUT TO PROCESS: " +coName + " CREATING SHP and GDB....")
	else:
		arcpy.AddMessage("ABOUT TO PROCESS: " +coName + " LOADING IT TO BOX....")
	exportZipUploadLink(coName)