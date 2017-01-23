import gamelog_ss
import roster_ss
import train
import sqlite3
import csv
import constants
from bs4 import BeautifulSoup
from datetime import datetime
import requests
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

def forToday():
	print "Pulling all relevant data for today's games and players."
	# We want to delete all records in today table in nba.db if it exists;
	# otherwise, re-instantiate it
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	c.execute('CREATE TABLE IF NOT EXISTS today (player_slug TEXT, position TEXT, projected_fantasy_points REAL, cost INTEGER, PRIMARY KEY(player_slug));')
	c.execute('DELETE FROM today;')
	# Extract the list of games being played today. If there are no games today,
	# exit. If there are, denote whether the participating teams are home or away
	# in the teams dictionary.
	r = requests.get(constants.todayURL)
	soup = BeautifulSoup(r.text)
	games = soup.find_all(attrs={"class":"rwo-game-game"})
	if not games:
		print "No games being played today."
		return
	teams = {}
	for game in games:
		visit = game['data-visitteam'].replace(' ','').replace('@','').lower()
		if visit in constants.swapDict:
			visit = constants.swapDict[visit]
		home = game['data-hometeam'].replace(' ','').replace('@','').lower()
		if home in constants.swapDict:
			home = constants.swapDict[home]
		teams[visit] = "away"
		teams[home] = "home"
	# Extract the list of players playing today
	players = soup.find("tbody", attrs={"id": "players"}).find_all("tr")
	# Loop through each player and extract the necessary information to add
	# the player's record in the today table.
	records = []
	for player in players:
		# Extract player name
		name = player.find("a", attrs={"class": "dplayer-link"}).text.split(" ")
		first, last = name[0].replace("'", '').replace('-',''), name[1].replace("'",'').replace('-','')
		# Look up first, last in roster table; retrieve player slug and position
		sqlStmt = 'SELECT player_slug from roster where first like "' + first + '%" and last like "' + last + '%";'
		c.execute(sqlStmt)
		result = c.fetchone()
		if not result:
			print first, last, "did not have a record."
			continue
		playerSlug  = result[0]
		# Extract player position
		position = player.find("td", attrs={"class": "rwo-pos align-c"}).text
		# Extract player cost
		cost = int(player.find("td", attrs={"class": "rwo-salary"})['data-salary'].replace(',', ''))
		############################## FEATURES BELOW ##############################
		dct = {'playerSlug': playerSlug}
		# EXTRACT: Today's date
		dct['date'] = int(datetime.now().strftime('%Y%m%d'))
		# EXTRACT: Opponent's slug
		opponent = player.find("td", attrs={"class": "rwo-opp align-c"})['data-opp'].replace('@', '').replace(' ', '').lower()
		if opponent in constants.swapDict:
			opponent = constants.swapDict[opponent]
		dct['opponentSlug'] = 'nba-' + opponent
	 	# EXTRACT: Home or away
	 	dct['homeAway'] = teams[opponent]
	 	# Transform dct into a query point compatible with train.model
	 	queryPoint = train.createQueryPoint(dct, c)
	 	# Use train.model to predict fantasy points using queryPoint
	 	projectedPoints = train.model.predict(queryPoint)[0]
	 	# print dct.values(), projectedPoints, cost
	 	# Add record for current player to the records to be inserted into the 
	 	# today table
	 	record = [playerSlug, position, projectedPoints, cost]
	 	print record
	 	records += [record]
	sqlStmt = "INSERT OR REPLACE INTO today VALUES (?, ?, ?, ?)"
	c.executemany(sqlStmt, records)
	conn.commit()
	conn.close()