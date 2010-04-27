# run using python run_basic.py
# See http://pyxmpp.jajcus.net/trac/browser/trunk/examples/echobot.py for a more detailed example
# requires pyxmpp (on Ubuntu: sudo apt-get install python-pyxmpp)
import sys
import urllib
import re
import threading
import random
import json
import libxml2
import BeautifulSoup
from threading import Timer

from BeautifulSoup import BeautifulSoup

from pyxmpp.all import JID,Iq,Presence,Message,StreamError
from pyxmpp.interface import implements
from pyxmpp.interfaces import IMessageHandlersProvider,IIqHandlersProvider,IPresenceHandlersProvider
from pyxmpp.iq import Iq


class BasicBot(object):
  implements(IMessageHandlersProvider,IIqHandlersProvider,IPresenceHandlersProvider)
    
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

######
# Various interfaces so we can handle presence, iq and chat messages
######

  def get_presence_handlers(self):
     print "Presence handlers called"
     return [("available", self.presence), (None, self.presence)]

  def get_iq_get_handlers(self):
    print "get handlers requested for iq"
    return [("query","http://buttons.foaf.tv/",self.iq)]

  def get_iq_set_handlers(self):
    print "set handlers requested for iq"
    return [("query","http://buttons.foaf.tv/",self.iq)]

  def get_message_handlers(self):
    return [("normal", self.default)]

######
# handle presence messages
######

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
# The full jid only appears in the presence requests.
# These should always be requested before we get any messages
      self.myFullJID= stanza.get_to()
      print "full jid is "+str(self.myFullJID)
      return p

######
# Handle iq messages
######

  def iq(self,stanza):
    print "IQ requested"
    print "iq stanza",stanza.serialize(),"\n"
    b=stanza.get_query()
    print "GOT an IQ",str(b.get_content())
    ty=stanza.get_type()   
    rr= "no response"
    content = b.get_content()
    if b:
       b = unicode(b)
    resp = stanza.make_result_response()
    cmd = content.lower()
    body = ''
# These commands are the ones that we want to use over IQ
    param=None
    arr = cmd.split(" ")
    if(arr and len(arr)>1 and arr[1]):
       cmd = arr[0]
       param = arr[1]
    body = self.process_command(cmd,param)
    source = "<nowp-result xmlns='http://buttons.foaf.tv/'>" + body + "</nowp-result>"        
    soup = BeautifulSoup(source)
    doc = libxml2.parseDoc(str(soup.contents[0]))
    resp.set_content(doc)
    print "IQ response is ",resp
    return resp


######
# Handle chat messages
######

  def default(self,stanza):
    sub=stanza.get_subject()
    print "chat stanza",stanza.serialize(),"\n"
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
    param=None
    if(len(arr)>1 and arr[1]):
       param = arr[1]

    body = self.process_command(cmd, param)
    msg=Message(to_jid=stanza.get_from(),from_jid=stanza.get_to(),stanza_type=stanza.get_type(),subject=sub,body=body)
    return msg

#######
# Commands
#######

  def process_command(self, cmd,param):
    if cmd == "nowp":
       body = self.html_nowp()
    elif cmd == "plus":
       body = self.plus()
    elif cmd == "minu":
       body = self.minu()
    elif cmd == "righ":
       body = self.righ()
    elif cmd == "left":
       body = self.left()
    elif cmd == "like":
       body = self.do_bookmark()
    elif cmd == "qr":
       body = self.do_qr()
    elif cmd == "plpz":
       body = self.plpz()
    elif cmd == "ffwd":
       body = self.ffwd()
    elif cmd == "rewd":
       body = self.rewd()
    elif cmd == "menu":
       body = self.menu()
    elif cmd == "info":
       body = self.info()
    elif cmd == "loud":
       body = self.loud()
    elif cmd == "hush":
       body = self.hush()
    elif cmd == "save":
       body = self.save(param)
    elif cmd == "okay":
       body = self.okay()
    elif cmd == "help":
       body = self.help()
    else:
       body = cmd
    print "returning body",body
    print body.__class__
    return body

