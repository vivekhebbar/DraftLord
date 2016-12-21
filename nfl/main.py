import argparse
import gamelog_ss
import roster_ss
import train

# Currently implemented options for command line argument
# usage
actions = {'pr': roster_ss.populateRoster,
		  'ugl': gamelog_ss.ugl,
		  'pgl': gamelog_ss.pgl,
		  'x': train.xsql
		  }

parser = argparse.ArgumentParser(description='Tell stat-predictor what you want to do.')
parser.add_argument('action', type=str, choices=actions.keys())
args = parser.parse_args()
actions[args.action]()