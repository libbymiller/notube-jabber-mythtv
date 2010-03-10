# See http://pyxmpp.jajcus.net/trac/browser/trunk/examples/echobot.py for a more detailed example
# requires pyxmpp (on Ubuntu: sudo apt-get install python-pyxmpp)
import sys
import urllib
import re
import datetime
import time
import timeit
import threading
import os
import random
import subprocess
import MySQLdb


from pyxmpp import streamtls
from pyxmpp.all import JID,Iq,Presence,Message,StreamError
from pyxmpp.jabber.client import JabberClient
from pyxmpp.interface import implements
from pyxmpp.interfaces import IMessageHandlersProvider

# required to talk to mythtv
import telnetlib

class BasicHandler(object):
  implements(IMessageHandlersProvider)
    
  def __init__(self, client):
    self.client = client
    
  def get_message_handlers(self):
    return [("normal", self.default)]

  def default(self,stanza):
    sub=stanza.get_subject()
    b=stanza.get_body()
    ty=stanza.get_type()
    if sub:
       sub=unicode(sub)
    if b:
       b = unicode(b)
    print "Got msg.... "+unicode(b)
    if stanza.get_type()=="headline":
       # don't reply to these
       return True
    print "bb ",b
    arr = b.split(" ")
    cmd = arr[0]
    cmd = cmd.lower() 
    print "command ",cmd
    if cmd == "go":
       arr.pop(0)
       bbb = " ".join(arr)
       print "body ",bbb
       body = self.send_command(bbb)
    elif cmd == "p":
       body = self.do_now_playing()
    elif cmd == "b":
       body = self.do_bookmark()
    elif cmd == "qr":
       body = self.do_qr()
    elif cmd == "nowp":
       body = self.html_nowp()
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
    elif cmd == "loud":
       time.sleep(1)
       body = self.send_command("key [")
    elif cmd == "hush":
       time.sleep(1)
       body = self.send_command("key }")
    elif cmd == "okay":
        # if we are in the epg, send one set of commands, else send 'enter'
        # first check where we are 
        res = self.send_command("query location")
        arr = res.split(",")
        print "location str ",arr[2]
        m = re.search('Playback', arr[2])
        print " status: ",m
        if(m):
          self.send_command("key enter")
        else:
          self.send_command("key X")
          time.sleep(2)
          return self.send_command("key escape")
    else:
       body = b
    msg=Message(to_jid=stanza.get_from(),from_jid=stanza.get_to(),stanza_type=stanza.get_type(),subject=sub,body=body)
    return msg

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

  def do_now_playing(self):
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

      # you need to add your myth password
      db = MySQLdb.connect(host="localhost", user="mythtv", passwd="pass",db="mythconverg")
      cursor = db.cursor()
      cursor.execute("select title,starttime,callsign from program,channel where program.chanid=channel.chanid and starttime <= '"+dtnfmt+"' and endtime > '"+dtnfmt+"' and program.chanid='"+arr[9]+"' limit 1;")
      result = cursor.fetchall()
      record = result[0] 
      print "RECORD",str(record)

      res2=""
      if (record!=""):
        secs = record[1]
        results["secs"]=secs-dtnow
        results["secs"]=results["secs"].seconds
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
           print data2,"..."
           progs = "http://www.bbc.co.uk/programmes/"
        else:
           data2=None
    return results

####
# Send a bookmark to delicious - requires username and password
####

  def do_bookmark(self):
    data2 = self.do_now_playing()
    if (data2):
      # wait one sec
      time.sleep(1)
      # do delicious on it
      uu=None
      pw=None
      if(uu!="" and pw!=""):
        progs = "http://www.bbc.co.uk/programmes/"
        delicious_url_1="https://"+uu+":"+pw+"@api.del.icio.us/v1/posts/add?url="
        q=progs+""+data2["pid"]+"#"+data2["secs"]
        delicious_url_2=urllib.quote_plus(q)+"&description="+urllib.quote_plus(data2["title"]+" ("+data2["secs"]+" seconds in)")+"&tags=tv&tags=mythtv&tags=notube"
        delicious_url= delicious_url_1+delicious_url_2
        z = urllib.urlopen(delicious_url).read()
        res2= "bookmarked "+data2["title"]
      else:
        res2 = "could not bookmark "+data2["title"]+" - no username / password"
      return res2
    else:
      res2 = "no bookmark created - not playing anything at the moment"
      return res2


####
# pop up a qr code on request
####

  def do_qr(self):
    i = random.randint(1000, 9999)
    print "bot ",self.client.jid
    fn = "q"+str(i)+".png"
    jid = self.client.jid
    jstring = jid.node+"@"+jid.domain
    ar = ["qrencode", "-o", fn, "-s", "20", "xmpp:"+unicode(jstring)+"/q"+str(i)+"'"]
    print ar
    res = subprocess.Popen(ar)
    cm = ["xli", "-display", ":0.0", "-fullscreen", fn]
    time.sleep(1)
    foo = subprocess.Popen(cm)
    time.sleep(3)
    foo.terminate() 
    print foo

####
# now playing as html
###

  def html_nowp(self):
    print "nowplaying requested"
    z = self.do_now_playing()  
    title = z["title"]
    channel = z["channel"]
    stt = z["datetime"]
    channum = z["channum"]
    s = "<div><h2>Now playing</h2><p>"+title+"</p><p>On channel: "+channel+"</p><p>Programme started at: "+stt+"</p><p>Local channel number is: "+channum+"</p></div>"
    return s

class Client(JabberClient):
  def __init__(self, jid, password):
    jid=JID(jid.node, jid.domain, "Basicbot")
    tls = streamtls.TLSSettings(require=True, verify_peer=False)
    auth = ['sasl:PLAIN']
    JabberClient.__init__(self, jid, password, tls_settings=tls,auth_methods=auth)
    self.interface_providers = [BasicHandler(self)]

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