#####
# These commands need to be made specific to the platform
# These are just stubs
#####

  def plus(self):
    return "plus called"

  def minu(self):
    return "minu called"

  def righ(self):
    return "righ called"

  def left(self):
    return "left called"

  def plpz(self):
    return "plpz called"

  def ffwd(self):
    return "ffwd called"

  def rewd(self):
    return "rewd called"

  def menu(self):
    return "menu called"

  def info(self):
    return "info called"

  def loud(self):
    return "loud called"

  def hush(self):
    return "hush called"

  def okay(self):
    return "okay called"


#####
# Help message
#####

  def help(self):
     body = "nowp,plus,minu,righ,left,like,qr,plpz,ffwd,rewd,menu,loud,hush,save [bbc progs url],okay,info,help"
     return body

#####
# Save using the iplayer thread
#####

  def save(self,pid):
     body = None
     if pid:
        if (re.match("^http",pid)):
           pid =pid.replace("http://www.bbc.co.uk/programmes/","")
        pid_match = re.match('.*?\/?([b-df-hj-np-tv-z][0-9b-df-hj-np-tv-z]{7,15}).*?',pid)
        if pid_match:
           pid = pid_match.group(1)
           print "saving using get_iplayer:",pid
           GetIplayerThread(pid).start()
           body = "Trying to download "+ pid
        else:
          body = "No pid found"
     else:
          body = "No pid found"
     return body


####
# Get what is playing now - faked!
####

  def do_now_playing(self,send_event):
    # start thread for polling for nowp every 5 minutes
    print "XXXXXX starting timer"
    t = Timer(600.0, self.nowp_rpt)
    t.start()

    results = {'title': "BBC News At Six", 'pid': 'b00s1kpc', 'datetime': '2010-04-13T18:00:00', 'secs': 600, 'channum': '1001', 'channel': 'bbcone'}

    if (send_event):
       print "Should send watching event here"           
       self.send_event(results, "Watching")
    self.nowplaying=results
    self.client.stream.send( Presence( status="foo"+results["title"] ) )
    print "returning results, sending ptresence"
    return results

####
# Send an event to the beancounter specified by this user
####

  def send_event(self, event, e_type):
    event["type"]=e_type
    jid =self.currentJID
    event["username"]=jid.node+"@"+jid.domain
    print "sending event",e_type,str(event)


####
# Send a bookmark to delicious - requires username and password
####


  def do_bookmark(self):
    data2 = self.do_now_playing(False)
    print "got data for bookmarking", data2
    res2= "bookmarked "+data2["title"]
    self.send_event( data2, "Bookmarked")
    print "Sending alert to screen"
    return res2


####
# Pop up a qr code on request
####

  def do_qr(self):
    pin = random.randint(1000, 9999)
    fn = "q"+str(pin)+".png"
    jstring = str(self.myFullJID)
    print "bot ",jstring
# Need to add some stuff so that we can accept things with this pin
    return "Popping up a QR code for"+jstring+"#"+str(pin)

####
# Now playing as html
###

  def html_nowp(self):
    print "nowplaying requested"
    z = self.do_now_playing(False) 
    print "z ",z 
    if z:
      title = z["title"]
      channel = z["channel"]
      channum = None
      stt = z["datetime"]
      if z.has_key("channum"):
         channum = z["channum"]
      extras = ""
# get the pid if it's a BBC programme
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

      s = "<div><meta name=\"viewport\" content=\"width=320\"/><h2>Now playing</h2><p>"+title+"</p><p>On channel: "+channel+"</p><p>Programme started at: "+stt+"</p>"
      if (channum):
         s = s+"<p>Local channel number is: "+channum+"</p>"
      s = s+extras+"</div>"

      s = s.replace("&","&amp;")

      print "s is ",s
      return s
    else:
      return "<div><meta name=\"viewport\" content=\"width=320\"/><p>Nothing playing at the moment - this sometimes means it's an ad break, or else MythTV frontend has crashed</p></div>"



  def nowp_rpt():
     print "nowp requested in 5 minutes"
     self.do_now_playing(nil)


######
# Special thread for getiplayer
######

class GetIplayerThread ( threading.Thread):
  def __init__ (self, pid):
     self.pid = pid
     threading.Thread.__init__ ( self )
  def run ( self ):
     print "getIplayer thread run called",self.pid


