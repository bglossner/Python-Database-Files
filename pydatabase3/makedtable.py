#!/usr/bin/python3

import mysql.connector as mariadb

mariadb_connection = mariadb.connect(user='pi', password='raspberry', database='pythonDB')
cursor = mariadb_connection.cursor()

def add_lists(l1, l2):
	l1.extend(l2)
	return l1

def make_specific_dtable(columnNames, labnum):
	overall_format = ["ID INT PRIMARY KEY AUTO_INCREMENT", "VA FLOAT()
	return ("CREATE TABLE VoltagesLS%d (%s" % (labnum, ("".jo))) 

def make_dtable(labnum):
	#FOR BASIC DATA TABLE OF BASIC BROADCAST
	
	# Set up for AMagPhase
	aob_format1 =	["aobV","aobI","aobVseq","aobIseq"]
	aob_format2 = ["fMag", "fPhase"]
	general_types = ["A", "B", "C"]
	aob_format = []
	
	for aobtype in aob_format1:
		for aobtype2 in aob_format2:
			for general_type in general_types:
				aob_format.append(aobtype + aobtype2 + general_type)
	
	# Set up for APowerData
	power_format2 = ["fW", "fVar", "fVa", "fPf", "fQ"]
	power_format = []
	general_types.append("TOTAL")
	
	for powertype in power_format2:
		for general_type in general_types:
			power_format.append(powertype + general_type)
	
	# Set up for frequency		
	freq_format = ["fFreq", "fFreqDev", "fFreqRate", "fTdevSec", "fTdevCyc"]
	
	# Set up for flicker
	flicker_format = ["fVa", "fIa", "fVc", "fIc", "fVb", "fIb"]
	
	print()
	# Whole thing
	overall_format = add_lists(aob_format, (add_lists(power_format, (add_lists(freq_format, flicker_format)))))
	
	overall_format = [oformat + " FLOAT(7, 4) NOT NULL, " for oformat in overall_format]
	overall_format.insert(0, "ID INT(10) NOT NULL PRIMARY KEY AUTO_INCREMENT, ")
	overall_format.append("Year INT(4), ")
	overall_format.append("YearSeconds INT(8)")
	
	return (("CREATE TABLE Lab_Standard_%d (" % (labnum)) + ("".join(overall_format)) + ")")
	
cursor.execute(make_dtable(int(raw_input("Enter lab standard number: "))))

mariadb_connection.close()

