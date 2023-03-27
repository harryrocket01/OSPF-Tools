
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

#Main path analyser class
class path_analyser():

    def __init__ (self,network,path,traceroute):
        #NetworkX object for network
        self.OSPF_Network = nx.DiGraph()

        #Arrays to store link, stubnetworks, paths and traceroutes
        self.Links = []
        self.Stub_Network = []
        self.Paths = []
        self.TraceRoutes = []

        #Reads the network file
        self.Read_network(network)
        #Read traceroute file
        self.Read_traceroute(traceroute)
        #read path file
        self.Read_path(path)
        #construct the network
        self.construct_network()

        #Analyse each path
        for Path in self.Paths:
            self.analyse_path(Path)
        
        #analyse each traceroute
        for Trace in self.TraceRoutes:
            self.analyse_traceroute(Trace)

 

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

    #Reads the Path file
    def Read_path(self,path):
        for Line in path:
            if Line != (" ", "","\n"):
                try:
                    Split = Line.split()
                    Name = Split[0][:-1]
                    Route = Split[1:]
                    self.Paths.append([Name,Route])
                except:
                    pass
    
    #Reads the traceroute file
    def Read_traceroute(self,traceroute):
        State = 0
        To_Append = ["","",[]]
        for Line in traceroute:
            if "traceroute:" in Line:
                State = 1

            if State ==1 or State == 2:
                Split = Line.split()
                To_Append[State-1] = Split[1]
                State += 1 

            elif State ==3:
                State += 1 

            elif State ==4 and "ms" in Line:
                Split = Line.split()
                To_Append[2].append(Split)

            else:
                if To_Append != ["","",[]]:
                    self.TraceRoutes.append(To_Append)

                State = 0
                To_Append = ["","",[]]

        if To_Append != ["","",[]]:
            self.TraceRoutes.append(To_Append)
            To_Append = ["","",[]]

    #Constructs the network
    def construct_network(self):
        #Constructs links
        for x in self.Links:
            if x[2]!= x[3]:
                self.OSPF_Network.add_edge(x[2],x[3],weight=int(x[1]))
                self.OSPF_Network.add_edge(x[3],x[2],weight=int(x[1]))

        #Constructs StubNetwork
        for y in self.Stub_Network:
            if y[0]!= y[3]:
                self.OSPF_Network.add_edge(y[3],y[0],weight=int(y[2]))
                self.OSPF_Network.add_edge(y[0],y[3],weight=int(y[2]))

    #used to analyse path
    def analyse_path(self,path):
    
        try:
            #calculates best path with Dijsktras algorithm
            Best_Path = nx.all_shortest_paths(self.OSPF_Network,path[1][0],path[1][-1],weight = "weight")
            result = True
            #Checks to see if the best path is one of the calulated best paths
            if path[1] not in Best_Path:
                result = False
        except:
            #if fales returns false
            result = False

        #Prints result
        print(path[0]+": "+str(result))

    #Function to analyse trace rotues
    def analyse_traceroute(self,trace):
        result = False
        Routerpath = [trace[1]]

        #Attempts to reconstruct jumps from the link ID
        for Jump in trace[2]:
            Router = self.resolve_router(Routerpath[-1],Jump[1])
            if Router != None:
                Routerpath.append(Router)
            else:
                print(trace[0]+": "+str(result))
                return
        
        #Clalulates the best path
        Best_Path = nx.all_shortest_paths(self.OSPF_Network,Routerpath[0],Routerpath[-1],weight = "weight")

        #Checks to see if the best path exists within the constructed path
        if Routerpath in Best_Path:
            result = True

        #Prints Result
        print(trace[0]+": "+str(result))
        
    #used to resolve if the router exists in the network
    def resolve_router(self,sauce, destination):
        
        #First checks the StubNetwork
        for Stub in self.Stub_Network:
            if destination[:-1] == Stub[0][:-1] and sauce[:-1] == Stub[3][:-1]:
                return Stub[0]
        
        #Next checks the links
        for Link in self.Links:
            if destination[:-1] == Link[0][:-1]:
                if Link[2] == sauce:
                    return Link[3]
                elif Link[3] == sauce:
                    return Link[2]           

        #if it does not exist it returns none   
        return None

#Runs main function
if __name__ == '__main__':

    #Checks to see if it is in the right format if so runs the function
    try:
        if len(sys.argv) > 1:
            network = open(sys.argv[1], "r")
            path = open(sys.argv[2], "r")
            traceroute = open(sys.argv[3], "r")

            network = path_analyser(network,path,traceroute)
        else:
            print("usage: path-analyser.py <network> <paths> <trace-route>")
            sys.exit()
    except:
        print("usage: path-analyser.py <network> <paths> <trace-route>")
        sys.exit()