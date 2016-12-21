from stattlepy import Stattleship
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import constants

# This function builds the gamelog table, which contains record entries
# for all game performances in the past year for all players in the form:
# (player id, slug, date, opponent, home/away, points, 3pters, rebounds, assists,
# steals, blocks, turnovers, double doubles, triple doubles, fantasy points scored)
# The function essentially works by stepping through one year of dates and
# individually calling updateGameLog().
# WARNING: IF YOU WANT TO FULLY REPOPULATE THE GAME LOG, YOU MUST DELETE NBA.DB
# This function will only pull data for a date if it looks into nba.db and 
# verifies that zero records exist for the date. This is in order to save time
# and eliminate redundant expensive calls. It also allows a user to call pgl()
# and quit as many times as wanted without having to re-do progress.
def populateGameLog():
	# Open DB connection and create gamelog table
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS gamelog (player_id TEXT,
		player_slug TEXT, date INTEGER, opponent_slug TEXT, home_away TEXT, points INTEGER, three_pointers_made INTEGER, rebounds_total INTEGER, assists INTEGER, steals INTEGER, blocks INTEGER, turnovers INTEGER, double_double INTEGER, triple_double INTEGER, fantasy_points_scored REAL, PRIMARY KEY(player_slug, date)) ''')
	conn.commit()
	# sql ='SET SESSION max_allowed_packet=500M'
	# c.execute(sql)
	# Starting with today, update the game log for each day and 
	# decrement pointer by one day. End when pointer points to today one 
	# year ago.
	curr, step = datetime.now(), timedelta(days=1)
	for i in range(366):
		# Determine whether there are already records in gamelog on
		# the currDate (curr - i * step) and set equal to recordsExist
		currDate = curr - i * step
		sqlStmt = "SELECT COUNT(*) FROM gamelog WHERE date = " + currDate \
		.strftime('%Y%m%d')
		c.execute(sqlStmt)
		recordsExist = (c.fetchone()[0] != 0)
		# Add records for currDate to gamelog only if they do not exist
		# in gamelog already
		if not recordsExist:
			logRecords = updateGameLog(currDate, conn)
			sqlStmt = "INSERT OR REPLACE INTO gamelog VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
			c.executemany(sqlStmt, logRecords)
			conn.commit()
	# Compute the number of records added to gamelogs
	c.execute("SELECT COUNT(*) FROM gamelog")
	numRecords = c.fetchone()[0]
	print "There are " + str(numRecords) + " records in the gamelog table."
	# Upon looping through all teams, close DBconnection
	conn.close()

# This function adds player logs for games that happened on 
# date - note that this function assumes that there is an existing
# gamelog table that has been populated with populateGameLog(), and
# that this function solely exists to incrementally add recent logs 
# to an existing log table.
def updateGameLog(date=datetime.now(), conn=None):
	# Generate cursor for database connection if c=None
	if not conn:
		conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	# Convert date (datetime) into string 'yyyy-mm-dd'
	strDate = date.strftime('%Y-%m-%d')
	print "================= WORKING ON DATE " + strDate + " ================="
	# Convert date (datetime) into int yyyymmdd for SQLite sorting
	# purposes
	intDate = int(date.strftime('%Y%m%d'))
	# Query stattleship for NFL teams
	newQuery = Stattleship()
	token = newQuery.set_token(constants.accessToken)
	teams = newQuery.ss_get_results(sport='basketball',league='nba',ep='teams')
	# Construct dictionary of all team ids and each matching team slug
	teamIds = {item['id'] : item['slug'] for item in teams[0]['teams']}
	# logRecords will contain all of the date's game logs to be inserted
	# into gamelog at end of for loop
	logRecords = []
	# Loop through all valid pages of game logs for a given day
	for index in range(1, 1000):
		# Query stattleship for a page of date's game logs
		page = newQuery.ss_get_results(sport='basketball',league='nba', \
		ep='game_logs', on=strDate, page=str(index))
		logs = page[0]['game_logs']
		# If there are no more logs to consider, then break
		if not logs:
			break
		players = page[0]['players']
		for curr in range(len(logs)):
			# These are the current log entry and its associated player
			currLog, currPlayer = logs[curr], players[curr]
			# Determine player id, slug, position, and team 
			[id, slug, pos, teamId] = [currPlayer[key] for key \
			in ('id', 'slug', 'position_abbreviation', 'team_id')]
			# Utilize helper function to calculate the player's fantasy points
			# scored in date's game
			[pts, threes, rbs, ass, stl, blk, trn, dbldbl, tpldbl, fpts] =calculateFantasyPoints(currLog)
			record = [id, slug, intDate, teamIds[currLog['opponent_id']], 'home' if currLog['is_home_team'] else 'away', pts, threes, rbs, ass, stl, blk, trn, dbldbl, tpldbl, fpts]
			print "Finished " + record[1] + " " + pos + "."
			logRecords += [record]
	return logRecords


def calculateFantasyPoints(log):
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

ugl = updateGameLog
pgl = populateGameLog