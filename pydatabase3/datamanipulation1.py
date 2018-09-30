#!/usr/bin/python3.3

from __future__ import print_function
import mysql.connector as mariadb, sys

def initialize_default_action(h="localhost", u="pi", p="raspberry", d="pythonDB"):
	mariadb_connection = mariadb.connect(host=h, user=u, password=p, database=d)
	print("*** Do not include parentheses in response ***")
	cmd_list = ["see table", "reset table", "delete table", "return data", "(display COL and CSV) OR (1)", "(display ROW and CSV) OR (2)"];
	for i, cmd in enumerate(cmd_list):
		print(cmd, end=", ")
	print("\n")
	user = raw_input("Command you'd like to use: ")
	do_command(user, mariadb_connection)
	mariadb_connection.close()

def do_command(user_response, *data):
	global tableUsed
	tableUsed = ""
	
	if(len(data) != 0):
		cursor = (data[0]).cursor()
	else:
		return "No connection to use"
	
	def get_table_data():
		global tableUsed
		cursor.execute("SHOW TABLES")
		result = cursor.fetchall()
		table_list = [((item[0])) for item in result]
		if(len(data) <= 1):
			print("Tables that exist: ", end="")
			for i, table in enumerate(table_list):
				print(table + " [{}]".format(i + 1), end=", ")
			table_to_see = raw_input("\nWhich would you like to see? ")
		else:
			table_to_see = data[1]
		if (table_to_see in table_list) or ((table_to_see.isdigit()) and ((int(table_to_see) <= len(table_list)) and (int(table_to_see) >= 0))):
			if table_to_see.isdigit():
				table_to_see = table_list[int(table_to_see) - 1]
			cursor.execute("SELECT * FROM %s" % (table_to_see))
			tableUsed = table_to_see
			#print(tableUsed)
			return cursor.fetchall()
		else:
			return "Not a valid table name"
			
	def get_table():
		global tableUsed
		cursor.execute("SHOW TABLES")
		result = cursor.fetchall()
		table_list = [((item[0])) for item in result]
		if(len(data) <= 1):
			print("Tables that exist: ", end="")
			for i, table in enumerate(table_list):
				print(table + " [{}]".format(i + 1), end=", ")
			table_to_see = raw_input("\nWhich would you like to see? ")
		else:
			table_to_see = data[1]
		if (table_to_see in table_list) or ((table_to_see.isdigit()) and ((int(table_to_see) <= len(table_list)) and (int(table_to_see) >= 0))):
			if table_to_see.isdigit():
				table_to_see = table_list[int(table_to_see) - 1]
			return table_to_see
		return -1
			
	def get_column_names(tableName):
		cursor.execute("show columns from {}".format(tableName))
		result = cursor.fetchall()
		column_list = [(repr(item[0]))[2:len(item[0]) + 2] for item in result]
		return column_list
	
	if user_response == "delete table":
		cursor.execute("SHOW TABLES")
		print("Tables that exist: ", end="")
		result = cursor.fetchall()
		table_list = [((item[0])) for item in result]
		if not len(table_list):
			print("No tables exist in this database")
		for table in table_list:
			print(table, end=", ")
		table_to_delete = raw_input("\nWhich would you like to delete? ")
		if table_to_delete in table_list:
			confirm = raw_input("Are you sure you'd like to delete %s? (yes/no): " % (table_to_delete))
			if(confirm == "yes"):
				cursor.execute("DROP TABLE %s" % (table_to_delete))
				return 0
		else:
			print("Not a valid table name")
	elif user_response == "create table":
		pass
	elif user_response == "see table":
		data_received = get_table_data()
		if data_received == "Not a valid table name":
			return data_received
		if len(data_received) > 0:
			for row in data_received:
				for coldata in row:
					print(str(coldata) + "|", end="")
				print()
		else:
			print("No data in this table")
	elif (user_response == "insert data") and (len(data) > 0):
		pass
	elif user_response == "return data":
		return get_table_data()
	elif (user_response == "display COL and CSV") or (user_response == "1") or ("COL" in user_response):
		data_received = get_table_data()
		#print(tableUsed)
		if tableUsed:
			column_names = get_column_names(tableUsed)
			with open("makecol{}.csv".format(tableUsed), "w") as f:
				for i, column in enumerate(column_names):
					print(column + ":")
					f.write(column + ",")
					for j in range(len(data_received)):
						dataToUse = data_received[j][i]
						print("\t{}: ".format(j) + str(dataToUse))
						f.write(str(dataToUse) + ",")
					print("\n")
					f.write("\n")
				print("Done\n")
					
	elif (user_response == "display ROW and CSV") or (user_response == "2") or ("ROW" in user_response):
		data_received = get_table_data()
		#print(tableUsed)
		if tableUsed:
			column_names = get_column_names(tableUsed)
			with open("makerow{}.csv".format(tableUsed), "w") as f:
				for i, column in enumerate(column_names):
					f.write(column + ("," if i < len(column_names) - 1 else ""))
					print(column)
				print()
				f.write("\n")
				for row in data_received:
					for i, value in enumerate(row):
						f.write(str(value) + ("," if i < len(row) - 1 else ""))
						print(value)
					print()
					f.write("\n")
					
	elif "reset" in user_response:
		table = get_table()
		if table != -1:
			print("Resetting {} table".format(table))
			cursor.execute("delete from {}".format(table))
			cursor.execute("alter table {} AUTO_INCREMENT=1".format(table))
			print("Reset")
			
	elif "parse" in user_response:
		csv_to_use = raw_input("Name of CSV file: ")
		with open(csv_to_use, 
					
	print("\nNo table affected")
	
initialize_default_action("bourbon", "testset", "testset", "testset")
