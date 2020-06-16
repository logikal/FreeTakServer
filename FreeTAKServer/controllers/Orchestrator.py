#######################################################
# 
# orchestrator.py
# Python implementation of the Class orchestrator
# Generated by Enterprise Architect
# Created on:      21-May-2020 12:24:48 PM
# Original author: Natha Paquette
# 
#######################################################
from importlib import import_module
from RecieveConnections import RecieveConnections
from ClientInformationController import ClientInformationController
from ClientSendHandeler import ClientSendHandeler
from SendClientData import SendClientData
from DataQueueController import DataQueueController
from ClientInformationQueueController import ClientInformationQueueController
from ActiveThreadsController import ActiveThreadsController
from RecieveConnectionsProcessController import RecieveConnectionsProcessController
from MainSocketController import MainSocketController
from XMLCoTController import XMLCoTController
from SendOtherController import SendOtherController
from SendDataController import SendDataController
from AsciiController import AsciiController
from constants.LoggingConstants import LoggingConstants

ascii = AsciiController().ascii
import sys
from logging.handlers import RotatingFileHandler
import logging
import DataPackageServer
import multiprocessing
import threading
import time
import pickle
import importlib
from queue import Queue
import argparse
import sqlite3

loggingConstants = LoggingConstants()

def newHandler(filename, log_level, log_format):
    handler = RotatingFileHandler(
        filename,
        maxBytes=loggingConstants.MAXFILESIZE,
        backupCount=loggingConstants.BACKUPCOUNT
    )
    handler.setFormatter(log_format)
    handler.setLevel(log_level)
    return handler


log_format = logging.Formatter(loggingConstants.LOGFORMAT)
logger = logging.getLogger(loggingConstants.LOGNAME)
logger.setLevel(logging.DEBUG)
logger.addHandler(newHandler(loggingConstants.DEBUGLOG, logging.DEBUG, log_format))
logger.addHandler(newHandler(loggingConstants.WARNINGLOG, logging.WARNING, log_format))
logger.addHandler(newHandler(loggingConstants.INFOLOG, logging.INFO, log_format))
console = logging.StreamHandler(sys.stdout)
console.setFormatter(log_format)
console.setLevel(logging.DEBUG)
logger.addHandler(console)

from ClientReceptionHandler import ClientReceptionHandler

