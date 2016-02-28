#!/usr/bin/python
############################################################################################################################################
#Packages - (Igraph,Gambit)
#Multi_IDS
#Trivial solution
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
	
"""populate payoffs for the target_nodes"""
for i in range(num_targets):
	temp=[int(i) for i in lines[0].split()]
	payoffs[temp[0]]=temp[1]
	targets.append(temp[0])
	lines.pop(0)
#print payoffs

"""nodes from which attacker can enter"""
outernodes=[int(i) for i in lines[0].split()]
print "Source_nodes ",outernodes
lines.pop(0)

line=random.sample(lines,num_edges)				
#print line

"""fetch the points from a file and make a graph_file which goes as input to gephi"""
def populate_graph():
	f=open("graph.gdf","w")
	g.add_vertices(num_vertices)
	for i in vertices:
		if i in targets:
			entities.add_node(Node(name=str(i),color=0,label=str(i)))
		else:
			entities.add_node(Node(name=str(i),color=255,label=str(i),labelcolor=111,strokecolor=50))	
	for l in line:
		a=[int(i) for i in l.split()]
		if len(a)==3:
			g.add_edges([(a[0],a[1])])
			g.es[g.get_eid(a[0],a[1])]['weight']=a[2]
		else:
			g.add_edges([(a[0],a[1])])
			g.es[g.get_eid(a[0],a[1])]['weight']=0
			
		entities.link(str(a[0]),str(a[1]),weight=a[2])
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

"""find all the path in the graph(part of attacker's strategies)"""	
def find_all_paths():
	for i in targets:
		for j in outernodes:
			allpaths.append(find_all_paths_helper(j,i,path))
	

"""find all the combination of targets(part of defender's strategies) """
def combine(index,num,stack):
	if num==0 :
		combi.append(copy.deepcopy(stack))
		return

	if index == len(targets):
		return
	
	stack.append(targets[index])
	combine(index+1,num-1,stack)
	stack.pop()
	combine(index+1,num,stack)


def game_value():

	print "Calculating equilibrium"
	A=[]
	X=[]
	A_old=[]
	B_old=[]

	stack=[]
	combine(0,num_IDS,stack)
	for i in combi:
		X.append(i)
	
	#X=random.sample(X,len(X))		#just randomize the defender's strategies
	 
	for i in allpaths:
		for j in i:
			flag=True
			for a in j[:-1]:
				if a in targets:
					flag=False
					break
			if flag==True:		
				A.append(j)	
				#raw_input()	
	
	
	#A=random.sample(A,len(A))			#just randomize the attacker's strategies
	
#	print "Defender: ",X
#	print "Attacker: ",A	
	#raw_input()				
	n=len(A)
	m=len(X)
	
	game=gambit.new_table([n,m])		#create a payoff table
	game.players[0].label="attacker"
	game.players[1].label="defender"
	game.title="P2P Patrol"
	
	i=0
	for a in A:							#assigning labels to attacker's strategies
		game.players[0].strategies[i].label='->'.join(str(x) for x in a)
		i+=1
	
	i=0
	for k in X:							#assigning labels to defender's strategies
		game.players[1].strategies[i].label=str(k)
		i+=1	 
		
	
	strategies0= game.players[0].strategies
	strategies1= game.players[1].strategies
	
	strategies0=str(strategies0).split(",")		
	strategies1=str(strategies1).split(">")
	
	print "\nStrategies of Attacker"
	for i in strategies0:
		print i	
	
	print "\nStrategies of Defender"
	for j in strategies1:
		print j	
	
	
	raw_input()
	print "\nPayoff matrix "
	k=0
	for i in range(len(A)):
		temp=[]	
		target=A[i][-1]
		
		for j in combi:
			if target in j:								#if target is in one of the combinations its caught both get payoff 0
				game[i,k][0]=0
				game[i,k][1]=0
				temp.append(0)
			else:	
				value=0	
				payoff=0
				for y in range(len(A[i])-1):
					value=g.es[g.get_eid(A[i][y],A[i][y+1])]['weight']
					payoff+=value	
					
					if y==len(A[i])-2 and value != 0:
						payoff+=payoffs[target]	 
						game[i,k][0]=int(payoff)					
						game[i,k][1]=-int(payoff)
						break
	
				temp.append(payoff)
			k+=1
			
		k=0	
		print temp ," --- ", game.players[0].strategies[i].label 
		
	raw_input()			
	p=game.mixed_profile()
	solver = gambit.nash.ExternalLCPSolver()				#Solve for Nash Equilibrium
	strategies= solver.solve(game)
	#print strategies
	strategies=str(strategies).split(',')
	p=solver.solve(game,use_strategic=True)
	probabilities_defender={}
	"""print the probability distribution of attacker and defender strategies"""
	l=0
	print "\nProbability distribution for defender's strategy"
	for x in range(num_vertices):						#initialize all probabilities to zero
			probabilities_defender[x]=0
	
	for i in X:
		#print "setting prob"
		
		for j in i:
			#if probabilities_defender[j] <= p[0][len(A_str)+l] :
			probabilities_defender[j]=p[0][len(A)+l]	
		#	print "j: ",j,probabilities_defender[j]			
		print p[0][len(A)+l], " <--- ", i
		l+=1
		
	print "\nProbability distribution for attacker's strategy"
	l=0
	for i in A:
		print p[0][l] , "\t <--- " , i
		l+=1

	
	for j in range(n):
		i=0
		k=n
		payoff=0.0	
		for i in range(m):
			#print "pay ",game[j,i][0],"prob ",p[0][k]
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
	raw_input()
	populate_graph()																				
	find_all_paths()	
	game_value()

main()
