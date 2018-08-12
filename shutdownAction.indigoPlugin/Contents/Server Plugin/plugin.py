#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# show sql data in logfile  Plugin
# Developed by Karl Wachs
# karlwachs@me.com

import os, sys, subprocess, pwd, copy, datetime, time
import versionCheck.versionCheck as VS


'''
PURPOSE:    execute a specific action at shut down of indigo  in order to be able to finish things, ... 

exeute indigo action during indigo shutdown  .. triggered by shutting down this plugin 
- it will test if the indig logfile indicates a complet indigo shut down
- look for "Quitting Indigo Server - stopping plugins"
  then if found, tries to find  "Loading plugin" after the shutdown lines.
  if loading plugin is found , it's not a shutdown 
  if not it will execute the selected action group (setup in config)
  
'''


################################################################################
class Plugin(indigo.PluginBase):

    ########################################
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)
        ##self.errorLog( os.getcwd())
        self.pathToPlugin = os.getcwd() + "/"
        ## = /Library/Application Support/Perceptive Automation/Indigo 6/Plugins/piBeacon.indigoPlugin/Contents/Server Plugin
        p = max(0, self.pathToPlugin.lower().find("/plugins/")) + 1
        self.indigoPath = self.pathToPlugin[:p]
        self.pluginVersion      = pluginVersion
        self.pluginId           = pluginId
        self.pluginName         = pluginId.split(".")[-1]

        ##self.errorLog(self.indigoPath)
        # self.errorLog(self.pathToPlugin)


    ########################################
    def __del__(self):
        indigo.PluginBase.__del__(self)
    
    ########################################
    def startup(self):


        if self.pathToPlugin.find("/" + self.pluginName + ".indigoPlugin/") == -1:
            self.errorLog(u"--------------------------------------------------------------------------------------------------------------")
            self.errorLog(u"The pluginname is not correct, please reinstall or rename")
            self.errorLog(u"It should be   /Libray/....../Plugins/" + self.pluginName + ".indigPlugin")
            p = max(0, self.pathToPlugin.find("/Contents/Server"))
            self.errorLog(u"It is: " + self.pathToPlugin[:p])
            self.errorLog(u"please check your download folder, delete old *.indigoPlugin files or this will happen again during next update")
            self.errorLog(u"---------------------------------------------------------------------------------------------------------------")
            self.sleep(2000)
            exit(1)
            return

        self.userName = pwd.getpwuid( os.getuid() )[ 0 ]
        self.debugLevel		= int(self.pluginPrefs.get(	"debugLevel",		255))

        try:    self.shutDownAction = int(self.pluginPrefs.get(		"shutDownAction",	0))
        except: self.shutDownAction = 0
        self.shutDownActionName  = ""

        if self.shutDownAction !=0:
            ac = indigo.actionGroups[self.shutDownAction]
            self.shutDownActionName = ac.name
            indigo.server.log('action to be executed when this plugin shuts down: "'+ self.shutDownActionName+'"; id= '+str(self.shutDownAction)) 
        else:
            indigo.server.log('no action to be executed when this plugin shuts down') 
        return




####-----------------  set the geneeral config parameters---------
    def validatePrefsConfigUi(self, valuesDict):

        self.debugLevel	    = int(valuesDict[u"debugLevel"])
            
        try:    self.shutDownAction = int(valuesDict["shutDownAction"])
        except: self.shutDownAction = 0
        if self.shutDownAction != 0:
            ac = indigo.actionGroups[self.shutDownAction]
            self.shutDownActionName = ac.name
            indigo.server.log('action to be executed when this plugin shuts down: "'+ self.shutDownActionName+'"; id= '+str(self.shutDownAction)) 
        else:
            indigo.server.log('no action to be executed when this plugin shuts down') 
        
        return True, valuesDict

#	def		(self):
#		self.myLog(255,u"getPrefsConfigUiValues called " )



####-----------------  shutdown action           ---------
    def filterActions(self, valuesDict=None, typeId=""):
        xlist = []
        for item in indigo.actionGroups:
            xlist.append((item.id,item.name))
        xlist.append((0,"-none"))
        return xlist



####-----------------  shutdown action           ---------
    def shutdown(self):
     # do any cleanup necessary before exiting
    
        #look at logfile and searching for:
        ##    Quitting Indigo Server - received slow quit signal
        ##    Application	Quitting Indigo Server - stopping plugins
        if self.shutDownAction == 0: return
        
        # can we find todays logfile
        logfileName = self.indigoPath + "Logs/"+datetime.datetime.now().strftime("%Y-%m-%d")+" Events.txt"
        if  not os.path.isfile(logfileName): 
            indigo.server.log("shutdown action: cant find indigo logfile, no action '"+ logfileName+"'" )
            return
        
        # yes, lets check the last lines , see if we find indigo shutting down and no plugin start afterwards
        ret = subprocess.Popen("tail -400 '"+logfileName+"'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
        if  ret.find("Quitting Indigo Server - stopping plugins") == -1 : 
            indigo.server.log("shutdown action: indigo NOT shutting down, not found  >Quitting  Indigo  Server...< " )
            return 

        foundShutdown= False
        for line in ret.split("\n"):
            #indigo.server.log(line.strip("\n")) 
            if foundShutdown or line.find("Quitting Indigo Server - stopping plugins") >-1 :
                foundShutdown= True
            if foundShutdown:
                if line.find("Loading plugin") > -1:
                    indigo.server.log("shutdown action: indigo NOT shutting down, found >loading plugin< after >Quitting  Indigo  Server...< " )
                    return
    
        if not foundShutdown:
            indigo.server.log("shutdown action: indigo not shutting down >>Quitting Indigo Server... << not in last lines of logfile" )
            return

        indigo.server.log("shutdown action: indigo IS shutting down" )
        
        #check if variable is set to no
        try:
            enabled = indigo.variables["shutdownActionEnabled"].value
            if enabled.lower() not in ["1","true","yes"]:
                if self.debugLevel > 0:
                    indigo.server.log("shutdown action: is disabled due to variable shutdownActionEnabled setting: "+enabled )
                return
        except: pass
            
        try:    action = int(self.shutDownAction)
        except: return
        
        if action == 0: 
            indigo.server.log("shutdown action: no action selected to be executed ")
            return 
        
        if self.debugLevel > 0:
            indigo.server.log('shutdown called with action: "' + self.shutDownActionName+'"; id= '+str(self.shutDownAction))
        indigo.actionGroup.execute(action)
        return 
####-----------------      END                   ---------



####-----------------   for menue aded --- lines          ---------
    def dummyCALLBACK(self):
        return


####-----------------   main loop, is dummy           ---------
    def runConcurrentThread(self):

        indigo.server.log("select or change shutdown action in plugin config")
        lastVCheckMinute =-1
        try:
            while True:
                self.sleep(55)
                mm = datetime.datetime.now().minute 
                hh = datetime.datetime.now().hour 
                if hh == 22 and mm == 36:
                    VS.versionCheck(self.pluginId,self.pluginVersion,indigo,22,33,printToLog="log")
        except: pass
        return

