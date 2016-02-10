#!/usr/bin/python
#
# == Synopsis
#
# Script to get index data from elasticsearch
# through the ES API.
#
# Because I work with multiple scripts to push data
# into Carbon, I insert the data into a separate
# Carbon database (elasticsearch.index)
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
grpDatabase = 'elasticsearch.index'

#Suppress SSL warnings generated when contacting Foreman
requests.packages.urllib3.disable_warnings()

def elaGetData(elaHost,elaPort):
  elaUrl     = "http://%s:%s/_cat/indices?bytes=b" % (elaHost,elaPort)
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

    message       = ''
    greenIndex    = 0
    yellowIndex   = 0
    redIndex      = 0
    numDocs       = 0
    docsDeleted   = 0
    priStoreSizeB = 0
    storeSizeB    = 0
    primaryShards = 0
    replicas      = 0

    for listItem in elaData:

      numDocs       += int(listItem['docs.count'])
      docsDeleted   += int(listItem['docs.deleted'])
      storeSizeB    += int(listItem['store.size'])
      priStoreSizeB += int(listItem['pri.store.size'])
      primaryShards += int(listItem['pri'])
      replicas      += int(listItem['rep'])

      if listItem['health'] == 'green':
        greenIndex += 1
      elif listItem['health'] == 'yellow':
        yellowIndex += 1
      elif listItem['health'] == 'red':
        redIndex += 1

    storeSizeG    = round((storeSizeB / 1073741824.0),2)
    storeSizeM    = round((storeSizeB / 1000000),2)
    priStoreSizeG = round((priStoreSizeB / 1073741824.0),2)
    priStoreSizeM = round((priStoreSizeB / 1000000),2)
    repStoreSizeB = storeSizeB - priStoreSizeB
    repStoreSizeG = round((repStoreSizeB / 1073741824.0),2)
    repStoreSizeM = round((repStoreSizeB / 1000000),2)


    message = "\n %s %s" % (grpPutMessage('total_indices',len(elaData)),message)
    message = "\n %s %s" % (grpPutMessage('green_index',greenIndex),message)
    message = "\n %s %s" % (grpPutMessage('yellow_index',yellowIndex),message)
    message = "\n %s %s" % (grpPutMessage('red_index',redIndex),message)
    message = "\n %s %s" % (grpPutMessage('num_docs',numDocs),message)
    message = "\n %s %s" % (grpPutMessage('deleted_docs',docsDeleted),message)
    message = "\n %s %s" % (grpPutMessage('total_store_size_bytes',storeSizeB),message)
    message = "\n %s %s" % (grpPutMessage('total_store_size_gigabytes',storeSizeG),message)
    message = "\n %s %s" % (grpPutMessage('total_store_size_megabytes',storeSizeM),message)
    message = "\n %s %s" % (grpPutMessage('primary_store_size_bytes',priStoreSizeB),message)
    message = "\n %s %s" % (grpPutMessage('primary_store_size_gigabytes',priStoreSizeG),message)
    message = "\n %s %s" % (grpPutMessage('primary_store_size_megabytes',priStoreSizeM),message)
    message = "\n %s %s" % (grpPutMessage('replica_store_size_bytes',repStoreSizeB),message)
    message = "\n %s %s" % (grpPutMessage('replica_store_size_gigabytes',repStoreSizeG),message)
    message = "\n %s %s" % (grpPutMessage('replica_store_size_megabytes',repStoreSizeM),message)
    message = "\n %s %s" % (grpPutMessage('primary_shards',primaryShards),message)
    message = "\n %s %s" % (grpPutMessage('replicas',replicas),message)

    grpSocket.sendall(message)
    grpSocket.close()

    time.sleep(runInterval)

if __name__ == "__main__":

  procPid = os.fork()

  if procPid != 0:
    sys.exit(0)

  print ("Running %s every %s seconds in the background." % (__file__,runInterval))

  run(runInterval)
