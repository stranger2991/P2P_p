#!/usr/bin/python
############################################################################################################################################
#Packages - (Igraph,Gambit,gdflib)
#Multi_IDS
#Non_trivial solution (Putting IDS on the vertices except the target nodes) 
############################################################################################################################################
import copy
import random
from igraph import *
from gambit import *
import gambit.nash
from gdflib import *


graph_file='new_graph'
path=[]		
vertices=[]						
g=Graph()
allpaths=[] 									#contains all the possible paths					
payoffs={}										#contains key-value pairs of targets->payoff
targets=[]										#list of targets
combi=[]										#holds combination of IDS
outernodes=[]
entities=GdfEntries()

values=[]

f=open(graph_file,"r")							#open the file and fetch information about the graph	
lines=f.readlines()

num_vertices,num_edges,num_targets,num_IDS=[int(i) for i in lines[0].split()]
lines.pop(0)

for i in range(num_vertices):					#save vertices of the graph in "vertices" variable
	vertices.append(i)
	
#vertices=random.sample(vertices,num_vertices)	#randomize the arrangement of vertices
#print vertices
	
"""populate payoffs"""

for i in range(num_targets):
	temp=[int(i) for i in lines[0].split()]
	payoffs[temp[0]]=temp[1]
	targets.append(temp[0])
	lines.pop(0)
#print payoffs

"""nodes from which attacker can enter"""
#for i in vertices:
#	if i not in targets:
#		outernodes.append(i)

outernodes=[int(i) for i in lines[0].split()]
print "Outernode ",outernodes
lines.pop(0)

line=random.sample(lines,num_edges)				
#print line

"""fetch the points from a file and make a graph"""
def populate_graph():
	f=open("graph.gdf","w")
	g.add_vertices(num_vertices)
	for i in vertices:
		if i in targets:
			entities.add_node(Node(name=str(i),color=0,label=str(i)))					#populate attributes in the gdf file
		else:
			entities.add_node(Node(name=str(i),color=255,label=str(i),labelcolor=100,strokecolor=50))	#populate attributes in the gdf file
	for l in line:
		a=[int(i) for i in l.split()]
		if len(a)==3:
			g.add_edges([(a[0],a[1])])
			g.es[g.get_eid(a[0],a[1])]['weight']=a[2]
		else:
			g.add_edges([(a[0],a[1])])
			g.es[g.get_eid(a[0],a[1])]['weight']=0
			
		entities.link(str(a[0]),str(a[1]))
	#print g	
	gdfdump=entities.dumps()
	f.write(gdfdump)
	f.close()
	print g,"\n"


"""helper function to find all the paths"""	
def find_all_paths_helper( start, end,path=[]):
    path = path + [start]
    if start == end:
        return [path]
    paths = []
    for node in set(g.neighbors(start)) - set(path):
        paths.extend(find_all_paths_helper(node, end, path))
    return paths

"""find all the path"""	
def find_all_paths():
	for i in targets:
		for j in outernodes:
			allpaths.append(find_all_paths_helper(j,i,path))
			
#	print allpaths			#found all paths !! 


"""find all the combination of targets """
def combine(index,num,stack):
	if num==0 :
		combi.append(copy.deepcopy(stack))
		return

	if index == len(vertices):
		return
	
	stack.append(vertices[index])
	combine(index+1,num-1,stack)
	stack.pop()
	combine(index+1,num,stack)


count=[]
def compare(x,y):
	count1=0
	count2=0
	for i in range(len(x)):
		count1=count[x[i]]
		
	for i in range(len(y)):
		count2=count[y[i]]
	#print count1 
	if count1 < count2:
		return 1
	elif count1==count2:
		return 0
	else:
		return -1			
	
	#if count[x[0]]+count[x[1]] < count[y[0]]+count[y[1]]:
	#		return 1
	#elif count[x[0]]+count[x[1]] == count[y[0]]+count[y[1]]:
	#	return 0
	#else:
	#	return -1


def compare_a(x,y):								#used for sorting of the paths according to payoffs
	payoff1=0
	payoff2=0
	for i in range(len(x)-1):
		payoff1+=g.es[g.get_eid(x[i],x[i+1])]['weight']
	
	for i in range(len(y)-1):	
		payoff2+=g.es[g.get_eid(y[i],y[i+1])]['weight']	
		
	if payoff1 > payoff2:
		return 1
	elif payoff1==payoff2:
		return 0
	else:
		return -1		
		
