import numpy as np
import sqlite3
import heapq
import sys

names, positions, projectedPts, costs, numPlayers = [], [], [], [], 0

""" Create lists for names, positions, projected points, and costs where list[i] corresponds to the entry for player with name names[i]. These lists will be used to compute the optimal lineup."""
def setupLineup():
	global names, positions, projectedPts, costs, numPlayers
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	sqlStmt = "SELECT * FROM today ORDER BY projected_fantasy_points desc, cost desc"
	c.execute(sqlStmt)
	records = np.array(c.fetchall())
	conn.close()
	numPlayers, _ = records.shape
	names, positions, projectedPts, costs = records.T
	projectedPts, costs = projectedPts.astype(float), (costs.astype(int) / 100).astype(int)

""" Find the initial lineup possible and add it on the heap at value alpha * cost - projectedPts. While the heap is not empty, pop a lineup off of the heap and check to make sure it has not been visited. If the lineup cost exceeds the budget, simply generate the neighbors of this lineup and add them onto the heap at a value alpha * cost - projectedPts. If the lineup is under budget, return the lineup."""
def optimize():
	lineups, init = [], findInitial()
	lineupPts, lineupCost = sum([projectedPts[i] for i in init.values()]), sum([costs[i] for i in init.values()])
	heapq.heappush(lineups, (.15 * lineupCost - lineupPts, init, lineupPts, lineupCost))
	best, bestScore = None, 0
	visited = set()
	ctr = 0
	while lineups:
		_, lineup, score, spent = heapq.heappop(lineups)
		visitCheck = str(sorted(lineup.values()))
		if visitCheck in visited:
			continue
		ctr += 1
		visited.add(visitCheck)
		lineupStr = ' '.join([pos + ':' + '0' * (3 - len(str(lineup[pos]))) + str(lineup[pos]) for pos in sorted(lineup.keys())])
		sys.stdout.write('\rTRY #' + '0' * (8 - len(str(ctr))) + str(ctr) + ',  $' + str(spent) + ', ' + lineupStr + ', ' + str(int(score)))
		sys.stdout.flush()
		if spent <= 500:
			if score > bestScore:
				bestScore, best = score, {ps: lineup[ps] for ps in lineup}
				print "NEW BEST", score, lineup, [names[i] for i in best.values()]
		else:
			neighbors = generateNeighbors(lineup)
			for nb in neighbors:
				if not str(sorted(nb.values())) in visited:
					nbCost, nbPts = sum([costs[i] for i in nb.values()]), sum([projectedPts[i] for i in nb.values()])
					heapq.heappush(lineups, (.15 * nbCost - nbPts, nb, nbPts, nbCost))

	print best, sum([projectedPts[i] for i in best.values()]), [names[i] for i in best.values()], sum([costs[i] for i in best.values()]), [positions[i] for i in best.values()]
	return best

""" Find the initial lineup to start searching from by walking down the positions list until all 8 positions have been filled subject to constraints."""
def findInitial():
	result = {}
	# find SG, PG, SF, PF, C
	for pos in ['SG', 'PG', 'SF', 'PF', 'C']:
		for i in range(numPlayers):
			if positions[i] == pos:
				result[pos] = i
				break
	# find G
	for i in range(numPlayers):
		if (positions[i] == 'SG' and result['SG'] != i) or (positions[i] == 'PG' and result['PG'] != i):
			result['G'] = i
			break
	# find F
	for i in range(numPlayers):
		if (positions[i] == 'SF' and result['SF'] != i) or (positions[i] == 'PF' and result['PF'] != i):
			result['F'] = i
			break
	# find U
	for i in range(numPlayers):
		if i not in result.values():
			result['U'] = i
			break
	return result

""" Generate the eigh neighboring lineups from the given lineup by walking down the positions list until a neighboring move for each position has been found"""
def generateNeighbors(lineup):
	results = []
	# generate neighbors for SG, PG, SF, PF, C
	for pos in ['SG', 'PG', 'SF', 'PF', 'C']:
		dictToAdd = {ps:lineup[ps] for ps in lineup}
		for i in range(lineup[pos] + 1, numPlayers):
			if positions[i] == pos and i not in lineup.values():
				dictToAdd[pos] = i
				results += [dictToAdd]
				break
	# generate neighbor for G
	dictToAdd = {ps:lineup[ps] for ps in lineup}
	for i in range(lineup['G'] + 1, numPlayers):
		if (positions[i] == 'SG' or positions[i] == 'PG') and i not in lineup.values():
			dictToAdd['G'] = i
			results += [dictToAdd]
			break
	# generate neighbor for F
	dictToAdd = {ps:lineup[ps] for ps in lineup}
	for i in range(lineup['F'] + 1, numPlayers):
		if (positions[i] == 'SF' or positions[i] == 'PF') and i not in lineup.values():
			dictToAdd['F'] = i
			results += [dictToAdd]
			break
	# generate neighbor for U
	dictToAdd = {ps:lineup[ps] for ps in lineup}
	for i in range(lineup['U'] + 1, numPlayers):
		if i not in lineup.values():
			dictToAdd['U'] = i
			results += [dictToAdd]
			break
	return results

