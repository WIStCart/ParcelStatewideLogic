import arcpy
from arcpy import env

def createSummaryTables(fc,outDir):
	zoning_fields = ["ZONINGFIPS","JURISDICTION","ZONINGCLASS","DESCRIPTION","LINK"]
	for i in zoning_fields:
		arcpy.Frequency_analysis(fc,outDir +"/"+fc+"_"+i+"_Summary",i)

#Initialize variables
in_dir = arcpy.GetParameterAsText(0)
arcpy.env.workspace = in_dir

#Loop through feature classes in gdb
fcs = arcpy.ListFeatureClasses()
for fc in fcs:
	arcpy.AddMessage("WRITING SUMMARIES FOR "+ fc)
	createSummaryTables(fc,in_dir)
