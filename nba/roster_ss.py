from stattlepy import Stattleship
import sqlite3
import constants


"""
This function builds the roster table, which conatins record entries for all current
players in the form: 
(first name, last name, team slug, position, player slug, player id)
"""
def populateRoster():
	# Query stattleship for NBA teams and create dictionary of team slugs: team ids
	newQuery = Stattleship()
	token = newQuery.set_token(constants.accessToken)
	teams = newQuery.ss_get_results(sport='basketball',league='nba',ep='teams')
	teamSlugs = {item['slug'] : item['id'] for item in teams[0]['teams']}
	
	# Open DB connection and create roster table
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS roster (first TEXT, last TEXT,
		team TEXT, position TEXT, player_slug TEXT, player_id TEXT PRIMARY KEY)''')
	conn.commit()

	# Loop through teams, using each team slug to query for players 
	for team in teamSlugs:
		playerRecords = []
		for index in range(1, 30):
			page = newQuery.ss_get_results(sport='basketball',league='nba', ep='players', team_id=team, season_id=constants.currentSeason, page=str(index))
			pageOfPlayers = page[0]['players']
			if not pageOfPlayers:
				break
			for player in pageOfPlayers:
				record = (player['first_name'], player['last_name'], team, player['position_abbreviation'], player['slug'], player['id'])
				playerRecords += [record]
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