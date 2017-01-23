import sys
import sqlite3
import numpy as np
names, positions, projectedPts, costs, numPlayers, best, bestScore = [], [], [], [], 0, [], 0

def setupLineup():
	global names, positions, projectedPts, costs, numPlayers
	conn = sqlite3.connect('nba.db')
	c = conn.cursor()
	sqlStmt = "SELECT * FROM today ORDER BY projected_fantasy_points desc"
	c.execute(sqlStmt)
	records = np.array(c.fetchall())
	conn.close()
	numPlayers, _ = records.shape
	names, positions, projectedPts, costs = records.T
	projectedPts, costs = projectedPts.astype(float), costs.astype(int) / 100
	print "Done formatting lineup generation data."

memo = {}

def memoize(a, b, c):
	if (a, b, c) not in memo:
		memo[(a, b, c)] = knapsack(a, b, c)
	return memo[(a, b, c)]

# def knapsack(a, b, c):






def findLineup():
	global best, bestScore
	if not numPlayers:
		setupLineup()
	pointGuards, shootGuards, smallForwards, powerForwards, centers = [],[],[],[], []
	switchCase = {'PG': pointGuards, 'SG': shootGuards, 'SF': smallForwards, 'PF': powerForwards, 'C': centers}
	for i in range(numPlayers):
		switchCase[positions[i]].append(i)
	guards, forwards = sorted(pointGuards + shootGuards), sorted(smallForwards + powerForwards)
	utility = sorted(guards + forwards + centers)

	best, bestScore, cost, points, lineup = best, 0, 0, 0, []
	for pg in pointGuards:
		updateProgress(pointGuards.index(pg), len(pointGuards))
		cost += costs[pg]
		points += projectedPts[pg]
		lineup += [pg]

		for sg in shootGuards:
			if cost + costs[sg] >= 50000:
				continue
			cost += costs[sg]
			points += projectedPts[sg]
			lineup += [sg]

			for sf in smallForwards:
				if cost + costs[sf] >= 50000:
					continue
				cost += costs[sf]
				points += projectedPts[sf]
				lineup += [sf]

				for pf in powerForwards:
					if cost + costs[pf] >= 50000:
						continue
					cost += costs[pf]
					points += projectedPts[pf]
					lineup += [pf]

					for cr in centers:
						if cost + costs[cr] >= 50000:
							continue
						cost += costs[cr]
						points += projectedPts[cr]
						lineup += [cr]

						for f in forwards:
							if f in lineup or cost + costs[f] >= 50000:
								continue
							cost += costs[f]
							points += projectedPts[f]
							lineup += [f]

							for g in guards:
								if g in lineup or cost + costs[g] >= 50000:
									continue
								cost += costs[g]
								points += projectedPts[g]
								lineup += [g]

								for u in utility:
									if u in lineup or cost + costs[u] > 50000:
										continue
									cost += costs[u]
									points += projectedPts[u]
									lineup += [u]

									if points > bestScore:
										bestScore = points
										best = [names[index] for index in lineup]

									cost -= costs[u]
									points -= projectedPts[u]
									lineup.pop()

								cost -= costs[g]
								points -= projectedPts[g]
								lineup.pop()

							cost -= costs[f]
							points -= projectedPts[f]
							lineup.pop()

						cost -= costs[cr]
						points -= projectedPts[cr]
						lineup.pop()

					cost -= costs[pf]
					points -= projectedPts[pf]
					lineup.pop()

				cost -= costs[sf]
				points -= projectedPts[sf]
				lineup.pop()

			cost -= costs[sg]
			points -= projectedPts[sg]
			lineup.pop()

		print costs[pg]
		cost -= costs[pg]
		points -= projectedPts[pg]
		lineup.pop()

	print "Search completed. Best lineup:"
	print best, bestScore
	return best

def updateProgress(idx, size):
	progress = idx / float(size)
	block = int(round(30 * progress))
	text = "\rProgress: [{0}] {1}% Complete".format("#"*block + "-"*(30 - block), progress * 100)
	sys.stdout.write(text)
	sys.stdout.flush()

s = setupLineup
f = findLineup