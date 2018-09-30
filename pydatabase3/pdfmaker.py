#!/usr/bin/python

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
#An inch is 72px
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
import mysql.connector as mariadb
from datamanipulation import do_command
from datetime import datetime
from decimal import Decimal

#MariaDB stuff
global initial_mariadb_connection
initial_mariadb_connection = mariadb.connect(user='pi', password='raspberry', database='pythonDB')
global cursor
cursor = initial_mariadb_connection.cursor()

#global variables relating to the PDF
global fieldFont, dataFont, spacing, fonts, font, fontSize
fieldFont = 18
dataFont = 14
spacing = 10
fonts = ['Times-Bold', 'Times-Roman', 'Times-Italic']
spacing = [12, 14, 16]
font = fonts[0]
fontSize = 18

"""

	The following are variables for controlling the offsets and height differences
	of given texts in the PDF
	
	Important:
		THE PDF (0, 0) COORDINATE IS IN THE BOTTOM LEFT
		
		DEFAULT VALUES EXPECT PIXELS. Most of this is converted to INCHES
		
		.drawString() is part of the labgen library. It takes the x-coord in pixels, y-coord in pixels, and the text
			-It will draw it in the current font/font size
		
		Page is 8.5 x 11 inches (standard)
		serialHeight is just the height at which all the Serial Number:... sits on the page

"""

#=========== All Tests ===========#
pageWidth = 8.5
pageHeight = 11
serialHeight = (pageHeight - 1.5) * inch
popHeightChange = 0.35 * inch

#=========== 1133 =============#
#FOR BOTH

#FOR VERIFICATION
verSide1133 = 0.5 * inch
afterSerialOffset = verSide1133 + (2 * inch)
datetextLength = 0
verPopWidthChange1133 = 1.45 * inch
verSetHeight1133 = (spacing[0] * 3 + 4) + popHeightChange

#FOR CALIBRATION
calSide1133 = (1.0 + (float(7)/32)) * inch
calPopWidthChange1133 = float(60)/72 * inch #AKA 60
calCalConIndent = float(3)/8 * inch

#========== 928 ==============#
#FOR BOTH
side928 = float(10)/16 * inch
popWidthChange928 = 1.25 * inch

#FOR VERIFICATION
verPopHeightChange928 = popWidthChange928

#FOR CALIBRATION
calPopHeightChange928 = 0.5 * inch

#========== 933 ==============#
#FOR BOTH
side933 = 0.5 * inch

#FOR VERIFICATION
verPopWidthChange933 = 1.45 * inch
verSetHeight933 = (spacing[0] * 3 + 4) + popHeightChange

#FOR CALIBRATION
calPopHeightChange933 = float(7)/16 * inch
calPopWidthChange933 = float(13)/15 * inch
#calCalConIndent = float(3)/8 * inch

#==============================#

#Set font of given PDF here. Changes global variables
def fontSet(pg, fontGiven, size):
	global font, fontSize
	font = fontGiven
	fontSize = size
	pg.setFont(font, fontSize)

#Returns back the pixel value of where the text should be to be in the center of the page
#	stringWidth() is part of the labgen library and returns back the pixel width of a string
#	at a given font and font size
def grab_center(text, f, fS):
	global pageWidth
	centerX = (inch * pageWidth) / 2
	return centerX - (stringWidth(text, f, fS) / 2)

#For putting the units needed on the PDF to know what the numbers represent
def put_ver_unit_values(pg, whereY):
	distBetween = ((pageWidth * 72) - (verSide1133 * 2)) / 7
	yValue =  whereY
	values = ("V Mag(%)", "V Ph(deg)", "I Mag(%)", "I Ph(deg)", "W (%VA)", "var(%VA)", "VA(%)")
	for j, value in enumerate(values):
		xValue = (j + 1) * distBetween
		pg.drawString(xValue, yValue, ("%s" % value))
		
	return whereY - popHeightChange

