# See http://pyxmpp.jajcus.net/trac/browser/trunk/examples/echobot.py for a more detailed example
# requires pyxmpp (on Ubuntu: sudo apt-get install python-pyxmpp)
import sys
#import urllib
import re
import datetime
import time
import timeit
import threading
#import os
import random
import subprocess
#import MySQLdb
import json
import locale
import codecs
import libxml2
import BeautifulSoup

from BeautifulSoup import BeautifulSoup

from pyxmpp import streamtls
from pyxmpp.all import JID,Iq,Presence,Message,StreamError
from pyxmpp.jabber.client import JabberClient
from pyxmpp.interface import implements
from pyxmpp.interfaces import IMessageHandlersProvider,IIqHandlersProvider,IPresenceHandlersProvider
from pyxmpp.iq import Iq


# required to talk to mythtv
import telnetlib


class GetIplayerThread ( threading.Thread):
  def __init__ (self, pid):
     self.pid = pid
     threading.Thread.__init__ ( self )
  def run ( self ):
     print "getIplayer thread run called",self.pid

class BasicHandler(object):
  implements(IMessageHandlersProvider,IIqHandlersProvider,IPresenceHandlersProvider)
    
  def __init__(self, client):
    self.client = client
    self.nowplaying = None
    self.lastchanged=0
    self.database={}
    self.defaultpingback=None
    self.defaultrecommender=None
    self.currentJID=None
    self.mypass = None
    try:
       self.mypass = os.environ["MYTHMYSQLPASS"]
    except(Exception):
       print "No mysql password found (MYTHMYSQLPASS, copy it from /etc/myth/config.xml please!)"

  def get_presence_handlers(self):
     print "Presence heandler called"
     return [(None, self.presence)]

  def presence(self,stanza):
      print "Presence requested"
      status=""
      if (self.nowplaying==None):
         self.nowplaying = self.do_now_playing(False)
      if (self.nowplaying.has_key("title") and self.nowplaying.has_key("channel")):
         status = "Now playing "+self.nowplaying["title"]+" on "+self.nowplaying["channel"]
      p=Presence(
          stanza_type=stanza.get_type(),
          to_jid=stanza.get_from(),
          from_jid=stanza.get_to(),
          show=stanza.get_show(),
          status=status
          )
      print "Presence is ",status
      return p


  def get_iq_get_handlers(self):
    print "handlers requested for iq ",self
    return [("query","http://buttons.foaf.tv/",self.query)]

  def get_iq_set_handlers(self):
    return [] #?

  def query(self,stanza):
    print "IQ requested"
    b=stanza.get_query()
    print "GOT an IQ",str(b.get_content())
    ty=stanza.get_type()   
    rr= "no response"
    content = b.get_content()
    if b:
       b = unicode(b)
    resp = stanza.make_result_response()
    cmd = content.lower()

# These commands are the ones that we want to use over IQ
    if cmd == "nowp":
       body = self.html_nowp()
    elif cmd == "plus":
       body = self.send_command("key up")
    elif cmd == "minu":
       body = self.send_command("key down")
    elif cmd == "righ":
       body = self.send_command("key right")
    elif cmd == "left":
       body = self.send_command("key left")

    source = "<nowp-result xmlns='http://buttons.foaf.tv/'>" + body + "</nowp-result>"        
    soup = BeautifulSoup(source)
    doc = libxml2.parseDoc(str(soup.contents[0]))
    resp.set_content(doc)
    print "IQ response is ",resp
    return resp

    
  def get_message_handlers(self):
    return [("normal", self.default)]


# These are responses to chat messages

  def default(self,stanza):
    sub=stanza.get_subject()
    b=stanza.get_body()
    ty=stanza.get_type()
    jid=stanza.get_from()
    self.currentJID = jid
    if sub:
       sub=unicode(sub)
    if b:
       b = unicode(b)
    print "Got chat message.... "+unicode(b)
    #if stanza.get_type()=="headline":
    #   # don't reply to these
    #   return True
    arr = b.split(" ")
    cmd = arr[0]
    cmd = cmd.lower() 
    print "Chat command is ",cmd

# Various chat based commands

    if cmd == "go":
       arr.pop(0)
       bbb = " ".join(arr)
       print "body ",bbb
       body = self.send_command(bbb)
    elif cmd == "p":
       body = self.do_now_playing(False)
    elif cmd == "ev":
       body = self.do_now_playing(True)
    elif cmd == "b":
       body = self.do_bookmark()
    elif cmd == "like":
       body = self.do_bookmark()
    elif cmd == "qr":
       body = self.do_qr()
    elif cmd == "plpz":
       body = self.send_command("key P")
    elif cmd == "ffwd":
       body = self.send_command("key >")
    elif cmd == "rewd":
       body = self.send_command("key <")
    elif cmd == "menu":
       m = self.send_command("key M")
       time.sleep(1)
       body = self.send_command("key enter")
    elif cmd == "plus":
       body = self.send_command("key up")
    elif cmd == "minu":
       body = self.send_command("key down")
    elif cmd == "righ":
       body = self.send_command("key right")
    elif cmd == "left":
       body = self.send_command("key left")
    elif cmd == "info":
       body = self.send_command("key I")
    elif cmd == "loud":
       time.sleep(1)
       body = self.send_command("key [")
    elif cmd == "hush":
       time.sleep(1)
       body = self.send_command("key }")
    elif cmd == "nowp":
       body = self.html_nowp()
    elif cmd == "save":
       print "arr len ",len(arr)
       if (len(arr)>1):
          pid = arr[1]
          if (re.match("^http",pid)):
             pid =pid.replace("http://www.bbc.co.uk/programmes/","")
          print "saving using get_iplayer:",pid
          GetIplayerThread(pid).start()
          body = "Trying to download "+ arr[1]
       else:
          body = "No pid found"
    elif cmd == "okay":
       print "got command OK"
       body = self.send_command("key enter")
    elif cmd == "help":
       body = "as IQ: nowp,plus,minu,righ,left; as chat: go [any telnet cmd],nowp,plus,minu,righ,left,p,ev,b,qr,plpz,ffwd,rewd,menu,loud,hush,save [bbc progs url],okay,info,help"
    else:
       body = b
    msg=Message(to_jid=stanza.get_from(),from_jid=stanza.get_to(),stanza_type=stanza.get_type(),subject=sub,body=body)
    return msg

