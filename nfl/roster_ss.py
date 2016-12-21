from stattlepy import Stattleship
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import constants

# This function builds the roster table, which contains record entries
# for all current players of all teams in the form:
# (first name, last name, team slug, position, player slug, player id)
def populateRoster():
	# Query stattleship for NFL teams
	newQuery = Stattleship()
	token = newQuery.set_token(constants.accessToken)
	teams = newQuery.ss_get_results(sport='football',league='nfl',ep='teams')
	# Construct dictionary of all team slugs and each matching team id
	teamSlugs = {item['slug'] : item['id'] for item in teams[0]['teams']}
	# Open DB connection and create roster table
	conn = sqlite3.connect('nfl.db')
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS roster (first TEXT, last TEXT,
		team TEXT, position TEXT, player_slug TEXT, player_id TEXT PRIMARY KEY)''')
	conn.commit()
	# Loop through each team in teamSlugs
	for team in teamSlugs:
		# playerRecords will contain all of the team's player records to be inserted
		# into roster at end of for loop
		playerRecords = []
		# Want to look at all valid pages of players for a given team
		for index in range(1, 30):
			# Query stattleship for a page of team's roster
			page = newQuery.ss_get_results(sport='football',league='nfl', \
			ep='players', team_id=team, season_id=constants.currentSeason, page=str(index))
			pageOfPlayers = page[0]['players']
			# If there are no more players to consider, move to next team
			if not pageOfPlayers:
				break
			# Loop through each player on page
			for player in pageOfPlayers:
				# If player should be considered, add his record to be inserted
				if player['position_abbreviation'] in offensivePositions:
					record = (player['first_name'], player['last_name'], \
						team, player['position_abbreviation'], player['slug'], \
						player['id'])
					playerRecords += [record]
		# Create one record for team's D/ST
		defense = (team, 'D/ST', team, 'D/ST', team, teamSlugs[team])
		playerRecords += [defense]
		# Insert team's player records, commit
		sqlStmt = "INSERT OR REPLACE INTO roster VALUES (?, ?, ?, ?, ?, ?)"
		c.executemany(sqlStmt, playerRecords)
		conn.commit()
		print "Done with team " + team + ". "
	# Compute the number of records added within for loops
	c.execute("SELECT COUNT(*) FROM roster")
	numRecords = c.fetchone()[0]
	print "There are " + str(numRecords) + " records in the roster table."
	# Upon looping through all teams, close DBconnection
	conn.close()