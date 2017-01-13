from stattlepy import Stattleship
from bs4 import BeautifulSoup
import sqlite3
import constants
import requests
from datetime import datetime, timedelta, date



"""
Should populate a table that contains (teamslug, date) as a primary key, and 
average points scored against that team up to that point in the season
"""
def populateDefensiveTeamStats():
	
	#Create table to store defensive statistics
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS defense (team_slug TEXT, date INTEGER, points REAL, PRIMARY KEY(team_slug, date))''')
	conn.commit()

	#Create view containing position with opposing team and fantasty points 
	sqlStmt = '''CREATE VIEW IF NOT EXISTS gamelog_defense AS SELECT gamelog.player_slug, gamelog.opponent_slug,'''
	sqlStmt+= '''gamelog.fantasy_points_scored, roster.position, gamelog.date FROM gamelog INNER JOIN roster ON gamelog.player_slug = roster.player_slug;'''
	c.execute(sqlStmt)

	#For each team, for each position, for each date 
	new_query = Stattleship()
	token = new_query.set_token(constants.accessToken)
	teams = new_query.ss_get_results(sport='basketball',league='nba',ep='teams')
	team_slugs = {item['slug'] : item['id'] for item in teams[0]['teams']}

	start_of_season = date(2016, 10, 24)
	iterable_days = (date.today() - start_of_season).days
	print("Number of days since start of season is :" + str(iterable_days))
	curr, step = datetime.now(), timedelta(days=1)

	print(team_slugs.keys())
	for team in team_slugs.keys():
		for pos in ['C','PF','SF','SG','PG']:
			for i in iterable_days:
				currDate = (curr - i * step).strftime('%Y%m%d')
				avgPoints = getAveragePointsAgainst(team, currDate, pos)
				#Insert into defense table 
	



"""
Returns the average points scored against a team by a position up to the point 
of the date in the season 
"""
def getAveragePointsAgainst(team_slug, date, position):
	#Create sql to actually return something
	return 0.0


populateDefensiveTeamStats()