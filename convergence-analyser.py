
"""
COMP - Networking Systems Coursework 2

ALL code written, Commented and Tested by
Harry R J Softley-Graham
SN : 19087176

"""

import sys
import networkx as nx
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

#Class used to check for convergence loops
class convergence_analyser():


    #Init Sets up global lists and runs each of the functiosn to check for convergence
    def __init__ (self,network,path,destination):
        #NetworkX object used to construct network
        self.OSPF_Network = nx.DiGraph()

        #used to save all of the infomation within the inputted network
        self.Links = []
        self.Stub_Network = []

        #Used to check where routers can start
        self.Start_Routers = []

        #Reads file, constructs network and then checks for convergence
        self.Read_network(network)
        self.construct_network()
        self.check_convergence(path,destination)


    #Used to read the file
    def Read_network(self,network):
        
        #Loop that goes through each line, updating the state depending on the type of line
        State = 0
        for line in network:
            
            #State 1 is to read the Link ID section
            if "Link ID         Metric     Routers" in line:
                State = 1
            #State 1 is to read the Stub network
            elif "Stub ID         Netmask              Metric     Advertising router" in line:
                State = 2
            
            elif line == ("" or " " or "\n"):
                pass

            #Reads and appends links to the LinkID array
            elif State == 1:

                try:
                    LinkID, Metirc, Routers = line.split()
                    Router1,Router2 = Routers.split("-")
                    self.Links.append([LinkID, Metirc,Router1,Router2])

                except:
                    pass

            #Reads and appends STUB to the StubNetwork array
            elif State == 2:
                try:
                    ip_address, subnet_mask, hop_count, next_hop = line.split()
                    self.Stub_Network.append([ip_address, subnet_mask, hop_count, next_hop ])
                except:
                    pass

        pass

    #Constructs the network from the read file, using the Link and Stub_Network arrays 
    def construct_network(self):
        for x in self.Links:
            if x[2]!= x[3]:
                self.OSPF_Network.add_edge(x[2],x[3],weight=int(x[1]))
                self.OSPF_Network.add_edge(x[3],x[2],weight=int(x[1]))
                if x[2] != self.Start_Routers:
                    self.Start_Routers.append(x[2])
                if x[3] != self.Start_Routers:
                    self.Start_Routers.append(x[3])
                    
        for y in self.Stub_Network:
            if y[0]!= y[3]:
                self.OSPF_Network.add_edge(y[3],y[0],weight=int(y[2]))
                self.OSPF_Network.add_edge(y[0],y[3],weight=int(y[2]))

    #Main Function to check for convergence
    def check_convergence(self,Break,destination):
        
        #Used to check if broken link or destination are in the network
        In_Network_Flag = False
        End_Router = destination

        #Saves both ways of the broken link
        Broken_Link = []
        Broken_Link2 = []

        #Checks to see if destination is in the Stub Network List
        for X in self.Stub_Network:

            if X[0] == destination:
                In_Network_Flag = True
                End_Router = X[0]
                break
        if In_Network_Flag == False:
            print("OSPF convergence loop: no loop")
            return
        In_Network_Flag = False

        #Checks to see if broken link exists within the network
        for Y in self.Links:
            if Y[0] == Break:
                In_Network_Flag = True
                Broken_Link = [Y[2],Y[3]]
                Broken_Link2 = [Y[3],Y[2]]

                break
        if In_Network_Flag == False:
            print("OSPF convergence loop: no loop")
            return

        #If its in the network it will loop through all the potential start routers within the network
        for Start_Router in self.Start_Routers:
            
            #it calculates all the shortest routes
            All_Paths = nx.all_shortest_paths(self.OSPF_Network,Start_Router,End_Router,weight = "weight")

            #Iterates through all the shortest routes
            for Route in All_Paths:
                
                #Checks to see if Broken link is in path
                for Nodes in range(0,len(Route)-1):
                    Link =[Route[Nodes],Route[Nodes+1]]

                    #If there is it then finds all the nodes around the broken link
                    if (Broken_Link == Link) or (Broken_Link2 == Link):
                        Edges = self.OSPF_Network.edges(Route[Nodes])
                        #Finds all connected nodes to broken point
                        Sorted_Edges = []

                        No_Island_Flag = False

                        #It checks to see if the break makes the route a island
                        for Edge_Node in Edges:
                            Sorted_Edges.append(Edge_Node[1])

                            
                            if Edge_Node[1] in self.Start_Routers and Edge_Node[1] not in Route:
                                No_Island_Flag = True

                        #if no islands it iterates through the rest of the link
                        if No_Island_Flag:
                            for Edge_Node in Sorted_Edges:                                
                                if (Edge_Node not in Route) and (Edge_Node in self.Start_Routers):

                                    #It recalcualtes the shortes path 
                                    New_Path = nx.all_shortest_paths(self.OSPF_Network,Edge_Node,End_Router,weight = "weight")
                                    
                                    #It iterates through new potential paths
                                    for New_Route in New_Path:
                                        Last_Node = ""
                                        #Checks to see if there is a covnergence error where it sends it back
                                        for New_Nodes in New_Route:
                                            New_Link = [New_Nodes,Last_Node]

                                            #If there is a error it prints the path of the error
                                            if (Broken_Link == New_Link) or (Broken_Link2 == New_Link):


                                                Loop_Print = ""

                                                for X in Route:
                                                    Loop_Print += X+", "

                                                    if X in Broken_Link:
                                                        break
                                                
                                                for Y in New_Route:
                                                    Loop_Print += Y
                                                
                                                    if Y in Route:
                                                            break
                                                    Loop_Print += ", "

                                                print("OSPF convergence loop:",Loop_Print)
                                                return
                                            Last_Node = New_Nodes

                        else:
                            #If its a island, and cannot reach the desination it outputs the loop
                            Loop_Print = ""
                            for X in Sorted_Edges:
                                if X not in Broken_Link:
                                    LastItem = X
                                    break

                            for X in Route:
                                Loop_Print += X+", "

                                if X in Broken_Link:
                                    Loop_Print += LastItem+", "
                                    Loop_Print += X
                                    break
                                LastItem = X    
                            print("OSPF convergence loop:",Loop_Print)
                            return


        #If nothing is found there is no loop
        print("OSPF convergence loop: no loop")



#Runs Program
if __name__ == '__main__':

    #makes sure that the input arguments are correct
    try:
        if len(sys.argv) > 1:
            network = open(sys.argv[1], "r")
            start = sys.argv[2]
            destination = sys.argv[3]

            network = convergence_analyser(network,start,destination)
        else:
            print("usage: convergence-analyser.py <network> <start ip> <destination ip>")
            sys.exit()
    except:
        print("usage: convergence-analyser.py <network> <start ip> <destination ip>")
        sys.exit()