class Orchestrator:
# default constructor  def __init__(self):  
    def __init__(self):
        #create necessary queues
        self.clientInformationQueue = []
        #this contains a list of all pipes which are transmitting CoT from clients
        self.pipeList = []
        #Internal Pipe used for CoT generated by the server itself
        self.internalCoTArray = []

        self.ClientReceptionHandlerEventPipe = ''
        #instantiate controllers
        self.m_ActiveThreadsController = ActiveThreadsController()
        self.m_ClientInformationController = ClientInformationController()
        self.m_ClientInformationQueueController = ClientInformationQueueController() 
        self.m_ClientSendHandeler = ClientSendHandeler() 
        self.m_DataQueueController = DataQueueController() 
        self.m_RecieveConnections = RecieveConnections() 
        self.m_RecieveConnectionsProcessController = RecieveConnectionsProcessController()
        self.m_MainSocketController = MainSocketController()
        self.m_XMLCoTController = XMLCoTController()
        self.m_SendClientData = SendClientData()        

    def clientConnected(self, rawConnectionInformation):
        try:
            logger.info('client has connected')
            orchestratorPipe, clientPipe = multiprocessing.Pipe()
            #instantiate model
            clientInformation = self.m_ClientInformationController.intstantiateClientInformationModelFromConnection(rawConnectionInformation, clientPipe)
            #add client information to queue
            self.m_ClientInformationQueueController.addClientToQueue(clientInformation)
            self.clientInformationQueue.append(clientInformation)
            #begin client reception handler
            self.ClientReceptionHandlerEventPipe[0].send(("create", clientInformation))
            #add to active threads
            #send all client data needs to be implemented
            SendDataController().sendDataInQueue(clientInformation, clientInformation, self.clientInformationQueue)
            #add the callsign and UID to the DataPackageCallsignPipe
            pipeData = ["add",clientInformation.modelObject.uid ,clientInformation.modelObject.m_detail.m_Contact.callsign]
            self.CallSignsForDataPackagesPipe[0].send(pipeData)
            logger.info('finished establishing connection')
        except Exception as e:
            logger.error('there has been an error in a clients connection'+str(e))
    
    def emergencyRecieved(self, processedCoT):
        try:
            if processedCoT.status == 'on':
                self.internalCoTArray.append(processedCoT)
                logger.debug('emergency has been created')
            elif processedCoT.status == 'off':
                for CoT in self.internalCoTArray:
                    if CoT.type == "emergency" and CoT.modelObject.uid == processedCoT.modelObject.uid:
                        self.internalCoTArray.remove(CoT)
                        logger.debug('emergency has now been removed')
        except Exception as e:
            logger.error('there has been an error in a clients connection'+str(e))

    def dataRecieved(self,RawCoT):
        # this will be executed in the event that the use case for the CoT isnt specified in the orchestrator
        try:
            #this will check if the CoT is applicable to any specific controllers            
            RawCoT = self.m_XMLCoTController.determineCoTType(RawCoT)
            #the following calls whatever controller was specified by the above function
            module = importlib.import_module(RawCoT.CoTType)
            CoTSerializer = getattr(module, RawCoT.CoTType)
            processedCoT = CoTSerializer(RawCoT).getObject()
            sender = processedCoT.clientInformation
            #this will send the processed object to a function which will send it to connected clients
            SendDataController().sendDataInQueue(sender, processedCoT, self.clientInformationQueue)
            try:
                print(processedCoT.type)
                if processedCoT.type == 'emergency':
                    self.emergencyRecieved(processedCoT)
            except:
                pass
        except Exception as e:
            logger.error('there has been an error in the reception of generic data'+str(e))
            pass

    def clientDisconnected(self, clientInformation):
        #print(self.clientInformationQueue[0])
        #print(clientInformation)
        try:
            print('initiating client disconnection')
            for client in self.clientInformationQueue:
                if client.ID == clientInformation.clientInformation.ID:
                    self.clientInformationQueue.remove(client)
                else:
                    pass
            self.m_ActiveThreadsController.removeClientThread(clientInformation)
            pipeData = ["remove",clientInformation.clientInformation.modelObject.uid ,clientInformation.clientInformation.modelObject.m_detail.m_Contact.callsign]
            self.CallSignsForDataPackagesPipe[0].send(pipeData)
            self.ClientReceptionHandlerEventPipe[0].send(('destroy', clientInformation))
            print('client successfully disconnected')
        except Exception as e:
            logger.error('there has been an error in the reception of generic data'+str(e))
            pass

    def monitorRawCoT(self):
        #this needs to be the most robust function as it is the keystone of the program
        from model.RawCoT import RawCoT
        while True:
            try:
                if len(self.pipeList)>0:
                    for pipeTuple in self.pipeList:
                        time.sleep(0.1)
                        #this while loop runs on each pipe to extract all data within
                        while pipeTuple[0].poll():
                            try:
                                try:
                                    data = pipeTuple[0].recv()
                                except OSError as e:
                                    logger.error('there has been an error in the reception of data in the monitoring of pipes 1'+str(e))
                                    break
                                #this will attempt to define the type of CoT along with the designated controller
                                try:
                                    CoT = XMLCoTController().determineCoTGeneral(data)
                                    function = getattr(self, CoT[0])
                                    function(CoT[1])
                                except Exception as e:
                                    logger.error('there has been an error in the reception of data in the monitoring of pipes 2'+str(e))
                                    pass
                            except Exception as e:
                                logger.error('there has been an error in the reception of data in the monitoring of pipes 3'+str(e))
                                break
                else:
                    pass
            except Exception as e:
                logger.error('there has been an error in the reception of data in the monitoring of pipes 4'+str(e))
                pass
            if len(self.internalCoTArray) > 0:
                try:
                    for processedCoT in self.internalCoTArray:
                        SendDataController().sendDataInQueue(None, processedCoT, self.clientInformationQueue)
                except:
                    logger.error('there has been an error in the scanning of the internal CoT array'+str(e))
            else:
                pass
        self.monitorRawCoT()
    
    def loadAscii(self):
        ascii()

    def start(self, CoTIP, CoTPort, DataIP, DataPort):
        try:
            logger.propagate = False
            #create socket controller
            self.m_MainSocketController.changeIP(CoTIP)
            self.m_MainSocketController.changePort(CoTPort)
            sock = self.m_MainSocketController.createSocket()

            #create Pipe for callsigns between orchestrator and DataPackagesServerProcess
            orchestratorPipe, DataPackageServerPipe = multiprocessing.Pipe()
            pipeTuple = (orchestratorPipe, DataPackageServerPipe)
            self.CallSignsForDataPackagesPipe = pipeTuple

            #create pipe for reception of connections
            orchestratorPipe, recieveConnectionPipe = multiprocessing.Pipe()
            pipeTuple = (orchestratorPipe, recieveConnectionPipe)
            self.pipeList.append(pipeTuple)

            

            #begin DataPackageServer
            dataPackageServerProcess = multiprocessing.Process(target = DataPackageServer.FlaskFunctions().startup, args=(DataIP, DataPort,DataPackageServerPipe,), daemon=True)
            dataPackageServerProcess.start()
            time.sleep(2.5)
            print('loading ...')
            loading = threading.Thread(target=self.loadAscii, args=())
            loading.start()
            #establish client handeler
            orchestratorPipe, clientReceptionHandlerEventPipe = multiprocessing.Pipe()
            pipeTuple = (orchestratorPipe, clientReceptionHandlerEventPipe)
            self.ClientReceptionHandlerEventPipe = pipeTuple

            orchestratorPipe, clientReceptionHandlerDataPipe = multiprocessing.Pipe()
            pipeTuple = (orchestratorPipe, clientReceptionHandlerDataPipe)
            self.pipeList.append(pipeTuple)

            clientReceptionHandlerProcess = multiprocessing.Process(target=ClientReceptionHandler().startup, args=(clientReceptionHandlerDataPipe, clientReceptionHandlerEventPipe), daemon=True)
            clientReceptionHandlerProcess.start()

            time.sleep(3)

            #begin to monitor all pipes
            monitorRawCoTProcess = multiprocessing.Process(target = self.monitorRawCoT, args = ())
            monitorRawCoTProcess.start()

            loading.join()
            #begin to recieve connections
            recieveConnectionProcess = multiprocessing.Process(target=self.m_RecieveConnections.listen, args=(sock,recieveConnectionPipe,), daemon=True)
            recieveConnectionProcess.start()
            


            #instantiate domain model and save process as object
            activeRecieveConnectionProcess = self.m_RecieveConnectionsProcessController.InstantiateModel(recieveConnectionProcess)
            logger.propagate = True
            logger.info('server has started')
            while True:
                time.sleep(1000)
        except Exception as e:
            logger.critical('there has been a critical error in the startup of FTS'+str(e))
    def stop(self):
        pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='FreeTAKServer startup settings')
    parser.add_argument('-CoTPort', type = int, help = 'the port you would like FreeTAKServer to run receive connections on', default=8087)
    parser.add_argument('-CoTIP', type = str, help = "the IP you would like FreeTAKServer to run receive connections on ONLY CHANGE IF YOU KNOW WHAT YOU'RE DOING", default='0.0.0.0')
    parser.add_argument('-DataIP', type = str, help = 'the ip address you would like FreeTAKServer to run receive datapackages on this is necesarry if its not set correctly data packages will fail', default = '0.0.0.0')
    parser.add_argument('-DataPort', type = int, help = 'the port address you would like FreeTAKServer to run receive datapackages on not', default=8080)
    args = parser.parse_args()
    Orchestrator().start(args.CoTIP, args.CoTPort, args.DataIP, args.DataPort)

