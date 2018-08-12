PURPOSE:    execute a specific action at shut down of indigo  in order to be able to finish things, ...    

exeute indigo action during indigo shutdown  .. triggered by shutting down this plugin   
- it will test if the indig logfile indicates a complete indigo shut down  
- look for "Quitting Indigo Server - stopping plugins"  
  then if found, tries to find  "Loading plugin" after the shutdown lines.  
  if loading plugin is found , it's not a shutdown   
  if not it will execute the selected action group (setup in config)  
