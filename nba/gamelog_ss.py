from stattlepy import Stattleship
import sqlite3
from datetime import datetime, timedelta, date
import numpy as np
import constants

teamIds = None

"""
This function builds the gamelog table in nfl.db, which contains record entries for 
all game performances during the past season in the form: 
(player id, slug, date, opponent, home/away, points, three pointers, rebounds, assists, 
	steals, blocks, turnovers, double doubles, triple doubles, fantasy points)
This function builds the gamelog table, which contains record entries
for all game performances in the past year for all players in the form:
(player id, slug, date, opponent, home/away, points, 3pters, rebounds, assists,
steals, blocks, turnovers, double doubles, triple doubles, fantasy points scored)
WARNING: IF YOU WANT TO FULLY REPOPULATE THE GAME LOG, YOU MUST DELETE NBA.DB
"""
def populateGameLog():
	# Open DB connection and create gamelog table
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS gamelog (player_id TEXT,
		player_slug TEXT, date INTEGER, opponent_slug TEXT, home_away TEXT, points INTEGER, three_pointers_made INTEGER, rebounds_total INTEGER, assists INTEGER, steals INTEGER, blocks INTEGER, turnovers INTEGER, double_double INTEGER, triple_double INTEGER, fantasy_points_scored REAL, PRIMARY KEY(player_slug, date)) ''')
	conn.commit()

	# Starting with today and walking to beginning of the season, update the game log table for all
	# available games. Only populate for dates that are not currently in the table. 
	start_of_season = date(2016, 10, 24)
	iterable_days = (date.today() - start_of_season).days
	print("Number of days since start of season is :" + str(iterable_days))
	curr, step = datetime.now(), timedelta(days=1)
	for i in range(366):
		currDate = curr - i * step
		sqlStmt = "SELECT COUNT(*) FROM gamelog WHERE date = " + currDate \
		.strftime('%Y%m%d')
		c.execute(sqlStmt)
		recordsExist =  c.fetchone()[0]
		# Add records for currDate to gamelog only if they do not exist
		if not recordsExist:
			updateGameLog(currDate, conn)

	c.execute("SELECT COUNT(*) FROM gamelog")
	numRecords = c.fetchone()[0]
	print "There are " + str(numRecords) + " records in the gamelog table."
	# Upon looping through all teams, close DBconnection
	conn.close()

"""
Updates the gamelog table to include all missing records from today until the latest
day present in the gamelog table. 
"""
def updateMissing():
	print "Updating missing records in gamelog table..."
	
	# Open DB connection and create gamelog table
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	
	#Iterate backwards until date found in gamelog table 
	curr, step = datetime.now(), timedelta(days=1)
	for i in range(366):
		currDate = curr - i * step
		sqlStmt = "SELECT COUNT(*) FROM gamelog WHERE date = " + currDate \
		.strftime('%Y%m%d')
		c.execute(sqlStmt)
		recordsExist =  c.fetchone()[0]
		# If there are records for the current day, break out of for loop 
		if recordsExist:
			break
		updateGameLog(currDate, conn)
	c.execute("SELECT COUNT(*) FROM gamelog")
	numRecords = c.fetchone()[0]
	print "There are " + str(numRecords) + " records in the gamelog table."
	# Upon looping through all teams, close DBconnection
	conn.close()

"""
Updatess the game log to include games that occured on the date parameter. 
Default parameter is the current date. This function assumes that the gamelog
table already exists. 
"""
def updateGameLog(date=datetime.now(), conn=None):
	global teamIds
	# Generate cursor for database connection if c=None
	if not conn:
		conn = sqlite3.connect('nba.db')
	c = conn.cursor()

	#Manipulate date string and query Stattleship to create team IDs
	strDate = date.strftime('%Y-%m-%d')
	print "================= WORKING ON DATE " + strDate + " ================="
	intDate = int(date.strftime('%Y%m%d'))
	newQuery = Stattleship()
	token = newQuery.set_token(constants.accessToken)
	if not teamIds:
		teams = newQuery.ss_get_results(sport='basketball',league='nba',ep='teams')
		teamIds = {item['id'] : item['slug'] for item in teams[0]['teams']}
	
	# Loop through all valid pages of game logs for a given day, add the game logs to the 
	# game log table 
	logRecords = []
	for index in range(1, 1000):
		page = newQuery.ss_get_results(sport='basketball',league='nba', \
		ep='game_logs', on=strDate, page=str(index))
		logs = page[0]['game_logs']
		if not logs:
			break
		players = page[0]['players']
		for curr in range(len(logs)):
			# These are the current log entry and its associated player
			currLog, currPlayer = logs[curr], players[curr]
			# Determine player id, slug, position, and team 
			[id, slug, pos, teamId] = [currPlayer[key] for key \
			in ('id', 'slug', 'position_abbreviation', 'team_id')]
			# Utilize helper function to extract player stats and scored fantasy
			# points for game date's game. VARIABLES EXPLICITLY ENUMERATED HERE
			# TO PREVENT FORGETTING WHICH STATS ARE BEING USED.
			[pts, threes, rbs, ast, stl, blk, trn, dbldbl, tpldbl, fpts] =extractPlayerStats(currLog)
			record = [id, slug, intDate, teamIds[currLog['opponent_id']], 'home' if currLog['is_home_team'] else 'away', pts, threes, rbs, ast, stl, blk, trn, dbldbl, tpldbl, fpts]
			print "Finished " + record[1] + " " + pos + "."
			logRecords += [record]
	sqlStmt = "INSERT OR REPLACE INTO gamelog VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
	c.executemany(sqlStmt, logRecords)
	conn.commit()

# Helper function that extracts desired stats from log record; will also calculate
# the fantasy points the player was awarded from the game corresponding to the log
# record. Currently, stats used are:
# PTS, 3PT, RB, AST, STL, BLK, TO, 2-2, 3-2, (fantasy points)
def extractPlayerStats(log):
	xVector = np.array([
		int(log['points']), 
		log['three_pointers_made'], 
		log['rebounds_total'], 
		log['assists'], 
		log['steals'], 
		log['blocks'], 
		log['turnovers'],
		int(bool(log['double_double'])), 
		int(bool(log['triple_double']))
		])
	wVector = np.array([1, 0.5, 1.25, 1.5, 2, 2, -0.5, 1.5, 3])
	return np.append(xVector, np.dot(xVector, wVector))
