#!/usr/bin/python
import sys,os,xmpp,time,string


class Bot(object):

    def __init__( self, jid, password):
      self.jid = jid
      self.password = password
      self.client = None

    def send(msg, user):
      id=cl.send(xmpp.protocol.Message(user,msg))
      print "Sent message ",msg
    
    def reply(self, conn, mess):
      text = mess.getBody()
      print "Got message ",text
      self.send( mess.getFrom(), text, mess)

    def send( self, user, text, in_reply_to = None):
      mess = xmpp.Message( user, text)
      if in_reply_to:
        mess.setThread( in_reply_to.getThread())
        mess.setType( in_reply_to.getType())
        self.connect().send( mess)

    def connect(self):

      jid=xmpp.protocol.JID(self.jid)
      if not self.client:
        cl=xmpp.Client(jid.getDomain(),debug=[])
        con=cl.connect()
        if not con:
          print 'could not connect!'
          sys.exit()

        self.client = cl
        print 'connected with',con
        auth=cl.auth(jid.getNode(),self.password,resource=jid.getResource())

        if not auth:
          print 'could not authenticate!'
          sys.exit()
        print 'authenticated using',auth

        cl.RegisterHandler( 'message', self.reply)
        cl.sendInitPresence()

      return self.client

    def listen( self):
      conn = self.connect()
      while ("true"):
        try:
          conn.Process(1)
          pass
        except KeyboardInterrupt:
          break


if (len(sys.argv) > 2):
  bot = Bot(sys.argv[1],sys.argv[2])
  bot.listen()
else:
  print "Usage basicbot_xmpp.py jid password"

