import gamelog_ss
import roster_ss
import train
import sqlite3
import csv
import constants
from bs4 import BeautifulSoup
from datetime import datetime
import requests

def forToday():
	print "Pulling all relevant data for today's games and players."
	# We want to delete the today table in nba.db if it exists, and then re-
	# instantiate it
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	c.execute('DROP TABLE IF EXISTS today;')
	c.execute('CREATE TABLE today (player_slug TEXT, position TEXT, projected_fantasy_points REAL, cost INTEGER, PRIMARY KEY(player_slug));')
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
		first, last = name[0], name[1]
		# Look up first, last in roster table; retrieve player slug and position
		sqlStmt = 'SELECT player_slug, position from roster where first like "' + first + '%" and last like "' + last + '%";'
		c.execute(sqlStmt)
		result = c.fetchone()
		if not result:
			print first, last, "did not have a record."
			continue
		playerSlug, position = result
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
	 	print playerSlug, projectedPoints, cost
	 	# Add record for current player to the records to be inserted into the 
	 	# today table
	 	records += [[playerSlug, position, projectedPoints, cost]]
	sqlStmt = "INSERT OR REPLACE INTO today VALUES (?, ?, ?, ?)"
	c.executemany(sqlStmt, records)
	conn.commit()