#Makes the header part of the 1133 Verification
#Includes: title, serial number, date, and current time
def make_standard_header(pg, serial, modelStr="Model 1133 Power Sentinel", verStr="Verification Report", sideValue=verSide1133):
	firstString = modelStr
	secondString = verStr
	fontSet(pg, fonts[0], 14)
	
	pg.drawString(grab_center(firstString, font, fontSize), (pageHeight - 0.5) * inch, firstString)
	pg.drawString(grab_center(secondString, font, fontSize), (pageHeight - 0.5) * inch - spacing[2], secondString)
	
	fontSet(pg, fonts[0], 12)
	if(type(serial) == str):
		pg.drawString(sideValue, serialHeight, "Serial Number: %s" % serial)
	else:
		pg.drawString(sideValue, serialHeight, "Serial Number: %06d" % serial)
	
	"""print("%s" % datetime.now())
	print(type(datetime.now()))"""
	monthList = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
	currTime = str(datetime.now())
	currTimeParsed = datetime.strptime(currTime[:19], "%Y-%m-%d %H:%M:%S")
	datetext = "Date: %02d %s %4d" % (currTimeParsed.day, monthList[currTimeParsed.month - 1], currTimeParsed.year)
	timetext = "Time: %02d:%02d" % (currTimeParsed.hour, currTimeParsed.minute)
	global datetextLength
	datetextLength = stringWidth(datetext, font, fontSize)
	pg.drawString(pageWidth * inch - verSide1133 - datetextLength, serialHeight, datetext)
	pg.drawString(pageWidth * inch - verSide1133 - datetextLength, serialHeight - spacing[1], timetext)
	
	return serialHeight

#Creates in a PDF a "set" of data:
"""

	Set looks like: (each <number> is a 9 digit float value with 6 digits after the decimal)
	
	Input: <Param>Hz <Param>Volts <Param>Amps <Param>PF			Range: <Param>Volt <Param>Amp
	A	<number> 	<number> 	<number>	<number>	<number>	<number>	<number>
	B	<number> 	<number> 	<number>	<number>	<number>	<number>	<number>
	C	<number> 	<number> 	<number>	<number>	<number>	<number>	<number>
	
	Parameters to function: 
	- pdf
	- (x, y) in pixels
	- string of letters... "ABC" usually
	- list of input and range values to be inserted
	- tuple of tuples for the actual numerical data
	- number of tuples in parameter above

"""
def make_1133_ver_fullset(pg, where, letters, inputList, dataNeeded, dataLength, useRange=True, rangeStr=""):
	global fieldFont, dataFont, spacing, fonts, font, fontSize, pageWidth
	fontSet(pg, fonts[0], 12)
	
	inputListInput = inputList[:4] #List of first 4 elements (the numbers in the <Param> after Input: above)
	#Actually draws those two strings to the PDF
	pg.drawString(where[0], where[1], "Input: %gHz %gVolts %gAmps %gPF" % (inputListInput))
	
	if useRange:
		inputListRange = inputList[4:] #List of all other elements (numbers in the <Param> after Range: above)
		pg.drawString(inch * pageWidth / 2, where[1], "Range:  %gVolt %gAmp" % (inputListRange))
	elif rangeStr != "":
		pg.drawString(inch * pageWidth / 2, where[1], rangeStr)
	
	fontSet(pg, fonts[1], 10)
	leftSide = where[0] #usually 0.5 * inch
	distBetween = ((pageWidth * 72) - (leftSide * 2)) / dataLength
	
	#Draw out the letter and the numerical values as a row, for each row
	for i in range(len(letters)):
		yValue = where[1] - (spacing[0] * (i + 1) + 4)
		pg.drawString(leftSide, yValue, letters[i]) 
		for j, number in enumerate(dataNeeded[i]):
			if number != None:
				xValue = (j + 1) * distBetween
				#print(xValue)
				pg.drawString(xValue, yValue, ("%9.6f" % number))
			
	return where[1] - (spacing[0] * len(letters) + 4) - popHeightChange #returns height on page

#============================ 	1133	=================================#

#Makes full header with units
def make_1133_ver_header_control(pg, serialStr):
	currHeight = 0
	make_standard_header(pg, serialStr)
	put_ver_unit_values(pg, (pageHeight - 2.15))
		
#==================================		1133 VERIFICATION REPORT		==============================#


#Makes the header for the 1133 verification for a full, regular page
"""

extraData parameter:

1. MB value
2. GPS/IRIG value
3. ME value
4. PS value
5. Test set number
6. LS test number tuple
7. 4 tuples of date values for each of the dates
	a. ROM dates
	b. DSP dates
	c. Cal dates
	d. Cal dues

"""

