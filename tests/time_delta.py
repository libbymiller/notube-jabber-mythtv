import datetime
import time

d1str = "2010-04-16 17:15:00"
d2 = datetime.datetime.now()

d1 = datetime.datetime.strptime(d1str,"%Y-%m-%d %H:%M:%S")

print "comparing",d1.__class__,"and",d2.__class__

delta = d2 - d1
print "secs",delta.seconds,"mins",delta.seconds/60
