import sqlite3
import csv

""" Uses DKSalaries.csv file generated by DraftKings website. Each line in the CSV file corresponds to a player, and will be transformed into a record in the today table created/found in nba.db. Each record will contain player_slug, position, projected fantasy points, and cost."""
def forToday():
	# We want to delete all records in today table in nba.db if it exists;
	# otherwise, re-instantiate it
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	c.execute('CREATE TABLE IF NOT EXISTS today (player_slug TEXT, position TEXT, projected_fantasy_points REAL, cost INTEGER, PRIMARY KEY(player_slug));')
	c.execute('DELETE FROM today;')
	records = []
	with open('DKSalaries.csv', 'rb') as csvfile:
		rreader = csv.reader(csvfile)
		for row in rreader:
			if row[0] == 'Position':
				continue
			record = [row[1], row[0].split('/')[0], float(row[4]), int(row[2])] 
			records += [record]

	sqlStmt = "INSERT OR REPLACE INTO today VALUES (?, ?, ?, ?)"
	c.executemany(sqlStmt, records)
	conn.commit()
	conn.close()