#####
# Talking to the Mythtv telnet
####

# stub only

  def send_command(self,cmd):
    if (cmd == "query location"):
      
      return {'title': "Clifford's Puppy Days", 'pid': 'b008vhxr', 'datetime': '2010-03-25T09:15:00', 'secs': 85563, 'channum': '1002', 'channel': 'bbctwo'}
    else:
      return "Command sent:",cmd


####
# Get what is playing now
####

# stub only

  def do_now_playing(self,send_event):
    output = self.send_command("query location")
    results = output
    if (send_event):
       print "Should send watching event here"           
       self.send_event(results, "Watching")
    self.nowplaying=results
    print "returning results"
    return results

####
# send an event to the beancounter specificed by this user
####

  def send_event(self, event, e_type):
    event["type"]=e_type
    jid =self.currentJID
    event["username"]=jid.node+"@"+jid.domain
    print "sending event",e_type,str(event)


####
# Send a bookmark to delicious - requires username and password
####

#stub

  def do_bookmark(self):
    data2 = self.do_now_playing(False)
    print "got data for bookmarking", data2
    res2= "bookmarked "+data2["title"]
    self.send_event( data2, "Bookmarked")
    print "Sending alert to screen"
    return res2


####
# pop up a qr code on request
####

#stub

  def do_qr(self):
    i = random.randint(1000, 9999)
    print "bot ",self.client.jid
    fn = "q"+str(i)+".png"
    jid = self.client.jid
    jstring = jid.node+"@"+jid.domain
    print "Popping up a QR code for",jstring

####
# now playing as html
###

  def html_nowp(self):
    print "nowplaying requested"
    z = self.do_now_playing(False) 
    print "z ",z 
    if z:
      title = z["title"]
      channel = z["channel"]
      stt = z["datetime"]
      channum = z["channum"]
      extras = ""
# get the pid @@@
      if (re.match("bbc", channel)):
         u = "http://dev.notu.be/2009/10/bbc/info?channel="+channel
         pid = urllib.urlopen(u).read()
         print "u",u,"pid",pid

# query chris' stff
# http://services.notube.tv/epg/datawarehouse.php?service=getannotation&pid=b00c4frc
         if (pid):
            uu = "http://services.notube.tv/epg/datawarehouse.php?service=getannotation&pid="+pid
            j = urllib.urlopen(uu).read()
            jj = json.loads(j)
            for x in jj:
               for k, v in x.items():
                  if (k=="name" and v =="Actor"):
                     extras=extras+ "Actor: <a href='"+x["URL"]+"'>"+x["value"]+"</a><br />"
                  elif (k=="name" and v =="Director"):
                     extras=extras+ "Director: <a href='"+x["URL"]+"'>"+x["value"]+"</a><br />"
                  elif (k=="name" and v=="dbpprop:abstract"):
                     extras=extras+ "Description: "+x["value"]+"<br />"
                  elif (k=="name" and v=="skos:subject"):
                     cat = x["value"]
                     extras=extras+ "Category: <a href='"+cat+"'>"+cat+"</a><br />"

      s = "<div><meta name=\"viewport\" content=\"width=320\"/><h2>Now playing</h2><p>"+title+"</p><p>On channel: "+channel+"</p><p>Programme started at: "+stt+"</p><p>Local channel number is: "+channum+"</p>"+extras+"</div>"

      s = s.replace("&","&amp;")

      print "s is ",s
      return s
    else:
      return "<div><meta name=\"viewport\" content=\"width=320\"/><p>Nothing playing at the moment - this sometimes means it's an ad break, or else MythTV frontend has crashed</p></div>"



class Client(JabberClient):
  def __init__(self, jid, password):
    jid=JID(jid.node, jid.domain, "Basicbot")
    tls = streamtls.TLSSettings(require=True, verify_peer=False)
    auth = ['sasl:PLAIN']
    JabberClient.__init__(self, jid, password, tls_settings=tls,auth_methods=auth)
    self.interface_providers = [BasicHandler(self)]


locale.setlocale(locale.LC_CTYPE, "")
encoding = locale.getlocale()[1]
if not encoding:
    encoding = "us-ascii"
sys.stdout = codecs.getwriter(encoding)(sys.stdout, errors = "replace")
sys.stderr = codecs.getwriter(encoding)(sys.stderr, errors = "replace")


if len(sys.argv) < 3:
    print "Usage: python basicbot_pyxmpp.py jid password"
    sys.exit(1)
jid = sys.argv[1]
password = sys.argv[2]
c=Client(JID(sys.argv[1]), sys.argv[2])
c.connect()

try:
    c.loop(1)
except KeyboardInterrupt:
    c.disconnect()


