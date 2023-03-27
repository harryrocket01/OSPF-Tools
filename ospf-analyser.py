
"""
COMP - Networking Systems Coursework 2

ALL code written, Commented and Tested by
Harry R J Softley-Graham
SN : 19087176

"""

#! /usr/bin/python3

import sys
from scapy.all import *
from scapy.contrib.ospf import *
import networkx as nx
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

#Main class
class OSPF_analyser():
  def __init__(self,Given_Packets):

    #Arrays to store transit and Stub network links
    self.Links = []
    #Format [Link ID, Metric, Router1, Router2]
    self.Stub_Network = []
    #Format [Stub ID Netmask Metric Advertising router]


    Router = {}


    #Tries to read the given packet file
    try:
      allpackets = rdpcap(Given_Packets)
    except:
      print("usage: ospf-analyser.py <filename>.pcap")
      sys.exit()

    #Iterates through all the packets
    for p in allpackets:
      #checks to see if packet is of the OSPF protocol 
      if p.haslayer(OSPF_Hdr):

        current_packet_header = p[OSPF_Hdr]
        
        #If the packet is the OSPF Hello
        if p[OSPF_Hdr].type == 1: #OSPF Hello
          #Gets packet data, but not used within this code
          Current_Packet = p[OSPF_Hello]
          source = p[OSPF_Hdr].src
          router = p[OSPF_Hello].router
          backup = current_packet_header.backup
          p_neighbors = p[OSPF_Hello].neighbors
        
        #Checks to see if OSPF packet is a Databse desription
        if p[OSPF_Hdr].type == 2: #OSPF Database Description
          Current_Packet = p[OSPF_DBDesc]

          #Iterates through LSA header
          for LSAHead in Current_Packet.lsaheaders:
            Link_ID = LSAHead.id
            Source_Address = LSAHead.adrouter
            Current_Address = p[OSPF_Hdr].src 
            #if it is a transit link, updates the links
            if LSAHead.type == 2: #LSA Header is a network link
              self.Update_LinkState(Link_ID,None,None,Source_Address)
            
            elif LSAHead.type == 1: # LSA Header is a router
              Router[str(Link_ID)] = 1
            
        #If header is a link state request
        if p[OSPF_Hdr].type == 3: #Link State Request
          Current_Packet = p[OSPF_LSReq]
          pass

        #If OSPF packet is a link state update
        if p[OSPF_Hdr].type == 4: #Link State Update
          Current_Packet = p[OSPF_LSUpd]

          Packet_List = Current_Packet.lsalist
   
          #Iterates through packets
          count = 0
          #if link exists it removes it to update the stub network
          for X in self.Stub_Network:
            if (X[0] != p[OSPF_Hdr].src) and (X[3] == p[OSPF_Hdr].src):
              self.Stub_Network.remove(X)
            else:
              pass
            count +=1 

          #Goes through the LSA
          for LSA in Packet_List:
            LSA_Type = LSA.type
            #if its a stub netwrok it then ireates through the links
            if LSA_Type == 1: #STUB
                
              for current_link in LSA.linklist:
                ID = current_link.id
                Adv_Router = p[OSPF_Hdr].src 
                #If connected to link state, updates
                if current_link.type == 2: # If link is a transit
                  LinkID = current_link.id
                  LinkMetric = current_link.metric

                  self.Update_LinkState(LinkID,LinkMetric,None,None)

                #If connected to stub, updates stub network
                if current_link.type == 3: # If link is a STUB
                  Stub_ID = current_link.id
                  Netmask = current_link.data
                  Metric = current_link.metric
                  Adv_Router = LSA.adrouter
                  self.Update_Stub(Stub_ID,Netmask,Metric,Adv_Router)

            #If transit, updates transit network
            elif LSA_Type == 2 : #TRANSIT
              LinkID = LSA.id
              RouterList = LSA.routerlist

              self.Update_LinkState(LinkID,None,RouterList[0],RouterList[1])
              

        #used if aknnowlegement is sent, not used in this taks
        if p[OSPF_Hdr].type == 5: #Link State Acknowledge
          Current_Packet = p[OSPF_LSAck]
          pass

    #Prints out network

    #transit link
    print("Link ID         Metric     Routers")
    for current_line in self.Links:
      if None not in current_line:
        output = "{:<15} {:<10} {}-{}".format(current_line[0], current_line[1], current_line[2],current_line[3])
        print(output)

    print("")


    #Stub network
    print("Stub ID         Netmask              Metric     Advertising router")
    for current_line in self.Stub_Network:
      if (None not in current_line) :
        output = "{:<15} {:<20} {:<10} {}".format(current_line[0], current_line[1], current_line[2],current_line[3])
        print(output)

  #Function used to update a Transit link, if there are any updates
  def Update_LinkState(self,Link_ID, Metric, Router1, Router2):
    #Format [Link ID, Metric, Router1, Router2]

    for Current in self.Links:
      if Current[0] == Link_ID:

        if Metric != None:
          Current[1] = Metric
        if Router1 != None:
          Current[2] = Router1
        if Router2 != None:
          Current[3] = Router2
        return
    
    self.Links.append([Link_ID, Metric, Router1, Router2])
    return

  #used to Update Stub network
  def Update_Stub(self,Stub_ID, Netmask, Metric, Ad_Router):
    #Format [Stub ID Netmask Metric Advertising router]

    for Current in self.Stub_Network:
      if Current[0] == Stub_ID:

        if Netmask != None:
          Current[1] = Netmask
        if Metric != None:
          Current[2] = Metric
        if Ad_Router != None:
          Current[3] = Ad_Router
        return
      
    self.Stub_Network.append([Stub_ID, Netmask, Metric, Ad_Router])
    return

# Runs program
if __name__ == '__main__':

    #if incorrect format it prints error
    try:
      if len(sys.argv) == 2:
        infile = sys.argv[1]
        OSPF_analyser(infile)

      else:
        print("usage: ospf-analyser.py <filename>.pcap")
        sys.exit()
    except:
      print("usage: ospf-analyser.py <filename>.pcap")
      sys.exit()