#include <mysql.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

void error_occured(MYSQL *con)
{
	printf("%s\n", mysql_error(con));
	mysql_close(con);
	printf("CYA\n");
	exit(1);
}

int showColumns(MYSQL *con)
{
	if (mysql_query(con, "SHOW COLUMNS FROM Lab_Standard_1"))
	{
		error_occured(con);
	}
	printf("\nShowing Columns...\n");
	return 1;
}

int deleteFirstRow(MYSQL *con)
{
	if(mysql_query(con, "DELETE FROM Lab_Standard_1 WHERE Year=2018"))
	{
		error_occured(con);
	}
	if(mysql_query(con, "ALTER TABLE Lab_Standard_1 AUTO_INCREMENT = 1"))
	{
		error_occured(con);
	}
	printf("\nDeleted row successfully...\n")
	return 1;
}

int enterTestRow(MYSQL *con)
{
	int maxCount = 55;
	char c[(6 * maxCount) + 1];
	memset(c, 0, sizeof(c));
	for(int i = 0; i < maxCount; i++)
	{
		if (i > 0)
		{
			strcat(c, ",");
		}
		strcat(c, "10.02");
	}
	strcat(c, "\0");
	printf("%s\n", c);
	char queryString[800];
	memset(queryString, 0, sizeof(queryString));
	snprintf(queryString, 799, "INSERT INTO Lab_Standard_1 VALUES(default,%s,2018,3562354)", c);
	printf("%s\n", queryString);
	if(mysql_query(con, queryString))
	{
		error_occured(con);
	}
	printf("\nUpdated Table Successfully...\n");
	return 1;
}

int main()
{
	MYSQL *con = mysql_init(NULL);
	if(con == NULL)
	{
		printf("%s\n", mysql_error(con));
		exit(1);
	}
	
	if(mysql_real_connect(con, "localhost", "pi", "raspberry", "pythonDB", 0, NULL, 0) == NULL)
	{
		error_occured(con);
	}
	else
	{
		printf("Successful connection\n");
		char inputChar;
		//memset(inputChar, 0, sizeof(inputChar));
		int inputInt;
		printf("Enter a:\t[0] - Delete Row\n\t\t[1] - Add Test Row\n\t\t[2] - Show Columns\n\n:");
		inputChar = getchar();
		if(isdigit(inputChar))
		{
			inputInt = inputChar - '0';
		}
		switch(inputInt)
		{
			case 0:
				deleteFirstRow(con);
				break;
			case 1:
				enterTestRow(con);
				break;
			case 2:
				showColumns(con);
				break;
			default:
				printf("%d: is not an acceptable input\n", inputInt);
				break;
		}
		//exit(1);
		//deleteFirstRow(con);
		//enterTestRow(con);
		MYSQL_RES *result = mysql_store_result(con);
		if(result == NULL)
		{
			error_occured(con);
		}
		MYSQL_ROW row;
		int num_fields = mysql_num_fields(result);
		//printf("%d\n", mysql_num_rows(result));
		//int count = 0;
		while ((row = mysql_fetch_row(result)))
		{
			for(int i = 0; i < num_fields; i++)
			{
				printf("%s ", row[i]);
			}
			printf("\n");
			//count++;
		}
		//printf("Total Columns: %d", count);
		mysql_free_result(result);
	}
	mysql_close(con);
}
