#!/usr/bin/python
#
# == Synopsis
#
# Script to get cluster data from elasticsearch
# through the ES API.
#
# Because I work with multiple scripts to push data
# into Carbon, I insert the data into a separate
# Carbon database (elasticsearch.cluster)
#
# === Workflow
# This script grabs JSON from your elasticsearch
# cluster (_cluster/health), transforms data into
# valid Carbon metrics and delivers it into carbon
#
# Carbon only needs three things:
# <metric> <value> <timestamp>
#
# So what we do is grab the elasticsearch
# key as the metric, grab the elasticsearch value
# as the value and make up our own timestamp. Well,
# actually, that's done through time()
#
# Author  : D. Schutterop
# Email   : daniel@schutterop.nl
# Version : v0.1
#
# === HowTo
#
# Please replace the value of elaHost with the hostname
# or IP address of one of your ElasticSearch hosts
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

elaHost     = 'elasticsearch.localdomain'
elaPort     = 9200

grpHost     = 'graphite.localdomain'
grpPort     = 2003
grpDatabase = 'elasticsearch.cluster'

#Suppress SSL warnings generated when contacting Foreman
requests.packages.urllib3.disable_warnings()

def elaGetData(elaHost,elaPort):
  elaUrl     = "http://%s:%s/_cluster/health" % (elaHost,elaPort)
  elaHeaders = {'Content-type': 'application/json'}
  elaRequest = requests.get(elaUrl, verify=False, headers=elaHeaders)

  return json.loads(elaRequest.text)

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

    elaData = elaGetData(elaHost,elaPort)
    elaData['cluster_status'] = elaData.pop('status')
    message = ' '

    for listItem in elaData:
      elaData['cluster_name'] = 0

      if listItem == 'timed_out':
        if elaData['timed_out'] == True:
          elaData['timed_out'] = 1
        else:
          elaData['timed_out'] = 0

      if listItem == 'cluster_status':
        if elaData[listItem] == 'green':
          elaData[listItem] = 0
        if elaData[listItem] == 'yellow':
          elaData[listItem] = 1
        if elaData[listItem] == 'red':
          elaData[listItem] = 2

      message = "\n %s %s" % (grpPutMessage(listItem,elaData[listItem]),message)

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
