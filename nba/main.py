import argparse
import gamelog_ss
import roster_ss
import train
import today_scrape
import sqlite3
import lineup

# For command line access to SQLite3 table
def sqlInteract():
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	while True:
		try:
			sqlStmt = raw_input("enter SQL code which you would like to run:  ")
			c.execute(sqlStmt)
			result = c.fetchall()
			for line in result:
				print line
		except:
			print "Error!"
			pass

# Assuming that everything is in order, complete tasks required to generate lineup
# for today.
def today():
	gamelog_ss.updateMissing()
	train.formDataSet()
	train.generateModel()
	today_scrape.forToday()
	lineup.setupLineup()
	line = lineup.findLineup()
	return line

# Currently implemented options for command line argument
# usage
actions = {'pr': roster_ss.populateRoster,
		  'ugl': gamelog_ss.updateGameLog,
		  'pgl': gamelog_ss.populateGameLog,
		  'x': sqlInteract,
		  'tr': train.formDataSet,
		  'td': today
		  }

parser = argparse.ArgumentParser(description='Tell Draft Lord what you want to do.')
parser.add_argument('action', type=str, choices=actions.keys())
args = parser.parse_args()
actions[args.action]()