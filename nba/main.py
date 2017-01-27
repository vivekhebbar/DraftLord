import argparse
import gamelog_ss
import roster_ss
import train
import today_scrape
import sqlite3
import lineup

""" For command line access to SQLite3 table. Use A sqlite3 db viewer instead."""
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

""" Complete tasks required to generate a lineup for today. This includes:
	(1) update the missing game logs (assumes the gamelog table is populated up until the last x days)
	(2) form the data set and train the projection model
	(3) regenerate the today table to use in picking a lineup
	(4) set up and pick the optimal lineup from the data provided in the today table"""
def today():
	gamelog_ss.updateMissing()
	train.formDataSet()
	train.generateLinearRegressionModel()
	today_csv.forToday()
	lineup.setupLineup()
	line = lineup.optimize()
	return line

""" Currently implemented options for command line argument
usage"""
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