def make_1133_ver_fullheader(pg, serialNum, *extraData):
	currHeight = 0
	make_standard_header(pg, serialNum)
	
	pg.drawString(verSide1133, serialHeight - spacing[1], "MB: %d" % extraData[0])
	pg.drawString(verSide1133, serialHeight - (spacing[1] * 2), "GPS/IRIG: %d" % extraData[1])
	pg.drawString(afterSerialOffset, serialHeight - spacing[1], "ME: %d" % extraData[2])
	pg.drawString(afterSerialOffset, serialHeight - (spacing[1] * 2), "PS: %d" % extraData[3])
	testsetStr = "Test Set: %d" % extraData[4]
	pg.drawString(pageWidth * inch - verSide1133 - datetextLength, serialHeight - (spacing[1] * 2), testsetStr)
	currHeight = serialHeight - (spacing[1] * 2)
	
	currHeight -= popHeightChange
	dateFields = ("Cal. Due", "Cal. Date", "DSP Date", "ROM Date")
	dateRowNames = ("Unit Under Test", "1133 LS%d" % extraData[5][0], "1133 LS%d" % extraData[5][1])
	tmp = 0
	for i, field in enumerate(dateFields):
		xValue = pageWidth * inch - verSide1133 - datetextLength - (i * verPopWidthChange1133)
		fontSet(pg, fonts[0], 12)
		pg.drawString(xValue, currHeight, field)
		for j, date in enumerate(extraData[6][i]):
			yValue = currHeight - (spacing[0] * (j + 1) + 4)
			fontSet(pg, fonts[1], 10)
			pg.drawString(xValue, yValue, date)
			if tmp == 0:
				pg.drawString(verSide1133, yValue, dateRowNames[j])
			
		tmp = 1
			
	tmp = 0
	#Copied from above yValue
	currHeight -= (spacing[0] * 3 + 4)
	fontSet(pg, fonts[0], 12)
	currHeight -= popHeightChange
	
	currHeight = put_ver_unit_values(pg, currHeight)
	
	return currHeight
	

#For just the final line on the verification report
def draw_1133_ver_final_line(pg, whereY, freq, result, pts):
	fontSet(pg, fonts[1], 10)
	
	pg.drawString(verSide1133, whereY, "Frequency Error: %9.6f (ppm)" % freq)
	
	ptString = "{} point(s)".format(pts)
	currX = (pageWidth * inch) - verSide1133 - stringWidth(ptString, font, fontSize)
	pg.drawString(currX, whereY, ptString)
	currX -= inch
	
	fontSet(pg, fonts[0], 12)
	pg.drawString(currX, whereY, result.upper())
	currX -= inch
	
	fontSet(pg, fonts[1], 10)
	pg.drawString(currX, whereY, "Results:")

def do_1133_ver_test(c):
	testDateTuple = (("28 AUG 2018", "27 AUG 2018", "27 AUG 2018"), ("28 FEB 2018", "27 FEB 2018", "27 FEB 2018"), 
					("25 NOV 2008", "25 NOV 2008", "25 NOV 2008"), ("07 DEC 2016", "07 DEC 2016", "07 DEC 2016"))
	currHeight = make_1133_ver_fullheader(c, 73, 1, 1, 1, 1, 4, (51, 56), testDateTuple)
	currHeight = make_1133_ver_fullset(c, (verSide1133, currHeight), "ABC", (60, 120, 5, 1, 150, 5),
							((-0.001811, -0.002333, -0.003313, 0.000250, -0.005124, -0.004498, -0.005117),
							(-0.001434, -0.002891, -0.003790, 0.008159, -0.005279, -0.019274, -0.005231),
							(0.000086, -0.002217, -0.003289, 0.012427, -0.003273, -0.025553, -0.003215)),
							7)
	while currHeight > verSetHeight1133 * 2:
		currHeight = make_1133_ver_fullset(c, (verSide1133, currHeight), "ABC", (60, 120, 5, 1, 150, 5),
							((-0.001811, -0.002333, -0.003313, 0.000250, -0.005124, -0.004498, -0.005117),
							(-0.001434, -0.002891, -0.003790, 0.008159, -0.005279, -0.019274, -0.005231),
							(0.000086, -0.002217, -0.003289, 0.012427, -0.003273, -0.025553, -0.003215)),
							7)
	
	if currHeight > (verSide1133 + 10):  # 1/2 an inch needed to display
		#print("it is")
		currHeight -= (0.15 * inch) #already .35 below. We want .5
		draw_1133_ver_final_line(c, currHeight, 0.055630, "FAIL", 3)
	


#==================================		1133 CALIBRATION REPORT		==============================#

def make_1133_cal_standard_header(pg, serial, testSetNum):
	firstString = "Model 1133 Power Sentinel"
	secondString = "Calibration Report"
	fontSet(pg, fonts[0], 14)
	
	pg.drawString(grab_center(firstString, font, fontSize), (pageHeight - 0.5) * inch, firstString)
	pg.drawString(grab_center(secondString, font, fontSize), (pageHeight - 0.5) * inch - spacing[2], secondString)
	
	fontSet(pg, fonts[0], 12)
	if(type(serial) == str):
		pg.drawString(calSide1133, serialHeight, "Serial Number: %s" % serial)
	else:
		pg.drawString(calSide1133, serialHeight, "Serial Number: %06d" % serial)
		
	monthList = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
	currTime = str(datetime.now())
	currTimeParsed = datetime.strptime(currTime[:19], "%Y-%m-%d %H:%M:%S")
	datetext = "Date: %02d %s %4d" % (currTimeParsed.day, monthList[currTimeParsed.month - 1], currTimeParsed.year)
	timetext = "Time: %02d:%02d" % (currTimeParsed.hour, currTimeParsed.minute)
	global datetextLength
	datetextLength = stringWidth(datetext, font, fontSize)
	pg.drawString(pageWidth * inch - calSide1133 - datetextLength, serialHeight, datetext)
	pg.drawString(pageWidth * inch - calSide1133 - datetextLength, serialHeight - spacing[1], timetext)
	pg.drawString(calSide1133, serialHeight - spacing[1], "Test Set: %d" % testSetNum)
	
