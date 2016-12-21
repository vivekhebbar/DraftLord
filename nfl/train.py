import sqlite3
from datetime import datetime, timedelta
import numpy as np

# For command line access to SQLite3 table
def sqlInteract():
	conn = sqlite3.connect('nfl.db')
	c = conn.cursor()
	while True:
		sqlStmt = raw_input("enter SQL code which you would like to run:  ")
		c.execute(sqlStmt)
		result = c.fetchall()
		print result

xsql = sqlInteract