import sqlite3
from datetime import datetime, timedelta
import numpy as np

trainingData, trainingLabels = [], []

# This function builds the a 2-dimensional training array, as well as a
# 1-dimensional label array. Each inner array in the training array consists of
# training points the user would like to create a predictive model for.
# The label array consists of fantasy points scored by/on the player/date
# combination that corresponds to its respective data point in the training array.
def formTrainingSet(date=datetime.now()):
	global trainingData, trainingLabels
	# Open DB connection
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	# Starting with today and dating back one year, for each date fetch all
	# records. For each record, transform it into a data point and a label.
	# After traversing the entire year, return the array of data points and
	# their matching labels.
	curr, step = date, timedelta(days=1)
	for i in range(366):
		currDate = curr - i * step
		strDate = currDate.strftime('%Y-%m-%d')
		print "================= WORKING ON DATE " + strDate + " ================="
		# Determine whether there are records in the gamelog for the current date.
		# If there are none, skip this date.
		sqlStmt = "SELECT COUNT(*) FROM gamelog WHERE date = " + currDate.strftime('%Y%m%d')
		c.execute(sqlStmt)
		if (c.fetchone()[0] == 0):
			continue
		# Pull all records for the current date from gamelog
		sqlStmt = "SELECT * FROM gamelog WHERE date = " + currDate.strftime('%Y%m%d')
		c.execute(sqlStmt)
		records = c.fetchall()
		# for each record pulled, create a datapoint and a label using the helper
		# function. Then add the datapoint and the label to the existing lists
		for record in records:
			dataPoint, dataLabel = createPointandLabel(record, conn)
			trainingData += [dataPoint]
			trainingLabels += [dataLabel]

	print len(trainingData), len(trainingData[0]), len(trainingLabels)

# Helper function that extracts a datapoint and a label from a record in the 
# gamelog table. Currently, the datapoint is of the form: 
# ([points, 3pters, rebounds, assists, steals, blocks, turnovers] for [season
# average, 5 most recent average, opp team average, home/away average]).
def createPointandLabel(record, conn):
	if not conn:
		conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	# Instantiate point to empty array and label to fantasy points awarded
	point, label, playerSlug = [], record[-1], record[1]
	############################### FEATURES BELOW ###############################
	# ADD: Average over past year
	point += yearAverage(playerSlug, record[2], c)
	# ADD: Average over 5 most recent games for current date
	point += rollAverage(playerSlug, record[2], c)
 	# ADD: Average over season vs. opponent
 	point += oppAverage(playerSlug, record[3], c)
	# ADD: Average over season when home/away
	point += homeAwayAverage(playerSlug, record[4], c)
	return point, label

# Used to construct data point that is compatible with trained model by
# the pertinent features from the gamelog data table
def createQueryPoint():
	return None

# Helper function for calculating average over year features
def yearAverage(playerSlug, intDate, c):
	sqlStmt = "SELECT AVG(points), AVG(three_pointers_made), AVG(rebounds_total), AVG(assists), AVG(steals), AVG(blocks), AVG(turnovers), AVG(double_double), AVG(triple_double) FROM gamelog WHERE player_slug=\"" + playerSlug
 	sqlStmt += "\" AND date BETWEEN " + str(intDate - 10000) + " AND " + str(intDate)
 	c.execute(sqlStmt)
 	return list(c.fetchone())

# Helper function for calculating rolling average features
def rollAverage(playerSlug, intDate, c):
	sqlStmt = "SELECT AVG(points), AVG(three_pointers_made), AVG(rebounds_total), AVG(assists), AVG(steals), AVG(blocks), AVG(turnovers), AVG(double_double), AVG(triple_double) FROM gamelog WHERE player_slug=\"" + playerSlug
 	sqlStmt += "\" AND date  <=" + str(intDate) + " ORDER BY date DESC LIMIT 5"
	c.execute(sqlStmt)
 	return list(c.fetchone())

# Helper function for calculating opponent-based features
def oppAverage(playerSlug, oppSlug, c):
	sqlStmt = "SELECT AVG(points), AVG(three_pointers_made), AVG(rebounds_total), AVG(assists), AVG(steals), AVG(blocks), AVG(turnovers), AVG(double_double), AVG(triple_double) FROM gamelog WHERE player_slug=\"" + playerSlug
 	sqlStmt += "\" AND opponent_slug = \"" + oppSlug + "\""
	c.execute(sqlStmt)
 	return list(c.fetchone())

# Helper function for calculating home vs away features
def homeAwayAverage(playerSlug, homeAway, c):
	sqlStmt = "SELECT AVG(points), AVG(three_pointers_made), AVG(rebounds_total), AVG(assists), AVG(steals), AVG(blocks), AVG(turnovers), AVG(double_double), AVG(triple_double) FROM gamelog WHERE player_slug=\"" + playerSlug
 	sqlStmt += "\" AND home_away = \"" + homeAway + "\""
 	c.execute(sqlStmt)
 	return list(c.fetchone())