##########################################get defender's best response###################################################################
"""find the vertex which occurs most among all the paths chosen by the attacker"""				
def find_proper_vertex(A,D):				
	for i in range(num_vertices):		#initialize the count 
		count.append(0)
	
	for a in A:							#put values in the count array
		for j in a :
			if j not in targets:
				count[j]+=1
	
	#print count

	combinations=copy.deepcopy(combi)
	#print combinations
	combinations.sort(compare)			#sort to find a combination which occurs most ammong the paths chosen by the attacker
	#raw_input()
	positions=0
	for i in combinations:
		if i not in D:
			positions=i
			break
			
	count[:]=[]
	#print positions
	#raw_input()
	return positions

############################################get attacker's best response###############################################################
attacker_paths={}
for i in targets:
	attacker_paths[i]=[]
pop_count=0	
b_path=[]	

def get_attackers_best_path(A,D,prev,probabilities_defender):
	b_path[:]=[]
	flag4=0	
	
	for i in targets:
		if len(attacker_paths[i]) != 0:
			max_target=i
			flag4=1
			break
	if flag4==0:
		return 0	
			
	cur=0
	cur_path=[]
	Attacker=copy.deepcopy(A)
	Defender=copy.deepcopy(D)
	prev2=0
	
	###choose a path and calculate the payoff and find the one which gives the best ###
	for i in targets:
		if len(attacker_paths[i])==0:
			continue
		Attacker.append(copy.deepcopy(attacker_paths[i][-1]))
		cur=calculate_value(Attacker,Defender,probabilities_defender)
		
		if  cur > prev2:
			cur_path=attacker_paths[i][-1]
			max_target=i
			prev2=cur
		Attacker.pop()
		
	#print "Max_path :",attacker_paths[max_target][-1],"prev2 :",prev2	
	
	if prev2 <= prev:						#Discard the path if payoff is less that prev payoff
		print "poping: ",attacker_paths[max_target][-1]
		attacker_paths[max_target].pop()
		get_attackers_best_path(A,D,prev,probabilities_defender)
		
	else:									#if payoff > prev_payoff return this path as attacker's best response
		max_path=attacker_paths[max_target][-1]
		attacker_paths[max_target].pop()
		for i in max_path:
			b_path.append(i)
		return max_path					

######################################################################################################################################

probabilities_defender={}
for i in range(num_vertices):						#initialize all probabilities to zero
	probabilities_defender[i]=0


"""calulate the probability dist of the defender and attacker strategies and find the value of the game"""		
def game_value():
	A=[]									#contains set of all paths available for the attacker strategies
	D=[]									#contains all the combinations of vertices for the defender strategies
	A_str=[]								#contains only the best paths
	D_str=[]

	prev_value=0
	cur_value=0

	for i in vertices:						##make combinations of the vertices by discarding the target nodes
		if i in targets:
			vertices.remove(i)
	
	stack=[]		
	combine(0,num_IDS,stack)				##combinations are stored in the "combi" list
	
	for i in combi:						
		D.append(i)
	
	#allpaths=random.sample(allpaths,len(allpaths)) 
	
	for i in allpaths:						##initialize the "A" list by appending all the paths calculated
		for j in i:
			flag=True
			for a in j[:-1]:
				if a in targets:
					flag=False
					break
			if flag==True:	
				attacker_paths[j[-1]].append(j)	
				A.append(j)	
				#raw_input()	
	
	#########find the maximum payoff that can be attained by the attacker
	max_payoff=0
	for x in A:
		payoff1=0
		for i in range(len(x)-1):
			payoff1+=g.es[g.get_eid(x[i],x[i+1])]['weight']
		payoff1+=payoffs[x[-1]]
			
		if max_payoff < payoff1:
			max_payoff=payoff1
	print "max_payoff: ",max_payoff		

	
	#####################sort attackers paths according to max payoff#############
	for i in attacker_paths:
		#attacker_paths[i]=random.sample(attacker_paths[i],len(attacker_paths[i]))
		attacker_paths[i].sort(compare_a)
	
	for i in targets:
		print attacker_paths[i],"\n"
	#raw_input()
	
	A.reverse()
	flag1=0
	prev2=0
	
	#####loop until attacker's or defender's paths are over#############
	while len(A)!= 0 :
		bestpath=0
		#probabilities_defender.clear()
		att=0	#to check who is 
		defen=0	#adding strategy
		print "###########curr: ",cur_value,"prev: ",prev_value
		#raw_input()
		
		###for the first step both attacker and defender will add strategies#####
		if flag1 == 0 :					
			print "flag 0"
			#D_str.append(D.pop())
			A_str.append(A.pop(A.index(attacker_paths[targets[0]].pop())))
			D_str.append(D.pop())					
			flag1+=1
			cur_value=calculate_value(A_str,D_str,probabilities_defender)
			prev2=cur_value
			continue
		
		else:
		
			##defender adds only when cur_value >= prev_value##################
			if cur_value >= prev_value and cur_value != 0:
				print "\n*****Defender adding str******\n"
				position = find_proper_vertex(A_str,D_str)				#get best overlapping vertex from previous paths
				if position == 0 :
					print "defender paths over"
					break
				D_str.append(D.pop(D.index(position)))
				print position
				#raw_input()
			
			else:	
				print "\n*********Attacker addding str******\n"
				bestpath=get_attackers_best_path(A_str,D_str,cur_value,probabilities_defender)
				print "#####attacker adding : ",b_path
				#raw_input()
				if bestpath==0:				#no more paths
					break
				if bestpath==None:			#no more paths
					if len(b_path)==0:
						print "NO more attackers strategies left"
						continue
					else:
						bestpath=b_path	
				A_str.append(A.pop(A.index(bestpath)))
			
		cur_value=calculate_value(A_str,D_str,probabilities_defender)		#calculate the value of the game
		prev_value=prev2
		prev2=cur_value
		