"""

	dataRec:
	
	A tuple of 3 tuples of 5 tuples of length 5
	-PreCal, Post Cal, Delta
		-tuple of units for each row
	(((), (), (), (), ()), ((), (), (), (), ()), ((), (), (), (), ()))

"""

def make_1133_cal_cal_constants(pg, dataRec, givenDelta=True):
	currHeight = serialHeight - (spacing[1] * 2)
	newStr = "Calibration Constants"
	pg.drawString(grab_center(newStr, font, fontSize), currHeight, newStr)
	unitList = ("V Mag", "V Phase", "P Mag", "P Phase", "V Lin.")
	currHeight -= popHeightChange
	#print(calPopWidthChange1133)
	for i, unit in enumerate(unitList):
		pg.drawString(calSide1133 * 2 + (i * calPopWidthChange1133), currHeight, unit)
	currHeight -= spacing[1]
		
	if not givenDelta:
		deltaList = [dataRec[i][1] - dataRec[i][0] for i in range(len(dataRec)) if dataRec[i][1] != None]
	
	#Tests
	testList = ("Pre Cal", "Post Cal", "Delta")
	for i, test in enumerate(dataRec):
		fontSet(pg, fonts[0], 12)
		pg.drawString(calSide1133, currHeight, testList[i])
		currHeight -= spacing[1]
		for j, row in enumerate(test):
			fontSet(pg, fonts[1], 10)
			pg.drawString(calSide1133 + calCalConIndent, currHeight, str(j))
			for k, value in enumerate(row):
				if value != None:
					pg.drawString(calSide1133 * 2 + (k * calPopWidthChange1133), currHeight, "{:10.3e}".format(value))
			if not givenDelta:
				pg.drawString(calSide1133 * 2 + (len(row) * calPopWidthChange1133), currHeight, "{:10.3e}".format(deltaList[i]))
			currHeight -= spacing[0]
		currHeight -= 2 #So it's 12 instead of 10
		
	return currHeight
	
	
	
def make_1133_cal_measurement_errors(pg, whereY, dataRec):
	currHeight = whereY
	fontSet(pg, fonts[0], 12)
	newStr = "Measurement Error"
	pg.drawString(grab_center(newStr, font, fontSize), currHeight, newStr)
	unitList = ("V Mag(%)", "V Ph(deg)", "I Mag(%)", "P Ph(deg)", "W(%VA)", "V lin")
	currHeight -= popHeightChange
	#print(calPopWidthChange1133)
	for i, unit in enumerate(unitList):
		pg.drawString(calSide1133 * 2 + (i * calPopWidthChange1133), currHeight, unit)
	currHeight -= spacing[1]
		
	#Tests
	testList = ("Pre Cal", "Zero Cal", "Post Cal")
	testRowList = ("V:A-N I:A", "V:B-N I:B", "V:C-N I:C", "V:A-B I:A", "V:C-N I:C")
	for i, test in enumerate(dataRec):
		fontSet(pg, fonts[0], 12)
		pg.drawString(calSide1133, currHeight, testList[i])
		currHeight -= spacing[1]
		for j, row in enumerate(test):
			fontSet(pg, fonts[1], 10)
			pg.drawString(calSide1133, currHeight,testRowList[j])
			for k, value in enumerate(row):
				if value != None:
					pg.drawString(calSide1133 * 2 + (k * calPopWidthChange1133), currHeight, "{:10.3e}".format(value))
			currHeight -= spacing[0]
		currHeight -= 2 #So it's 12 instead of 10


