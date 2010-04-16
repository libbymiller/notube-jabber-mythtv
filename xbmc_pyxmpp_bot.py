#!/usr/bin/env python

from pyxmpp.all import JID,Iq,Presence,Message,StreamError
import urllib
import re
import time
import datetime
import MySQLdb
from buttons_pyxmpp_bot_stub import BasicBot

class XBMCBot(BasicBot):
    
  def __init__(self, client):
    self.client = client
    self.nowplaying = None
    self.lastchanged=0
    self.database={}
    self.defaultpingback=None
    self.defaultrecommender=None
    self.currentJID=None
    self.mypass = ""
    try:
       self.mypass = os.environ["MYTHMYSQLPASS"]
    except(Exception):
       print "No mysql password found (MYTHMYSQLPASS, copy it from /etc/myth/config.xml please!)"

  def plus(self):
    uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(3)"
    resu = urllib.urlopen(uuu).read()
    body = self.cleanresult(resu)
    print "plus called"
    return body

  def minu(self):
    uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(4)"
    resu = urllib.urlopen(uuu).read()
    body = self.cleanresult(resu)
    print "minu called" 
    return body
    
  def righ(self):
    uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(2)"
    resu = urllib.urlopen(uuu).read()
    body = self.cleanresult(resu)
    print "righ called"
    return body
   
  def left(self):
    uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(1)"
    resu = urllib.urlopen(uuu).read()
    body = self.cleanresult(resu)
    print "left called"
    return body

  def plpz(self):
    uuuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Pause()"
    resuu = urllib.urlopen(uuuu).read()
    body = self.cleanresult(resuu)
    print "plpz called"
    return body

  def ffwd(self):
    uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(77)"
    resu = urllib.urlopen(uuu).read()
    body = self.cleanresult(resu)
    print "ffwd called"
    return body 

  def rewd(self):
    uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(78)"
    resu = urllib.urlopen(uuu).read()
    body = self.cleanresult(resu)
    print "rewd called"
    return body

  def menu(self):
    uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=ExecBuiltIn(ActivateWindow(10024))"
    body = urllib.urlopen(uuu).read()
    print "menu called"
    return body
   
  def loud(self):
    print "loud called (not implemented yet)"
    return "loud called (not implemented yet)"

  def hush(self):
    time.sleep(1)
    print "hush called  (not implemented yet)"
    return "hush called  (not implemented yet)"

  def info(self):
    print "info called  (not implemented yet)"
    return "info called  (not implemented yet)"

  def okay(self):
    print "okay called"
    uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=Action(7)"
    resu = urllib.urlopen(uuu).read()
    # update our now playing
    self.do_now_playing(False)
    body = self.cleanresult(resu)
    return body

####
# xbmc-specific
####

  def cleanresult(self, body):
     body = body.replace("<html>","")
     body = body.replace("</html>","")
     body = body.replace("<li>","")
     body = body.replace("\n","")
     return body


####
# Get what is playing now
####

  def do_now_playing(self,send_event):
# http://localhost:8080/xbmcCmds/xbmcHttp?command=tcurrentlyplaying
# title is gettable
# channel has to be hack parsed
# not sure about whether we nede to bother with datetime
# else we'll have to get it from the database

    title = None
    channel = None
    uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=getcurrentlyplaying"
    resu = urllib.urlopen(uuu).read()
    print resu
    results= {}
# get the title
    data = resu.split("<li>")
# look for Show Title:
    for d in data:
       if (re.match("Show Title",d)):
           title = d.replace("Show Title:","")
           title = title.replace("\n","")
           results["title"]=title
#          print title
#look for title and find the last part of it after '-'
       if (re.match("Title",d)):
           z = re.search(".* - (.*?)$",d)
           channel = z.group(1)
           print "chann ",channel
           channel = channel.replace("\n","")
           results["callsign"]=channel
           results["callsign"]=channel

    if channel!=None and title!=None:
     
#@@set presence
       status = "Now playing "+title+" on "+channel
       # this doesn't seem to do anything
       self.client.get_stream().send(Presence(status=status))
       print "sending presence",status,"..\n"
##end send presence

       dtnow = datetime.datetime.now()
       dtnfmt = dtnow.strftime("%Y-%m-%d %H:%M:%S")
       db = MySQLdb.connect(host="localhost", user="mythtv", passwd=self.mypass,db="mythconverg")
       cursor = db.cursor()
       cursor.execute("select starttime from program,channel where program.chanid=channel.chanid and starttime <= '"+dtnfmt+"' and endtime > '"+dtnfmt+"' and channel.callsign='"+channel+"' limit 1;")

       result = cursor.fetchall()   
       record = result[0]
       print "RECORD",str(record)
       res2=""
       if (record!=""):
          secs = record[0]
          secsfmt = secs.strftime("%Y-%m-%d %H:%M:%S")
          results["datetime"]=secsfmt
          results["secs"]=secs-dtnow
          results["secs"]=results["secs"].seconds
          ch = channel.lower()
          ch = channel.replace(" ","")
          results["channel"]=ch

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
       print "not sending event as no defaultpingback set"


####
# Send a bookmark to delicious - requires username and password
####

  def do_bookmark(self):
    data2 = self.do_now_playing(False)
    print "got data for boomarking"
    if (data2):
      # wait one sec
      time.sleep(1)
      # do delicious on it
      uu=None
      pw=None
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
        delicious_url_2=urllib.quote_plus(q)+"&description="+urllib.quote_plus(data2["title"]+" ("+str(data2["secs"])+" seconds in)")+"&tags=tv&tags=xbmc&tags=notube"
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
        uuu = "http://localhost:8080/xbmcCmds/xbmcHttp?command=ExecBuiltIn(Notification('Bookmarked',"+data2['title']+",5))"
        resu = urllib.urlopen(uuu).read()
        res2 = self.cleanresult(resu)
      else:
        res2 = "could not bookmark "+data2["title"]+" - no username / password"
      return res2
    else:
      res2 = "no bookmark created - not playing anything at the moment"
      return res2


