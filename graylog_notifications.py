#!/usr/bin/python
#
# == Synopsis
#
# This script returns notifications from Graylog
# And pushes them into Graphite
#
# === Workflow
# This script grabs JSON from a Graylog host,
# transforms data into valid Carbon metrics
# and delivers it into carbon
#
# Carbon only needs three things:
# <metric> <value> <timestamp>
#
# So what we do is grab the Graylog
# key as the metric, grab the Graylog value
# as the value and make up our own timestamp. Well,
# actually, that's done through time()
#
# Author  : D. Schutterop
# Email   : daniel@schutterop.nl
# Version : v0.1
#
# === HowTo
#
# Please replace the value of grayHost with the hostname
# or IP address of one of your Graylog hosts
# (or DNS RR, load balanced addresses or whatever)
#
# Replace the value of grpHost (and port) of the Carbon
# server and, if you want, change the grpDatabase to
# something that makes sense to you.
#
# Fire the script and see the data appear in Graphite
# (Creation of the database files may take some time...
#
#
import json,requests,time,socket,os,sys

runInterval = 15

grayHost    = 'graylog-cluster.localdomain'
grayPort    = 12900
grayUser    = 'graphite' # Read only user!
grayPass    = 'graphite'

grpHost     = 'graphite.localdomain'
grpPort     = 2003
grpDatabase = 'graylog'

#Suppress SSL warnings generated when contacting Foreman
requests.packages.urllib3.disable_warnings()

def grayGetData(grayHost,grayPort):
  grayUrl     = "http://%s:%s/system/notifications" % (grayHost,grayPort)
  grayHeaders = {'Content-type': 'application/json'}
  grayRequest = requests.get(grayUrl, verify=False, auth=(grayUser,grayPass), headers=grayHeaders)

  return json.loads(grayRequest.text)

def grpPutMessage(grpMetricKey,grpMetricValue):
  metricPrepend = grpDatabase
  metricAppend  = grpMetricKey
  metricKey     = "%s.%s" % (metricPrepend,grpMetricKey)
  metricTime    = int(time.time())

  metricValue   = grpMetricValue

  return "%s %s %s" % (metricKey,metricValue,metricTime)

def run(runInterval):
  while True:
    grpSocket = socket.socket()
    grpSocket.connect((grpHost,grpPort))

    grayData = grayGetData(grayHost,grayPort)

    message = ' '

    for listItem in grayData:
      message = "\n %s %s" % (grpPutMessage(listItem,grayData[listItem]),message)

    message = "%s \n" % (message)

    grpSocket.sendall(message)
    grpSocket.close()

    time.sleep(runInterval)

if __name__ == "__main__":

  procPid = os.fork()

  if procPid != 0:
    sys.exit(0)

  print ("Running %s every %s seconds in the background." % (__file__,runInterval))

  run(runInterval)
