#!/usr/bin/env python

# This bot doesn't actualy do anything real, but just provides the outline.
# You shouldn't need myth or anything special to run it apart form pyxmpp

from pyxmpp import streamtls
from presence_test import BasicBot
from pyxmpp.all import JID
from pyxmpp.jabber.client import JabberClient
import locale
import codecs
import sys

class Client(JabberClient):
  def __init__(self, jid, password):
    jid=JID(jid.node, jid.domain, "Basicbot")
    tls = streamtls.TLSSettings(require=True, verify_peer=False)
    auth = ['sasl:PLAIN']
    JabberClient.__init__(self, jid, password, tls_settings=tls,auth_methods=auth,keepalive=600)
    self.interface_providers = [BasicBot(self)]

  def __stream_state_change(self,state,arg):
    self.stream_state_changed(state,arg)
    print "STATE",state
    if state=="fully connected":
      self.connected()
      
#     self.myFullJID=self.client.stream.jid
    elif state=="authorized":
      self.authorized()
    elif state=="disconnected":
      self.state_changed.acquire()
      try:
        if self.stream:
           self.stream.close()
        self.stream_closed(self.stream)
        self.stream=None
        self.state_changed.notify()
      finally:
        self.state_changed.release()
        self.disconnected()



locale.setlocale(locale.LC_CTYPE, "")
encoding = locale.getlocale()[1]
if not encoding:  
    encoding = "us-ascii"
sys.stdout = codecs.getwriter(encoding)(sys.stdout, errors = "replace")
sys.stderr = codecs.getwriter(encoding)(sys.stderr, errors = "replace")

if len(sys.argv) < 3:
    print "Usage: python run_basic.py jid password"
    sys.exit(1)
jid = sys.argv[1]
password = sys.argv[2]
c=Client(JID(sys.argv[1]), sys.argv[2])
c.connect()

try:
    c.loop(1)
except KeyboardInterrupt:
    c.disconnect()
