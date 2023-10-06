#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# show sql data in logfile  Plugin
# Developed by Karl Wachs
# karlwachs@me.com

import os, sys, subprocess, pwd, copy, datetime, time
from checkIndigoPluginName import checkIndigoPluginName 
import logging
import platform

try:
	unicode("x")
except:
	unicode = str

'''
PURPOSE:	execute a specific action at shut down of indigo  in order to be able to finish things, ... 

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

		self.pluginShortName			= "shutdown"
 ###############  common for all plugins ############
		self.getInstallFolderPath		= indigo.server.getInstallFolderPath()+"/"
		self.indigoPath					= indigo.server.getInstallFolderPath()+"/"
		self.indigoRootPath 			= indigo.server.getInstallFolderPath().split(u"Indigo")[0]
		self.pathToPlugin 				= self.completePath(os.getcwd())

		major, minor, release 			= map(int, indigo.server.version.split(u"."))
		self.indigoVersion 				= float(major)+float(minor)/10.
		self.indigoRelease 				= release

		self.pluginVersion				= pluginVersion
		self.pluginId					= pluginId
		self.pluginName					= pluginId.split(".")[-1]
		self.myPID						= os.getpid()
		self.pluginState				= u"init"

		self.myPID 						= os.getpid()
		self.MACuserName				= pwd.getpwuid(os.getuid())[0]

		self.MAChome					= os.path.expanduser(u"~")
		self.userIndigoDir				= self.MAChome + u"/indigo/"
		self.indigoPreferencesPluginDir = self.getInstallFolderPath+u"Preferences/Plugins/"+self.pluginId+"/"
		self.indigoPluginDirOld			= self.userIndigoDir + self.pluginShortName+"/"
		self.PluginLogFile				= indigo.server.getLogsFolderPath(pluginId=self.pluginId) +u"/plugin.log"

		formats=	{   logging.THREADDEBUG: u"%(asctime)s %(msg)s",
						logging.DEBUG:		u"%(asctime)s %(msg)s",
						logging.INFO:		u"%(asctime)s %(msg)s",
						logging.WARNING:	u"%(asctime)s %(msg)s",
						logging.ERROR:		u"%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s",
						logging.CRITICAL:	u"%(asctime)s.%(msecs)03d\t%(levelname)-12s\t%(name)s.%(funcName)-25s %(msg)s" }

		date_Format = { logging.THREADDEBUG: u"%Y-%m-%d %H:%M:%S",		# 5
						logging.DEBUG:		u"%Y-%m-%d %H:%M:%S",		# 10
						logging.INFO:		u"%Y-%m-%d %H:%M:%S",		# 20
						logging.WARNING:	u"%Y-%m-%d %H:%M:%S",		# 30
						logging.ERROR:		u"%Y-%m-%d %H:%M:%S",		# 40
						logging.CRITICAL:	u"%Y-%m-%d %H:%M:%S" }		# 50
		formatter = LevelFormatter(fmt=u"%(msg)s", datefmt=u"%Y-%m-%d %H:%M:%S", level_fmts=formats, level_date=date_Format)

		self.plugin_file_handler.setFormatter(formatter)
		self.indiLOG = logging.getLogger(u"Plugin")  
		self.indiLOG.setLevel(logging.THREADDEBUG)

		self.indigo_log_handler.setLevel(logging.INFO)

		self.indiLOG.log(20,u"initializing  ... ")
		self.indiLOG.log(20,u"path To files:          =================")
		self.indiLOG.log(10,u"indigo                  {}".format(self.indigoRootPath))
		self.indiLOG.log(10,u"installFolder           {}".format(self.indigoPath))
		self.indiLOG.log(10,u"plugin.py               {}".format(self.pathToPlugin))
		self.indiLOG.log(10,u"indigo                  {}".format(self.indigoRootPath))
		self.indiLOG.log(20,u"detailed logging        {}".format(self.PluginLogFile))
		self.indiLOG.log(20,u"testing logging levels, for info only: ")
		self.indiLOG.log( 0,u"logger  enabled for     0 ==> TEST ONLY ")
		self.indiLOG.log( 5,u"logger  enabled for     THREADDEBUG    ==> TEST ONLY ")
		self.indiLOG.log(10,u"logger  enabled for     DEBUG          ==> TEST ONLY ")
		self.indiLOG.log(20,u"logger  enabled for     INFO           ==> TEST ONLY ")
		self.indiLOG.log(30,u"logger  enabled for     WARNING        ==> TEST ONLY ")
		self.indiLOG.log(40,u"logger  enabled for     ERROR          ==> TEST ONLY ")
		self.indiLOG.log(50,u"logger  enabled for     CRITICAL       ==> TEST ONLY ")
		self.indiLOG.log(10,u"Plugin short Name       {}".format(self.pluginShortName))
		self.indiLOG.log(10,u"my PID                  {}".format(self.myPID))	 
		self.indiLOG.log(10,u"Achitecture             {}".format(platform.platform()))	 
		self.indiLOG.log(10,u"OS                      {}".format(platform.mac_ver()[0]))	 
		self.indiLOG.log(10,u"indigo V                {}".format(indigo.server.version))	 
		self.indiLOG.log(10,u"python V                {}.{}.{}".format(sys.version_info[0], sys.version_info[1] , sys.version_info[2]))	 


		self.pythonPath = ""
		if sys.version_info[0] >2:
			if os.path.isfile(u"/Library/Frameworks/Python.framework/Versions/Current/bin/python3"):
				self.pythonPath				= u"/Library/Frameworks/Python.framework/Versions/Current/bin/python3"
		else:
			if os.path.isfile(u"/usr/local/bin/python"):
				self.pythonPath				= u"/usr/local/bin/python"
			elif os.path.isfile(u"/usr/bin/python2.7"):
				self.pythonPath				= u"/usr/bin/python2.7"
		if self.pythonPath == "":
				self.indiLOG.log(40,u"FATAL error:  none of python versions 2.7 3.x is installed  ==>  stopping {}".format(self.pluginId))
				self.quitNOW = "none of python versions 2.7 3.x is installed "
				exit()
		self.indiLOG.log(20,u"using '{}' for utily programs".format(self.pythonPath))


	########################################
	def __del__(self):
		indigo.PluginBase.__del__(self)
	
	########################################
	def startup(self):

		if not checkIndigoPluginName(self, indigo): 
			exit() 

		self.debugLevel	=  int(self.pluginPrefs.get(	"debugLevel", 255))

		try:	self.shutDownAction = int(self.pluginPrefs.get(		"shutDownAction",	0))
		except: self.shutDownAction = 0
		self.shutDownActionName  = ""

		if self.shutDownAction !=0:
			ac = indigo.actionGroups[self.shutDownAction]
			self.shutDownActionName = ac.name
			self.indiLOG.log(20,'action to be executed when this plugin shuts down: "'+ self.shutDownActionName+'"; id= '+str(self.shutDownAction)) 
		else:
			self.indiLOG.log(20,'no action to be executed when this plugin shuts down') 
		return




####-----------------  set the geneeral config parameters---------
	def validatePrefsConfigUi(self, valuesDict):

		self.debugLevel		= int(valuesDict[u"debugLevel"])
			
		try:	self.shutDownAction = int(valuesDict["shutDownAction"])
		except: self.shutDownAction = 0
		if self.shutDownAction != 0:
			ac = indigo.actionGroups[self.shutDownAction]
			self.shutDownActionName = ac.name
			self.indiLOG.log(20,'action to be executed when this plugin shuts down: "'+ self.shutDownActionName+'"; id= '+str(self.shutDownAction)) 
		else:
			self.indiLOG.log(20,'no action to be executed when this plugin shuts down') 
		
		return True, valuesDict

#	def		(self):
#		self.myLog(255,u"getPrefsConfigUiValues called " )



####-----------------  shutdown action		   ---------
	def filterActions(self, valuesDict=None, typeId=""):
		xlist = []
		for item in indigo.actionGroups:
			xlist.append((item.id,item.name))
		xlist.append((0,"-none"))
		return xlist



####-----------------  shutdown action		   ---------
	def shutdown(self):
	 # do any cleanup necessary before exiting
	
		#look at logfile and searching for:
		##	Quitting Indigo Server - received slow quit signal
		##	Application	Quitting Indigo Server - stopping plugins
		if self.shutDownAction == 0: return
		
		# can we find todays logfile
		logfileName = self.indigoPath + "Logs/"+datetime.datetime.now().strftime("%Y-%m-%d")+" Events.txt"
		if  not os.path.isfile(logfileName): 
			self.indiLOG.log(20,"shutdown action: cant find indigo logfile, no action '{}'".format(logfileName) )
			return
		
		# yes, lets check the last lines , see if we find indigo shutting down and no plugin start afterwards
		ret = subprocess.Popen("tail -400 '"+logfileName+"'", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[0]
		if  ret.find("Quitting Indigo Server - stopping plugins") == -1 : 
			self.indiLOG.log(20,"shutdown action: indigo NOT shutting down, not found  >Quitting  Indigo  Server...< " )
			return 

		foundShutdown= False
		for line in ret.split("\n"):
			#indigo.server.log(line.strip("\n")) 
			if foundShutdown or line.find("Quitting Indigo Server - stopping plugins") >-1 :
				foundShutdown= True
			if foundShutdown:
				if line.find("Loading plugin") > -1:
					self.indiLOG.log(20,"shutdown action: indigo NOT shutting down, found >loading plugin< after >Quitting  Indigo  Server...< " )
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
					self.indiLOG.log(20,"shutdown action: is disabled due to variable shutdownActionEnabled setting: {}".format(enabled) )
				return
		except: pass
			
		try:	action = int(self.shutDownAction)
		except: return
		
		if action == 0: 
			indigo.server.log("shutdown action: no action selected to be executed ")
			return 
		
		if self.debugLevel >0:
			self.indiLOG.log(20,'shutdown called with action: "{}"; id= {}'.format(self.shutDownActionName, self.shutDownAction))
		indigo.actionGroup.execute(action)
		return 
####-----------------	  END				   ---------



####-----------------   for menue aded --- lines		  ---------
	def dummyCALLBACK(self):
		return

####-----------------	 ---------
	def completePath(self,inPath):
		if len(inPath) == 0: return ""
		if inPath == " ":	 return ""
		if inPath[-1] !="/": inPath +="/"
		return inPath

####-----------------   main loop, is dummy		   ---------
	def runConcurrentThread(self):

		self.indiLOG.log(20,"select or change shutdown action in plugin config")
		try:
			while True:
				self.sleep(55)
		except: pass
		return
####-----------------  valiable formatter for differnt log levels ---------
# call with: 
# formatter = LevelFormatter(fmt='<default log format>', level_fmts={logging.INFO: '<format string for info>'})
# handler.setFormatter(formatter)
class LevelFormatter(logging.Formatter):
	def __init__(self, fmt=None, datefmt=None, level_fmts={}, level_date={}):
		self._level_formatters = {}
		self._level_date_format = {}
		for level, format in level_fmts.items():
			# Could optionally support level names too
			self._level_formatters[level] = logging.Formatter(fmt=format, datefmt=level_date[level])
		# self._fmt will be the default format
		super(LevelFormatter, self).__init__(fmt=fmt, datefmt=datefmt)
		return

	def format(self, record):
		if record.levelno in self._level_formatters:
			return self._level_formatters[record.levelno].format(record)

		return super(LevelFormatter, self).format(record)


