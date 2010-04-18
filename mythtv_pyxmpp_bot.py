#!/usr/bin/env python

import datetime
import MySQLdb
import re
import urllib
import time
import datetime
import os

from buttons_pyxmpp_bot_stub import BasicBot

# required to talk to mythtv
import telnetlib

class MythBot(BasicBot):
    
  def __init__(self, client):
    self.client = client
    self.nowplaying = None
    self.lastchanged=0
    self.database={}
    self.defaultpingback=None
    self.defaultrecommender=None
    self.currentJID=None
    self.mypass = "196NYOxZ"
    try:
       self.mypass = os.environ["MYTHMYSQLPASS"]
    except(Exception):
       print "No mysql password found (MYTHMYSQLPASS, copy it from /etc/myth/config.xml please!)"

  def plus(self):
    body = self.send_command("key up")
    print "plus called"
    return body

  def minu(self):
    body = self.send_command("key down")
    print "minu called" 
    return body
    
  def righ(self):
    body = self.send_command("key right")
    print "righ called"
    return body
   
  def left(self):
    body = self.send_command("key left")
    print "left called"
    return body

  def plpz(self):
    body = self.send_command("key P")
    print "plpz called"
    return body

  def ffwd(self):
    body = self.send_command("key >")
    print "ffwd called"
    return body 

  def rewd(self):
    body = self.send_command("key <")
    print "rewd called"
    return body

  def menu(self):
    m = self.send_command("key M")
    time.sleep(1)
    body = self.send_command("key enter")
    print "menu called"
    return body
   
  def loud(self):
    time.sleep(1)
    body = self.send_command("key [")
    print "loud called"
    return body

  def hush(self):
    time.sleep(1)
    body = self.send_command("key ]")
    print "hush called"
    return body

  def info(self):
    body = self.send_command("key i")
    time.sleep(1)
    body = self.send_command("key i")
    print "hush called"
    return body

  def okay(self):
    print "okay called"
    # if we are in the epg, send one set of commands, else send 'enter'
    # first check where we are 
    res = self.send_command("query location")
    arr = res.split(",")
    print "location str ",arr[2]
    m = re.search('Playback', arr[2])
    print " status: ",m
    if(m):
       self.send_command("key enter")
       body="Changing channel"
    else:
       self.send_command("key X")
       time.sleep(2)
       body = self.send_command("key escape")
       # we have probably changed channel
       # update our now playing
       time.sleep(1)
       self.do_now_playing(False)
       return body


#####
# Talking to the Mythtv telnet
####

  def send_command(self,cmd):
    cmd = cmd.lstrip(' ')
    print "GOT command ",cmd
    HOST = "127.0.0.1"
    PORT = 6546
    tn = telnetlib.Telnet(HOST, PORT)
    print "sending command ",str(cmd)+"\r\n"
    tn.write(str(cmd)+"\r\n")
    res = tn.expect(['INVALID','OK'],3)
    output = str(res)
    print output
    output = output.replace("MythFrontend Network Control","")
    output = output.replace("---------------------------------","")
    output = output.replace("Type 'help' for usage information","")
    output = output.replace("\\r\\n","")
    output = output.replace("#","")
    tn.close()
    return output

####
# Get what is playing now
####

  def do_now_playing(self,send_event):
    output = self.send_command("query location")
    results= {}
    arr = output.rsplit(" ")
    print len(arr)," ",str(arr)
    if(len(arr)>10):                                          
      channel = arr[9]
      results["channum"]=arr[9]
      dt = arr[10]
      dtnow = datetime.datetime.now()
      dtnfmt = dtnow.strftime("%Y-%m-%d %H:%M:%S")
      results["datetime"]=dt

      db = MySQLdb.connect(host="localhost", user="mythtv", passwd=self.mypass,db="mythconverg")
      cursor = db.cursor()
      cursor.execute("select title,starttime,callsign from program,channel where program.chanid=channel.chanid and starttime <= '"+dtnfmt+"' and endtime > '"+dtnfmt+"' and program.chanid='"+arr[9]+"' limit 1;")

      result = cursor.fetchall()
      record = result[0] 
      print "RECORD",str(record)

      res2=""
      if (record!=""):
        secs = record[1]
        diff_secs=dtnow-secs
        print "SECS",secs,"dtnow",dtnow,"diff",diff_secs

#d1str = "2010-04-16 17:15:00"
#d2 = datetime.datetime.now()
#print "comparing",d1.__class__,"and",d2.__class__
#delta = d2 - d1
#print "secs",delta.seconds,"mins",delta.seconds/60

        results["secs"]=diff_secs.seconds
        ch = record[2]
        ch = ch.lower()
        ch = ch.replace(" ","")
        results["channel"]=ch
        t = record[0]
        results["title"]=t

        if (re.match("bbc", ch)):
           u = "http://dev.notu.be/2009/10/bbc/info?channel="+ch
           print "u",u
           data2 = urllib.urlopen(u).read()
           results["pid"]=data2
           print data2,"...data2"
           progs = "http://www.bbc.co.uk/programmes/"
        else:
           data2=None
        if (send_event):
           print "should send event here"           
           self.send_event(results, "Watching",None)
        self.nowplaying=results
        print "returning results"
    return results

####
# send an event to the beancounter specificed by this user
####

  def send_event(self, event, e_type,user):
#    u = "http://dev.notu.be/2009/10/bbc/info?channel="+ch
#    data2 = urllib.urlopen(u).read()
    event["type"]=e_type
    jid =self.currentJID
    event["username"]=jid.node+"@"+jid.domain
    print "sending event",e_type,str(event)
    params = urllib.urlencode(event)
    if self.defaultpingback:
       f = urllib.urlopen(self.defaultpingback, params)
       ff = f.read()
       print ff
    else:
       print "no event sent - no defaultpingback set"

####
# Send a bookmark to delicious - requires username and password
####

  def do_bookmark(self):
    data2 = self.do_now_playing(False)
    print "got data for bookmarking"
    if (data2):
      # wait one sec
      time.sleep(1)
      # do delicious on it
      uu=None
      pw=None
      uu="notube"
      pw="bean09"
      if(uu!="" and pw!=""):
        progs = "http://www.bbc.co.uk/programmes/"
        progsnonbbc = "http://notube.tv/programmes/"
        delicious_url_1="https://"+uu+":"+pw+"@api.del.icio.us/v1/posts/add?url="
        if data2.has_key("pid"):
           q=progs+""+data2["pid"]+"#"+str(data2["secs"])
        else:
           titl = data2["title"]
           titl = titl.replace(" ","_")
           q=progsnonbbc+"#{titl}#"+str(data2["secs"])
        delicious_url_2=urllib.quote_plus(q)+"&description="+urllib.quote_plus(data2["title"]+" ("+str(data2["secs"]/60)+" minutes in)")+"&tags=tv&tags=mythtv&tags=notube"
        delicious_url= delicious_url_1+delicious_url_2
        z = urllib.urlopen(delicious_url).read()
        res2= "bookmarked "+data2["title"]
        event = self.nowplaying
        if (self.nowplaying == None):
          event = {}
        jid = self.currentJID
        user = jid.node+"@"+jid.domain
        event["username"]=user
        print "sending event","Bookmarked",str(event)
        self.send_event( event, "Bookmarked", user)
##send an alert to screen
        st = 'mythtvosd --template=alert --alert_text="Bookmarked"'
        os.system(st)
      else:
        res2 = "could not bookmark "+data2["title"]+" - no username / password"
      return res2
    else:
      res2 = "no bookmark created - not playing anything at the moment"
      return res2


