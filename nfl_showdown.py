#import PuLP modeler  functions
from pulp import *

#import csv library to read CSV file from DraftKings salary data
import csv


def offense_defense_breakdown (position):
    #identify position of players as either offense or defense
    if position in ['QB', 'TE', 'WR', 'RB']:
        return 'offense'
    else:
        return 'defense'


def load_player_data():
    #open player data file and load into list of players, with each player built as a dictionary and returns list
    
    #create player list
    players = []
    
    with open("DKSalaries.csv") as csvfile:
        readCSV = csv.reader(csvfile, delimiter = ",")

        #move to next line, skip the file header
        next(readCSV)

        #iterate through each row in the player file
        for row in readCSV:
            #create player dictionary
            player = {
                                'position' : row[0],
                                'position_type' : offense_defense_breakdown(row[0]),
                                'player_name' : row[1].replace(' ', '_'),
                                'player_salary' : float(row[2]),
                                'player_avg_pts_game' : float(row[4]),
                                'player_team' : row[5],
                                'rushing_attempts' : float(row[6]),
                                'rushing_yards' : float(row[7]),
                                'yards_per_rushing_attempts' : float(row[8])
                          }

            #add each player to players list
            players.append(player)

        return players

    

#get the list of players for Superbowl 52
players = load_player_data()

#print players

#define maximization function to maximize point production for a player lineup.
maximization_function = 0

#define constraints for optimization problem
total_cost_player_lineup = 0
total_offensive_players = 0
total_defensive_players = 0

# define constraint for running backs
total_running_back_players = 0
total_under_performing_running_back_players = 0


for player in players:
    #define linear programming variable for each player.  solving this optimization problem requires a selction of a player on the team.  Either they are on the team (integrer value of 1) or they are not on the team (integer value of 0)
    player_lp_variable = LpVariable(str(player['player_name']), 0, 1, LpInteger)

    #maximizing player function = sum of (player * average points per game) for all players in lineup
    maximization_function += player_lp_variable * player['player_avg_pts_game']

    #total cost of player lineup function = sum of (player * player's salary) for all players in lineup.  need this later set constraint for optimization problem, total player lineup cost must be less than $50,000
    total_cost_player_lineup += player_lp_variable * player['player_salary']

    #check to see if this player is offensive player, if so, add the player represented by the linear programming varible to the contraint function for offensive players, or else add them to constraint function for defensive players.  There are only two player types in this optimziation problem, offense or defense
    if player['position_type'] == 'offense':
        total_offensive_players += player_lp_variable
    else:
        total_defensive_players += player_lp_variable

    #check to see if this player is a running back, if so, add the player represented by the linear programming variable to the constraint function for running back players.
    if player['position'] ==  'RB':                 
        total_running_back_players += player_lp_variable

        #check for unproductive running back and add to constraint function.  We don't want these running backs in our lineup
        if player['rushing_attempts'] < 100 or player['yards_per_rushing_attempts'] < 4:
            total_under_performing_running_back_players += player_lp_variable

#set the objective function as a maximization problem
optimization_problem = LpProblem("The Superbowl fantasy lineup optimization problem", LpMaximize)

#add the objective function to the problem.  This is the first thing to do to setup the PuLP problem.   In this case it is thefunction for total point production of the lineup
optimization_problem += maximization_function, "total points for the player lineup"

#add the salary constraint, total lineup salary must be less than $50,000
optimization_problem += total_cost_player_lineup <= 50000, 'salary constraint'

#add the constraint that there must be 4 offensive players
optimization_problem += total_offensive_players == 4, "offensive player constraint"

#add the contraint that there must be 2 defensive players
optimization_problem += total_defensive_players == 2, "defensive player constraint"

#add the constraint that there must be at least two running backs in the lineup
optimization_problem += total_running_back_players >= 2, "running back player constraint"

#add the constraint that the total count of under performing running backs is not in our line up = 0.
optimization_problem += total_under_performing_running_back_players == 0, "under performing running back player constraint"

#write the problem to a file for later inspection
optimization_problem.writeLP("SuperbowlFantasy.lp")

#solve the optimzaton problem
optimization_problem.solve()

#calculate total salary for players selected in lineup
total_lineup_salary = 0


print "-------------------------------------------------------------------------------"
print "Optimized player lineup solved for maximum point production"
print "-------------------------------------------------------------------------------"

#display all the information for players selected from the solver
for player_selected in optimization_problem.variables():
    if player_selected.varValue ==1:
        
        #player was selected for lineup, obtain individual player info for display
        for player in players:
            if player_selected.name == player['player_name']:
                total_lineup_salary += player['player_salary']
                print (player_selected.name, player['position_type'], player['position'],'salary=',player['player_salary'], 'team=' + player['player_team'])

print "\nThe total point production from this lineup is:" , value(optimization_problem.objective)
print "The total salary for this lineup is: $", total_lineup_salary