def do_1133_cal_test(c):
	make_1133_cal_standard_header(c, "A09430", 2)
	currHeight = make_1133_cal_cal_constants(c, (((0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0)), 
									((0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0)),
									((0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0))))
									
									
	make_1133_cal_measurement_errors(c, currHeight + 12 - popHeightChange, 
										(((0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0)), 
										((0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0)),
										((0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (0, 0, 0, 0, 0))))
	#(0.0001062, -0.0000001879, 0.00016, -0.0000000979)
	


#==================================		928 VERIFICATION REPORT		==============================#
	
def make_928_measurement_error(pg, whereY, dataRec):
	fontSet(pg, fonts[0], 12)
	pg.drawString(side928, whereY, "Measurement Error")
	currHeight = whereY - spacing[1]
	fieldsTuple = ("Parameter", "Specification", "60Hz", "50Hz", "Units")
	for i in range(5):
		pg.drawString(side928 + (i * popWidthChange928), currHeight, fieldsTuple[i])
	rowTuple = ("VmagA", "VmagB", "IImagA", "IVmagA", "IImagB", "IVmagB", "VphaseB", "IIphaseA", "IVphaseA", 
				"IIphaseB", "IVphaseB", "Frequency")
	unitTuple = ("Percent", "Percent", "Percent", "Percent", "Percent", "Percent", "Degree", "Degree", 
				"Degree", "Degree", "Degree", "Percent")
	currHeight -= spacing[1]
	
	fontSet(pg, fonts[1], 12)
	for i, row in enumerate(dataRec):
		pg.drawString(side928, currHeight, rowTuple[i])
		for j in range(len(row) + 2):
			if j < len(row):
				value = row[j]
				if value != None:
					if type(value) == float:
						valueToPut = "{:.4f}".format(value)
					elif (type(value) == str):
						if value.upper() not in ("PASS", "FAIL"):
							valueToPut = value[0].upper() + value[1:].lower()
						else:
							valueToPut = value.upper()
					else:
						valueToPut = value
			else:
				if j == (len(row)):
					valueToPut = (unitTuple[i])[0].upper() + (unitTuple[i])[1:].lower() #Should just be the same as the values above
				else:
					#If the 60Hz and 50Hz values are both under the specification value, it passes
					valueToPut = "PASS" if ((abs(row[1]) < row[0]) and (abs(row[2]) < row[0])) else "  FAIL"
				
			pg.drawString(side928 + ((j + 1) * popWidthChange928), currHeight, valueToPut)
			
		currHeight -= spacing[0]
		
def do_928_ver_test(c):
	currHeight = make_standard_header(c, 1000, modelStr="Model 928A Power System Multimeter", sideValue=side928)
	make_928_measurement_error(c, currHeight - inch, (
								(0.100, -0.00080, -0.002700),
								(0.100, -0.00080, 0.002700),
								(0.100, -0.5195, 36.0125),
								(0.100, -0.00080, -0.002700),
								(0.100, -0.00080, -0.002700),
								(0.100, -1241.1165, -0.0044),
								(0.100, -0.00080, -0.002700),
								(0.100, -0.00080, -0.002700),
								(0.100, -0.00080, -0.002700),
								(0.100, -0.00080, 0.002700),
								(0.100, -0.00080, -0.002700),
								(0.100, -0.00080, -0.002700)))
		


#==============================		928 Calibration Report	 ========================*

#pretty much the same as the verification except that time is optional
def make_928_cal_header(pg, serial, should_show_time=False):
	firstString = "Model 928A Power System Mulitmeter"
	secondString = "Verification Report"
	fontSet(pg, fonts[0], 14)
	
	pg.drawString(grab_center(firstString, font, fontSize), (pageHeight - 0.5) * inch, firstString)
	pg.drawString(grab_center(secondString, font, fontSize), (pageHeight - 0.5) * inch - spacing[2], secondString)
	
	fontSet(pg, fonts[0], 12)
	if(type(serial) == str):
		pg.drawString(side928, serialHeight, "Serial Number: %s" % serial)
	else:
		pg.drawString(side928, serialHeight, "Serial Number: %d" % serial)
	
	monthList = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")
	currTime = str(datetime.now())
	currTimeParsed = datetime.strptime(currTime[:19], "%Y-%m-%d %H:%M:%S")
	datetext = "Date: %02d %s %d" % (currTimeParsed.day, monthList[currTimeParsed.month - 1], currTimeParsed.year)
	timetext = "Time: %02d:%02d" % (currTimeParsed.hour, currTimeParsed.minute)
	global datetextLength
	datetextLength = stringWidth(datetext, font, fontSize)
	if should_show_time:
		pg.drawString(pageWidth * inch - side928 - datetextLength, serialHeight, datetext)
		pg.drawString(pageWidth * inch - side928 - datetextLength, serialHeight - spacing[1], timetext)
		
	return serialHeight
		
def make_928_cal_cal_constants(pg, whereY, dataRec, givenDelta=True):
	fontSet(pg, fonts[0], 12)
	pg.drawString(side928, whereY, "Calibration Constants")
	currHeight = whereY - spacing[1]
	
	#Tests
	testList = ("Pre Cal", "Post Cal", "Delta")
	for i, test in enumerate(testList):
		pg.drawString(side928 + ((i + 1) * popWidthChange928), currHeight, test)
	
	currHeight -= spacing[1]
	
	rowsTuple = ("VmagA", "VmagB", "VphaseB", "IImagA", "IImagB", "IVmagA", "IVmagB", "IIphaseA", "IIphaseB", "IVphaseA", 
				 "IVphaseB")
				 
	if not givenDelta:
		deltaList = [dataRec[i][1] - dataRec[i][0] for i in range(len(dataRec)) if dataRec[i][1] != None]
		
	fontSet(pg, fonts[1], 12)
	for i, row in enumerate(dataRec):
		pg.drawString(side928, currHeight, rowsTuple[i])
		for j, value in enumerate(row):
			if value != None:
				pg.drawString(side928 + ((j + 1) * popWidthChange928), currHeight, "{:10.3e}".format(value))
		
		if not givenDelta:
			pg.drawString(side928 + ((len(row) + 1) * popWidthChange928), currHeight, "{:10.3e}".format(deltaList[i]))
		currHeight -= spacing[1]
		
	return currHeight + spacing[1]
				
def make_928_cal_measurement_error(pg, whereY, dataRec):
	fontSet(pg, fonts[0], 12)
	pg.drawString(side928, whereY, "Measurement Error")
	currHeight = whereY - spacing[1]
	
	fieldsTuple = ("Parameter", "Pre Cal", "Zero Cal", "Post Cal", "Specification", "Units")
	
	for i in range(6):
		pg.drawString(side928 + (i * popWidthChange928), currHeight, fieldsTuple[i])
		
	currHeight -= spacing[1]
	rowsTuple = ("VmagA", "VmagB", "VphaseB", "IImagA", "IImagB", "IVmagA", "IVmagB", "IIphaseA", "IIphaseB", "IVphaseA", 
				 "IVphaseB")
	unitTuple = ("%", "%", "degree", "%", "%", "%", "%", "degree", "degree", "degree", "degree")
	
	fontSet(pg, fonts[1], 12)
	for i, row in enumerate(dataRec):
		pg.drawString(side928, currHeight, rowsTuple[i])
		for j in range(len(row) + 2):
			if j < len(row):
				value = row[j]
				if value != None:
					valueToPut = "{:.4f}".format(value)
			elif j == len(row):
				valueToPut = unitTuple[i]
			else:
				valueToPut = "PASS" if abs(row[2]) < row[3] else "  FAIL"
				pg.drawString(pageWidth * inch- side928 - stringWidth(valueToPut, font, fontSize), currHeight, valueToPut)
				break
				
			pg.drawString(side928 + ((j + 1) * popWidthChange928), currHeight, valueToPut)
		
		currHeight -= spacing[1]
	
	return currHeight
	
def do_928_cal_test(c):
	currHeight = make_928_cal_header(c, 1000, True)
	currHeight -= calPopHeightChange928 * 2
	currHeight = make_928_cal_cal_constants(c, currHeight,
											((0, 0.0001334), (0, -0.006342), (1, 0.025), (0, 0),
											(0, 0.0001334), (0, -0.006342), (1, 0.025), (0, 0),
											(0, 0.0001334), (0, -0.006342), (1, 0.025)), False)
	currHeight -= calPopHeightChange928
	make_928_cal_measurement_error(c, currHeight,
									((0.0131, 0.0133, -0.0003, 0.1), (0, 0, 2, 0.1), (0.0131, 0.0133, -0.0003, 0.1),
									(0.0131, 0.0133, -0.0003, 0.1), (0.0131, 0.0133, -0.0003, 0.1), (0, 0, 0, 0),
									(0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0), (0, 0, 0, 0)))

#============================ 	933 VERIFICATION 	================================#

def make_933_ver_fullheader(pg, serial, moduleNum, module, *extraData):
	currHeight = make_standard_header(pg, serial, "Model 933 Portable Power Sentinel",
											"Verification Report CT Module %02d" % moduleNum)
	
	currHeight -= spacing[1]
	pg.drawString(verSide1133, currHeight, "Current Module: %s" % module)
	
	currHeight -= popHeightChange
	dateFields = ("Cal. Due", "Cal. Date", "DSP Date", "ROM Date")
	dateRowNames = ("Unit Under Test", "1133 LS%d" % extraData[0][0], "1133 LS%d" % extraData[0][1])
	tmp = 0
	for i, field in enumerate(dateFields):
		xValue = pageWidth * inch - verSide1133 - datetextLength - (i * verPopWidthChange1133)
		fontSet(pg, fonts[0], 12)
		pg.drawString(xValue, currHeight, field)
		for j, date in enumerate(extraData[1][i]):
			yValue = currHeight - (spacing[0] * (j + 1) + 4)
			fontSet(pg, fonts[1], 10)
			pg.drawString(xValue, yValue, date)
			if tmp == 0:
				pg.drawString(verSide1133, yValue, dateRowNames[j])
			
		tmp = 1
			
	tmp = 0
	#Copied from above yValue
	currHeight -= (spacing[0] * 3 + 4)
	fontSet(pg, fonts[0], 12)
	currHeight -= popHeightChange
	
	currHeight = put_ver_unit_values(pg, currHeight)
	
	return currHeight

#Number of passes is represented by a byte (1 = PASS, 0 = FAIL)
def make_933_ver_final_section(pg, passByte, freq, currHeight, pts=0):
	fontSet(pg, fonts[1], 10)
	
	#6 is the maximum number of passes
	passList = ["PASS" if passByte & (2 ** i) else "FAIL" for i in range(6)]
	
	pg.drawString(side933, currHeight, "Real Time Clock: %s" % passList[0])
	currHeight -= spacing[2]
	auxStr = "Auxiliary IO Port: %s" % passList[1]
	pg.drawString(side933, currHeight, auxStr)
	pg.drawString(side933 + stringWidth(auxStr, font, fontSize), currHeight, "   USB: %s" % passList[2])
	currHeight -= spacing[2]
	hfStr = "Hot Flash: %s" % passList[3]
	pg.drawString(side933, currHeight, hfStr)
	pg.drawString(side933 + stringWidth(hfStr, font, fontSize), currHeight, "   DSP Flash: %s" % passList[4])
	currHeight -= spacing[2]
	#For just the final line on the verification report	
	pg.drawString(verSide1133, currHeight, "Frequency Error: %9.6f (ppm)" % freq)
	
	if passList[5] != "PASS":
		ptString = "{} point(s)".format(pts)
		currX = (pageWidth * inch) - side933 - stringWidth(ptString, font, fontSize)
		pg.drawString(currX, currHeight, ptString)
	else:
		currX = (pageWidth - 1) * inch
		
	currX -= inch
	
	fontSet(pg, fonts[0], 12)
	pg.drawString(currX, currHeight, passList[5])
	currX -= inch
	
	fontSet(pg, fonts[1], 10)
	pg.drawString(currX, currHeight, "Results:")
	

def do_933_ver_test(c):
	currHeight = make_933_ver_fullheader(c, "A0369", 1, "A0117", (33, 37), (("28 AUG 2018", "27 AUG 2018", "27 AUG 2018"), ("28 FEB 2018", "27 FEB 2018", "27 FEB 2018"), 
					("25 NOV 2008", "25 NOV 2008", "25 NOV 2008"), ("07 DEC 2016", "07 DEC 2016", "07 DEC 2016")))
	
	while currHeight > verSetHeight1133 * 2:
		currHeight = make_1133_ver_fullset(c, (verSide1133, currHeight), "ABC", (60, 120, 5, 1, 150, 5),
							((-0.001811, -0.002333, -0.003313, 0.000250, -0.005124, -0.004498, -0.005117),
							(-0.001434, -0.002891, -0.003790, 0.008159, -0.005279, -0.019274, -0.005231),
							(0.000086, -0.002217, -0.003289, 0.012427, -0.003273, -0.025553, -0.003215)),
							7, False, "Ello")
							
	make_933_ver_final_section(c, 0x0d, 0.039736, currHeight)



#============================ 	933 CALIBRATION 	================================#

def make_933_cal_header(pg, serial, module):
	currHeight = make_standard_header(pg, serial, "Model 933 Portable Power Sentinel", "Calibration Report")
	currHeight -= spacing[1]
	pg.drawString(side933, currHeight, "Current Module: {}".format(module))
	return currHeight

def make_unit(pg, currHeight, units):
	for i, unit in enumerate(units):
		pg.drawString(side933 + ((i + 1) * calPopWidthChange933), currHeight, unit)
	
def make_933_cal_cal_constants(pg, currHeight, xNumMag, xNumPhase, dataRec, givenDelta=True):
	fontSet(pg, fonts[0], 12)
	newStr = "Calibration Constants"
	currHeight -= spacing[1]
	pg.drawString(grab_center(newStr, font, fontSize), currHeight, newStr)
	currHeight -= calPopHeightChange933
	unitTuple = ("V Mag", "V Phase", "I Mag", "I Phase", "V Lin.", "I Mag({}x)".format(xNumMag), "I Ph({}x)".format(xNumPhase))
	make_unit(pg, currHeight, unitTuple)
	
	def make_cal_constant_table(currHeight, dataGiven):
		for j, row in enumerate(dataGiven):
			fontSet(pg, fonts[1], 10)
			pg.drawString(side933 + calCalConIndent, currHeight, str(j))
			for k, value in enumerate(row):
				if value != None:
					pg.drawString(side933 + ((k + 1) * calPopWidthChange933), currHeight, "{:10.3e}".format(value))
			currHeight -= spacing[0]
		
		currHeight -= 2 #So it's 12 instead of 10
		return currHeight
	
	testList = ("Pre Cal", "Post Cal", "Delta")
	for i, testSet in enumerate(dataRec):
		fontSet(pg, fonts[0], 12)
		pg.drawString(side933, currHeight, testList[i])
		currHeight -= spacing[1]
		currHeight = make_cal_constant_table(currHeight, testSet)
	
	if not givenDelta:
		#Just makes a two-dim list that subtracts Post Cals from Pre Cals (Pre - Post)
		deltaList = [[dataRec[0][j][k] - dataRec[1][j][k] for k in range(len(dataRec[0][j])) if dataRec[0][j][k] != None] for j in range(len(dataRec[0]))]
		#print(deltaList)
		fontSet(pg, fonts[0], 12)
		pg.drawString(side933, currHeight, "Delta")
		currHeight -= spacing[1]
		currHeight = make_cal_constant_table(currHeight, deltaList)
		
	return currHeight
		
def make_933_cal_measurement_error(pg, currHeight, dataRec, optionalStr=""):
	fontSet(pg, fonts[0], 12)
	newStr = "Measurement Error"
	pg.drawString(grab_center(newStr, font, fontSize), currHeight, newStr)
	if optionalStr != "":
		pg.drawString((pageWidth - 2.5) * inch, currHeight - spacing[1], optionalStr)
	
	currHeight -= calPopHeightChange933
	unitTuple = ("V Mag(%)", "V Ph(deg)", "I Mag(%)", "I Ph(deg)", "W(%VA)", "I Mag(%)", "I Ph(deg)", "V lin")
	make_unit(pg, currHeight, unitTuple)
	currHeight -= spacing[1]
	
	#Tests
	testList = ("Pre Cal", "Zero Cal", "Post Cal")
	testRowList = ("V:A-N I:A", "V:B-N I:B,", "V:C-N I:C,", "V:A-B I:N,", "V:C-N,")
	for i, test in enumerate(dataRec):
		fontSet(pg, fonts[0], 12)
		pg.drawString(side933, currHeight, testList[i])
		currHeight -= spacing[1]
		for j, row in enumerate(test):
			fontSet(pg, fonts[1], 10)
			pg.drawString(side933, currHeight,testRowList[j])
			for k, value in enumerate(row):
				if(value != None):
					pg.drawString(side933 + ((k + 1) * calPopWidthChange933), currHeight, "{:10.3e}".format(value))
			currHeight -= spacing[0]
		currHeight -= 2
	
def do_933_cal_test(c):
	xNum = 24
	currHeight = make_933_cal_header(c, "A0369", "A0117")
	currHeight = make_933_cal_cal_constants(c, currHeight, xNum, xNum, (((0, 0, 2.342, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0),
											(0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0)),
											((0, 0, -1.23, 0, 2.2, 0, 0), (0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0),
											(0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0))), False)
											#((0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0),
											#(0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0))))
	currHeight -= calPopHeightChange933
	make_933_cal_measurement_error(c, currHeight, 
									(((0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0),
									(0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
									((0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0),
									(0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0)),
									((0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0),
									(0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0))), optionalStr="%g X current mode" % xNum)

def make_pdf_file(filename):
	c = canvas.Canvas(filename, pagesize=letter)
	#c.translate(inch, inch)
	#c.setFont(font, 18)
	c.setFillColorRGB(0, 0, 0) #draw stuff in black
	
#====================== 	TESTS 	==============================#

	#do_1133_ver_test(c)
	#do_1133_cal_test(c)
	#do_928_ver_test(c)
	#do_928_cal_test(c)
	#do_933_ver_test(c)
	#do_933_cal_test(c)
	
#=================================================================#
	
	#c.drawString(grab_center(text, font, fontSize), 5 * inch,"Hello\tHello\tHello")
	c.showPage() #end of page, start new one if anything is after it
	c.save()
	
def get_database_data(user_to_use="pi", password_to_use="raspberry", database_to_use="pythonDB", table="", *other):
	if (len(other) == 0) and ('initial_mariadb_connection' in globals()):
		global initial_mariadb_connection
		mariadb_connection = initial_mariadb_connection
	else:
		mariadb_connection = mariadb.connect(user=user_to_use, password=password_to_use, database=database_to_use)
		
	returnResponse = do_command("see table", mariadb_connection)
	if type(returnResponse) == str:
		print(returnResponse)
	
	print("Success")
	mariadb_connection.close()


make_pdf_file("database.pdf")
	
