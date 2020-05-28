#!/bin/bash
# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Wrapper script to run the ledgermonolith application JAR as a system daemon

SERVICE_NAME=ledgermonolith
PATH_TO_JAR=/opt/monolith/ledgermonolith.jar 
PID_PATH_NAME=/tmp/ledgermonolith-pid 
case $1 in 
start)
       echo "Starting $SERVICE_NAME ..."
  if [ ! -f $PID_PATH_NAME ]; then 
       nohup java -jar $PATH_TO_JAR /tmp 2>> /dev/null >>/dev/null &      
                   echo $! > $PID_PATH_NAME  
       echo "$SERVICE_NAME started ..."         
  else 
       echo "$SERVICE_NAME is already running ..."
  fi
;;
stop)
  if [ -f $PID_PATH_NAME ]; then
         PID=$(cat $PID_PATH_NAME);
         echo "$SERVICE_NAME stoping ..." 
         kill $PID;         
         echo "$SERVICE_NAME stopped ..." 
         rm $PID_PATH_NAME       
  else          
         echo "$SERVICE_NAME is not running ..."   
  fi    
;;    
restart)  
  if [ -f $PID_PATH_NAME ]; then 
      PID=$(cat $PID_PATH_NAME);    
      echo "$SERVICE_NAME stopping ..."; 
      kill $PID;           
      echo "$SERVICE_NAME stopped ...";  
      rm $PID_PATH_NAME     
      echo "$SERVICE_NAME starting ..."  
      nohup java -jar $PATH_TO_JAR /tmp 2>> /dev/null >> /dev/null &            
      echo $! > $PID_PATH_NAME  
      echo "$SERVICE_NAME started ..."    
  else           
      echo "$SERVICE_NAME is not running ..."    
     fi     ;;
 esac
