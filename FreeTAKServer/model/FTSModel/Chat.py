from FreeTAKServer.model.FTSModel.fts_protocol_object import FTSProtocolObject
#######################################################
# 
# __chat.py
# Python implementation of the Class __chat
# Generated by Enterprise Architect
# Created on(FTSProtocolObject):      11-Feb-2020 11(FTSProtocolObject):08(FTSProtocolObject):10 AM
# Original author: Corvo
# 
#######################################################
from FreeTAKServer.model.FTSModelVariables.ChatVariables import ChatVariables as vars
from FreeTAKServer.model.FTSModel.Chatgrp import Chatgrp

class Chat(FTSProtocolObject):
      # default constructor       
    def __init__(self):
        self.senderCallsign = None
        self.id = None
        self.parent = None
        self.chatroom = None
        self.groupOwner = None
        self.chatgrp = None

    @staticmethod
    def geochat(GROUPOWNER = vars.geochat().GROUPOWNER, ID = vars.geochat().ID, PARENT = vars.geochat().PARENT,
                CHATROOM = vars.geochat().CHATROOM, SENDERCALLSIGN = vars.geochat().SENDERCALLSIGN):
        chat = Chat()
        chat.setgroupOwner(GROUPOWNER)
        chat.setparent(PARENT)
        chat.setid(ID)
        chat.setchatroom(CHATROOM)
        chat.setsenderCallsign(SENDERCALLSIGN)
        chat.setchatgrp(Chatgrp.geochat())
        return chat

    def getparent(self): 
        return self.parent 

     # parent setter 
    def setparent(self,parent=0):  
        self.parent=parent 
    
    # senderCallsign getter 
    def getsenderCallsign(self):
        return senderCallsign 

    # senderCallsign setter 
    def setsenderCallsign(self,senderCallsignn):
        global senderCallsign
        senderCallsign=senderCallsignn 

      # chatroom getter 
    def getchatroom(self): 
        return self.chatroom 

    # chatroom setter 
    def setchatroom(self, chatroom=0):  
        self.chatroom=chatroom 

        # groupOwner getter 
    def getgroupOwner(self): 
        return self.groupOwner 

    # groupOwner setter 
    def setgroupOwner(self, groupOwner=0):  
        self.groupOwner=groupOwner 

      # id getter 
    def getid(self): 
        return self.id 

    # id setter 
    def setid(self, id=0):  
        self.id=id
    #chatgrp uid0 getter
    def getuid0(self):
      self.chatgrp.getuid0()
  
    def setuid0(self, uid0=0):
        self.chatgrp.setuid0(uid0)

    def getuid1(self):
        self.chatgrp.getuid1()
  
    def setuid1(self, uid1=0):
        self.chatgrp.setuid1(uid1)

    def getchatgrp(self):
        return self.chatgrp
  
    def setchatgrp(self, chatgrp=0):
        print(chatgrp)
        self.chatgrp = chatgrp
