import sqlite3
from datetime import datetime, timedelta
import numpy as np
from sklearn import utils, linear_model
import csv
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# global variables
data, labels, model = [], [], None

""" This function builds the a 2-dimensional training array, as well as a
1-dimensional label array. Each inner array in the training array consists of
training points the user would like to create a predictive model for.
The label array consists of fantasy points scored by/on the player/date
combination that corresponds to its respective data point in the training array."""
def formDataSet(date=datetime.now()):
	print "Pulling data from gamelog table to create data, labels for training model..."
	global data, labels
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
			data += [dataPoint]
			labels += [dataLabel]
	conn.close()

""" Helper function that extracts a datapoint and a label from a record in the 
gamelog table. Currently, the datapoint is of the form: 
([points, 3pters, rebounds, assists, steals, blocks, turnovers] for [season
average, 5 most recent average, opp team average, home/away average])."""
def createPointandLabel(record, conn):
	if not conn:
		conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	# Instantiate point to empty array and label to fantasy points awarded
	point, label, playerSlug = [], record[-1], record[1]
	############################### FEATURES BELOW ###############################
	# ADD: Average over past year
	year = yearAverage(playerSlug, record[2], c)
	point += year
	# ADD: Average over 5 most recent games for current date
	roll = rollAverage(playerSlug, record[2], c)
	if roll[0] == None:
		roll = year
	point += roll
 	# ADD: Average over season vs. opponent
 	opp = oppAverage(playerSlug, record[3], c)
 	if opp[0] == None:
 		opp = year
 	point += opp
	# ADD: Average over season when home/away
	hoaw = homeAwayAverage(playerSlug, record[4], c)
	if hoaw[0] == None:
		hoaw = year
	point += hoaw
	return point, label

""" Partitions data and labels into training data and test data. Then trains a linear regression on the training data and prints out the accuracy of this regression on the test data. The coefficients of the linear regression are written to coefficients.csv."""
def generateLinearRegressionModel():
	global data, labels, model
	lenData = (len(data) / 10) * 10
	shfl = utils.shuffle(data, labels)
	# Create training and test data, labels to fit and evaluate model
	trainData, trainLabel = shfl[0][:lenData / 10 * 9], shfl[1][:lenData / 10 * 9]
	testData, testLabel = shfl[0][lenData / 10 * 9:], shfl[1][lenData / 10 * 9:]
	model = linear_model.LinearRegression()
	print "Training model on training data..."
	model.fit(trainData, trainLabel)
	print "Training completed."
	# Write coefficients to CSV file if later use is needed
	with open('coeffs.csv','wb') as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow(['Order','Value'])
		for i in range(len(model.coef_)):
			writer.writerow([i+1, model.coef_[i]])
	# Evaluate model's accuracy by comparing predicted test labels vs. true test
	# labels
	score = model.score(testData, testLabel)
	print "Accuracy of model on test data is: " + str(score)

""" Used to construct data point that is compatible with trained model by
the pertinent features from the gamelog data table dct currently requires: intdate, opponent_slug, home/away"""
def createQueryPoint(dct, c):
	if not c:
		conn = sqlite3.connect('nba.db')
		c = conn.cursor()
	# Instantiate point to empty array
	point = []
	############################### FEATURES BELOW ###############################
	# ADD: Average over past year
	year = yearAverage(dct['playerSlug'], dct['date'], c)
	point += year
	# ADD: Average over 5 most recent games for current date
	roll = rollAverage(dct['playerSlug'], dct['date'], c)
	if roll[0] == None:
		roll = year
	point += roll
 	# ADD: Average over season vs. opponent
 	opp = oppAverage(dct['playerSlug'], dct['opponentSlug'], c)
 	if opp[0] == None:
 		opp = year
 	point += opp
	# ADD: Average over season when home/away
	hoaw = homeAwayAverage(dct['playerSlug'], dct['homeAway'], c)
	if hoaw[0] == None:
		hoaw = year
	point += hoaw
	return point

# Helper function for calculating average over year features
def yearAverage(playerSlug, intDate, c):
	sqlStmt = "SELECT AVG(points), AVG(three_pointers_made), AVG(rebounds_total), AVG(assists), AVG(steals), AVG(blocks), AVG(turnovers), AVG(double_double), AVG(triple_double) FROM gamelog WHERE player_slug=\"" + playerSlug
 	sqlStmt += "\" AND date BETWEEN " + str(intDate - 10000) + " AND " + str(intDate)
 	c.execute(sqlStmt)
 	results = c.fetchone()
 	# If there are no results, re-run for non-player average
 	if results[0] == None:
 		sqlStmt = "SELECT AVG(points), AVG(three_pointers_made), AVG(rebounds_total), AVG(assists), AVG(steals), AVG(blocks), AVG(turnovers), AVG(double_double), AVG(triple_double) FROM gamelog WHERE"
 		sqlStmt += " date BETWEEN " + str(intDate - 10000) + " AND " + str(intDate)
 		c.execute(sqlStmt)
 		results = c.fetchone()
 	return list(results)

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
