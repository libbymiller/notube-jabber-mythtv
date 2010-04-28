#!/usr/bin/env python

import datetime
import MySQLdb
import re
import urllib
import time
import datetime
import os
import random
import subprocess
from threading import Timer

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
    self.myFullJID=None
    self.mypass = None
    try:
       self.mypass = os.environ["MYTHMYSQLPASS"]
    except(Exception):
       print "No mysql password found (MYTHMYSQLPASS, copy it from /etc/myth/config.xml please!)"

  def plus(self):
    body = self.send_command("key up")
    print "plus called ",self.myFullJID
    return body

  def minu(self):
    body = self.send_command("key down")
    print "minu called",self.myFullJID
    return body
    
  def righ(self):
    body = self.send_command("key right")
    print "righ called",self.myFullJID
    return body
   
  def left(self):
    body = self.send_command("key left")
    print "left called",self.myFullJID
    return body

  def plpz(self):
    body = self.send_command("key P")
    print "plpz called",self.myFullJID
    return body

  def ffwd(self):
    body = self.send_command("key >")
    print "ffwd called",self.myFullJID
    return body 

  def rewd(self):
    body = self.send_command("key <")
    print "rewd called",self.myFullJID
    return body

  def menu(self):
    m = self.send_command("key M")
    time.sleep(1)
    body = self.send_command("key enter")
    print "menu called",self.myFullJID
    return body
   
  def loud(self):
    time.sleep(1)
    body = self.send_command("key [")
    print "loud called",self.myFullJID
    return body

  def hush(self):
    time.sleep(1)
    body = self.send_command("key ]")
    print "hush called",self.myFullJID
    return body

  def info(self):
    body = self.send_command("key i")
    time.sleep(1)
    body = self.send_command("key i")
    print "info called",self.myFullJID
    return body

  def okay(self):
    print "okay called",self.myFullJID
    # if we are in the epg, send one set of commands, else send 'enter'
    # first check where we are 
    res = self.send_command("query location")
#    arr = res.split(" ")
    print "location str ",res
    m = re.search('Playback', res)
    print " status: ",m
    if(m):
       self.send_command("key enter")
       body="Enter selected"
    else:
       self.send_command("key X")
       time.sleep(2)
       c = self.send_command("key escape")
       # we have probably changed channel
       # update our now playing
#       time.sleep(1)
#       self.do_now_playing(False)
#       print body.__class__
       body ="Changing channel"
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
#   for i in res:
#     print "i is "+str(i)
    output = str(res[2])
#   print output
    output = output.replace("MythFrontend Network Control","")
    output = output.replace("---------------------------------","")
    output = output.replace("Type 'help' for usage information","")
    output = output.replace("\\r\\n","")
    output = output.replace("#","")
    output = re.sub("\n","",output)
    output = re.sub("\r","",output)
    output = re.sub("^\s*","",output)
    tn.close()
    print "OUTPUT is "+output
    #print output.__class__
    return output

####
# Get what is playing now
####

  def do_now_playing(self,send_event):
    print "XXXXXX starting timer",self.myFullJID
    #t = Timer(600.0, self.nowp_rpt)
    #t.start()

    output = self.send_command("query location")
    #print "OOOOOOO",output
    #print output.__class__
    results= {}
    arr = output.rsplit(" ")
    print len(arr)," ",str(arr)
    if(len(arr)>10):                                          
      channel = arr[6]
      results["channum"]=arr[6]
      dt = arr[8]
      dtnow = datetime.datetime.now()
      dtnfmt = dtnow.strftime("%Y-%m-%d %H:%M:%S")
      results["datetime"]=dt

      db = MySQLdb.connect(host="localhost", user="mythtv", passwd=self.mypass,db="mythconverg")
      cursor = db.cursor()
      q ="select title,starttime,callsign from program,channel where program.chanid=channel.chanid and starttime <= '"+dtnfmt+"' and endtime > '"+dtnfmt+"' and program.chanid='"+channel+"' limit 1;"
      print q
      cursor.execute(q)

      result = cursor.fetchall()
      if len(result)==0:
        print "No result for sql query - did you run mythfilldb or check EIT?"
      else:
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
    # this keeps crashing and doesn;t actually send events yet so commemnting out
    #event["type"]=e_type
    #jid =self.myFullJID
    #event["username"]=jid.node+"@"+jid.domain
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
    print "got data for bookmarking",self.myFullJID
    if (data2):
      # wait one sec
      time.sleep(1)
      # do delicious on it
      uu=None
      pw=None
      uu="notube"
      try:
         pw = os.environ["NOTUBEDELICIOUSPASS"]
      except(Exception):
         print "No delicious password found; set it in NOTUBEDELICIOUSPASS"
      if(uu!="" and pw!=""):
        print "bookmarking..."
        progs = "http://www.bbc.co.uk/programmes/"
        progsnonbbc = "http://purl.org/identifiers/epg/broadcast/"
        delicious_url_1="https://"+uu+":"+pw+"@api.del.icio.us/v1/posts/add?url="
        desc=""
        lup = ""
        if data2.has_key("pid"):
           q=progs+""+data2["pid"]+"#"+str(data2["secs"])
        else:
           titl = data2["title"]
           titl = titl.replace(" ","_")
           q=progsnonbbc+""+titl+"#"+str(data2["secs"])
        delicious_url_2=urllib.quote_plus(q)+"&description="+urllib.quote_plus(data2["title"]+" ("+str(data2["secs"]/60)+" minutes in)")+"&tags="+urllib.quote_plus("tv mythtv notube")
        delicious_url= delicious_url_1+delicious_url_2
        z = urllib.urlopen(delicious_url).read()
        res2= "Bookmarked "+data2["title"]
        event = self.nowplaying
        if (self.nowplaying == None):
          event = {}
        jid = self.myFullJID
        # this keeps crashing and doesn;t actually send events yet so commemnting out
        #user = jid.node+"@"+jid.domain
        #event["username"]=user
        print "sending event","Bookmarked",str(event)
        #self.send_event( event, "Bookmarked", user)
        self.send_event( event, "Bookmarked", None)
##send an alert to screen
        st = 'mythtvosd --template=alert --alert_text=\"'+res2+'\"'

#Bookmarked "+data2["title"]'
        os.system(st)
      else:
        res2 = "could not bookmark "+data2["title"]+" - no username / password"
      return res2
    else:
      res2 = "no bookmark created - not playing anything at the moment"
      return res2


  def do_qr(self):
    pin = random.randint(1000, 9999)
    fn = "q"+str(pin)+".png"
    jstring = str(self.myFullJID)
    print "bot ",jstring
# Need to add some stuff so that we can accept things with this pin
    ar = ["qrencode", "-o", fn, "-s", "20", "xmpp:"+unicode(jstring)+"'"]
#+"/q"+str(pin)+
    print ar
    res = subprocess.Popen(ar)
    cm = ["xli", "-display", ":0.0", "-fullscreen", fn]
    time.sleep(1)
    foo = subprocess.Popen(cm)
    time.sleep(10)
    foo.terminate()
    print foo
    return "Popping up a QR code for"+jstring+"#"+str(pin)," ",self.myFullJID

  def nowp_rpt(self):
     print "nowp requested in 5 minutes"
     self.do_now_playing(None)

    