"""calulate the value of the game using gambit"""					
def calculate_value(A_str,D_str,probabilities_defender):			
	n=len(A_str)
	m=len(D_str)

	game=gambit.new_table([n,m])        	#create a payoff table
	game.players[0].label="attacker"
	game.players[1].label="defender"
	game.title="P2P Patrol"
		
	i=0
	for a in A_str:							#assigning labels to attacker's strategies
		game.players[0].strategies[i].label='->'.join(str(x) for x in a)
		i+=1
	
	i=0
	for k in D_str:							#assigning labels to defender's strategies
		game.players[1].strategies[i].label=str(k)
		i+=1	 
		
	
	strategies0= game.players[0].strategies
	strategies1= game.players[1].strategies
		
	strategies0=str(strategies0).split(",")		
	strategies1=str(strategies1).split(">")
		

	"""print Strategies"""
	#print "\nStrategies of Attacker"
	#for i in strategies0:
	#	print i	
	
	#print "\nStrategies of Defender"
	#for j in strategies1:
	#	print j	
			
	#raw_input()
	#print "\nPayoff matrix "
	
	########################################Fill values in the payoff matrix###############################
	k=0
	for i in range(len(A_str)):
		temp=[]	
		target=A_str[i][-1]
		
		for j in D_str:
			flag=0		
			value=0	
			payoff=0
			for y in range(len(A_str[i])-1):
				if A_str[i][y] in j:
					game[i,k][0]=0					
					game[i,k][1]=0
					payoff=0
					break
				value=g.es[g.get_eid(A_str[i][y],A_str[i][y+1])]['weight']
				payoff+=value
				if y==len(A_str[i])-2 and value != 0:
					payoff+=payoffs[target]	
					game[i,k][0]=int(payoff)					
					game[i,k][1]=-int(payoff)
					break
			
			k+=1
			temp.append(payoff)
			
		k=0	
		print temp ," --- ", game.players[0].strategies[i].label 
	
	p=game.mixed_profile()
	solver = gambit.nash.ExternalLCPSolver()				#Solve for Nash Equilibrium
	strategies= solver.solve(game)
	strategies=str(strategies).split(',')
	p=solver.solve(game,use_strategic=True)
	
	######################print the probability distribution of attacker and defender strategies######################
	l=0
	print "\nProbability distribution for defender's strategy"
	for x in range(num_vertices):						#initialize all probabilities to zero
			probabilities_defender[x]=0
	
	for i in D_str:		
		for j in i:
			probabilities_defender[j]=p[0][len(A_str)+l]	
		print p[0][len(A_str)+l], " <--- ", i
		l+=1
	###print the prob dist of the attacker			
	print "\nProbability distribution for attacker's strategy"
	l=0
	for i in A_str:
		print p[0][l] , "\t <--- " , i
		l+=1
	
	#######################calculate the value of the game with help of above probabilities#########################
	for j in range(n):
		i=0
		k=n
		payoff=0.0	
		for i in range(m):
			payoff+=game[j,i][0]*p[0][k]					#Calculate the value of the game "p" contains the probability distribution
			k+=1
		
		if payoff != 0:
			break
			
	print "\nfinal payoff: ",payoff
	return payoff
			
	
def main():
	print "Target nodes are: ",targets
	
	for i in payoffs:
		print "Payoff for %d id %d"%(i,payoffs[i])
	print "\nNumber of IDS: ",num_IDS
	populate_graph()																				
	find_all_paths()	
	game_value()
	print len(allpaths)

main()
