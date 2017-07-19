# V3StatewideLogic
An ArcGIS arcpy script tool, designed to handle aspects of standardization, added value, and QA/QC upon the V3 Wisconsin Statewide Parcel Database.

Processing steps include:

-Converts the following fields from string to double:
'CNTASSDVALUE','LNDVALUE','IMPVALUE','FORESTVALUE','ESTFMKVALUE', 'NETPRPTA','GRSPRPTA','ASSDACRES','DEEDACRES','GISACRES', 'LONGITUDE', 'LATITUDE'

-Calculates STATEID field for all records

-Calculates SCHOOLDISTNO or SCHOODIST values based on the other in not provided (from dictionaries)

-Calculates IMPROVED value

-Check acreage fields for scientific notation

-Check AUXCLASS values and if not in known list, adds them to Unusual AuxClass table

-Creates output summary tables of ('PREFIX', 'STREETNAME', 'STREETTYPE', 'SUFFIX')

-Runs Clean,Case and Trim over dataset

-Calculates LONGITUDE and LATITUDE

-Creates a Point feature class of all parcels
