from stattlepy import Stattleship
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import constants

# This function builds the gamelog table, which contains record entries
# for all game performances in the past year for all players in the form:
# (player id, , , , , )
# The function essentially works by stepping through one year of dates and
# individually calling updateGameLog().
# WARNING: IF YOU WANT TO FULLY REPOPULATE THE GAME LOG, YOU MUST DELETE NFL.DB
# This function will only pull data for a date if it looks into nfl.db and 
# verifies that zero records exist for the date. This is in order to save time
# and eliminate redundant expensive calls. It also allows a user to call pgl()
# and quit as many times as wanted without having to re-do progress.
def populateGameLog():
	# Open DB connection and create gamelog table
	conn = sqlite3.connect('nfl.db')
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS gamelog (player_id TEXT,
		player_slug TEXT, date INTEGER, opponent_slug TEXT, home_away TEXT,
		points_scored REAL, PRIMARY KEY(player_slug, date)) ''')
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
			sqlStmt = "INSERT OR REPLACE INTO gamelog VALUES (?, ?, ?, ?, ?, ?)"
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
		conn = sqlite3.connect('nfl.db')
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
	teams = newQuery.ss_get_results(sport='football',league='nfl',ep='teams')
	# Construct dictionary of all team ids and each matching team slug
	teamIds = {item['id'] : item['slug'] for item in teams[0]['teams']}
	# Construct dictionary of all team slugs and each matching team id
	teamSlugs = {item['slug'] : item['id'] for item in teams[0]['teams']}
	# logRecords will contain all of the date's game logs to be inserted
	# into gamelog at end of for loop
	logRecords = []
	# One D/ST record is entered into gamelog for each team that plays
	# on date. At the end of the for loop, each entry in 
	# defensiveTeams is added to logRecords before it is inserted
	# into gamelog
	defensiveTeams = {}
	# Loop through all valid pages of game logs for a given day
	for index in range(1, 1000):
		# Query stattleship for a page of date's game logs
		page = newQuery.ss_get_results(sport='football',league='nfl', \
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
			# For fantasy point calculation purposes, we must determine
			# whether the player is an offensive player; if not, the player's
			# points must be summed with all other defensive players'
			# contributions
			isOffensive = (pos in offensivePositions)
			# Utilize helper function to calculate the player's fantasy points
			# scored in date's game, or their contribution to the team's D/ST
			# fantasy point total
			currPoints = calculateFantasyPoints(currLog, isOffensive)
			# If the player is not offensive, add his contributions to the
			# running total of his team's defensive fantasy point total.
			# Checking whether teamId is in teamIds is to prevent errors
			if not isOffensive and teamId in teamIds:
				# If teamId is not already stored in defensiveTeams,
				# instantiate the dictionary for teamId and populate its
				# opponent and home_away entries using current log
				if teamId not in defensiveTeams:
					defensiveTeams[teamId] = {'points': 0, 
					'opponent': teamIds[currLog['opponent_id']], 
					'home_away': 'home' if currLog['is_home_team'] else 'away'}
				defensiveTeams[teamId]['points'] += currPoints
			# If the player is offensive, add his log record to logRecords
			else:
				record = [id, slug, intDate, teamIds[currLog['opponent_id']], \
				'home' if currLog['is_home_team'] else 'away', currPoints]
				print "Finished " + record[1] + " " + pos + "."
				logRecords += [record]
	# Now loop through each entry in defensiveTeams and add a record to 
	# logRecords for each D/ST for each team for each game played on date
	for dst in defensiveTeams:
		defense = defensiveTeams[dst]
		record = [dst, teamIds[dst], intDate, defense['opponent'], \
		defense['home_away'], defense['points']]
		print "Finished " + record[1] + "."
		logRecords += [record]
	return logRecords

def calculateFantasyPoints(log, isOffensive):
	if isOffensive:
		xVector = np.array([
			log['passes_touchdowns'],
			log['passes_yards_gross'],
			int(log['passes_yards_gross'] >= 300),
			log['interceptions_total'],
			log['rushes_yards'],
			log['total_touchdowns'] - log['passes_touchdowns'],
			int(log['rushes_yards'] >= 100),
			log['receptions_yards'],
			log['receptions_total'],
			int(log['receptions_yards'] >= 100),
			log['fumbles_lost'],
			log['receiving_2pt_conversions_succeeded'] + \
			log['passing_2pt_conversions_succeeded'] + \
			log['rushing_2pt_conversions_succeeded']])
		wVector = np.array([4., .04, 3., -1., 0.1, 6., 3., \
			0.1, 1., 3., -1., 2.])
		return np.dot(xVector, wVector)
	else:
		oppScore = log['opponent_score']
		xVector = np.array([
			log['sacks_total'],
			log['interceptions_total'],
			log['fumbles_opposing_recovered'],
			log['kickoff_return_touchdowns'],
			log['punt_return_touchdowns'],
			#blocked punt or fg return td
			log['interceptions_touchdown'],
			log['safeties'],
			log['field_goals_blocked'],
			log['extra_points_made'],
			int(oppScore == 0),
			int(oppScore >= 1 and oppScore <= 6),
			int(oppScore >= 7 and oppScore <= 13),
			int(oppScore >= 14 and oppScore <= 20),
			int(oppScore >= 21 and oppScore <= 27),
			int(oppScore >= 28 and oppScore <= 34),
			int(oppScore >= 35)])
		wVector = np.array([1., 2., 2., 6., 6., 6., 2., 2., \
			2., 10., 7., 4., 1., 0., -1., -4.])
		return np.dot(xVector, wVector)

ugl = updateGameLog
pgl = populateGameLog