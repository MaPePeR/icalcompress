#!/usr/bin/env python
from icalendar import *
import datetime
from sys import argv,exit
from os import path
events = []

class ev:
	def __init__(self, vevent):
		self.summary = vevent.get('SUMMARY')
		self.location = vevent.get('LOCATION')
		self.description = vevent.get('DESCRIPTION')
		self.length = vevent.get('dtend').dt - vevent.get('dtstart').dt
		self.vevent = vevent
		self.similiars = [vevent]

	def isSimiliar(self, otherv):
		return self.summary == otherv.get('SUMMARY') and self.location == otherv.get('LOCATION') and self.description == otherv.get('DESCRIPTION') and self.length == otherv.get('dtend').dt - otherv.get('dtstart').dt

	def generateRecurring(self):
		self.similiars.sort(key=lambda e:e.get('DTSTART').dt)
		repetitions = 0
		for i,e in enumerate(self.similiars):
	#		if e.get('dtstart').dt - (self.vevent.get('dtstart').dt + datetime.timedelta(days=i*7)) == datetime.timedelta(0):
			if e.get('dtstart').dt ==  (self.vevent.get('dtstart').dt + datetime.timedelta(days=i*7)):
				repetitions = i
			else:
		#		print e.get('dtstart').dt - (self.vevent.get('dtstart').dt + datetime.timedelta(days=i*7)) 
		#		print e.get('dtstart').dt," != ", self.vevent.get('dtstart').dt + datetime.timedelta(days=i*7)
				break;
		if repetitions < len(self.similiars) - 1:
			#Not all events repeated => Split it
			newe = ev(self.similiars[repetitions+1])
			newe.similiars = self.similiars[repetitions + 1:]
			self.similiars = self.similiars[0:repetitions + 1]
			#return  str(repetitions + 1) + "/" + str(newe.generateRecurring())a
			events.append(newe)
		return repetitions + 1


def deleteFromSubcomponents(c, toDelete):
	if hasattr(c,'subcomponents'):
		#TODO there is probably a better way of doing this
		c.subcomponents = [x for x in c.subcomponents if x not in toDelete]
		for s in c.subcomponents:
			deleteFromSubcomponents(s,toDelete)
		

ifilename = ""
ofilename = ""
if len(argv) == 3:
	ifilename = argv[1]
	ofilename = argv[2]
	print "In File:  %s" % ifilename
	print "Out File: %s" % ofilename
	if (ifilename == ofilename):
		print "Error: you can't specify the same file name twice"
		exit(1)
	if not path.isfile(ifilename):
		print "%s does not exist" % ifilename
		exit(1)
else:
	print "USAGE: %s [input file] [output file]" % argv[0]
	print "Tool that searches an ICAL calendar file for weekly repeating Events that have the same Summary, Description, Location and Time Length"
	print "These Events will then be converted to actual weekly repeating events"
	exit(1)

with open(ifilename,"rb") as ifile:
	cal = Calendar.from_ical(ifile.read())
	for o in cal.walk():
		if (o.name == "VEVENT"):
			for e in events:
				if e.isSimiliar(o):
					e.similiars.append(o)
					break
			else:
				events.append(ev(o))
	todelete = []
	for e in events:
		e.generateRecurring()
		if len(e.similiars) > 1:
			e.vevent.add('RRULE', {'COUNT':len(e.similiars), 'FREQ':'WEEKLY'})
			todelete.extend(e.similiars[1:])
	deleteFromSubcomponents(cal, todelete)
	events.sort(key=lambda o: o.summary)
	for e in events:
		print "%s (%s-%s, %s)" % (e.summary, e.similiars[0].get('dtstart').dt.time(),e.similiars[0].get('dtend').dt.time(), e.length)
		print "%d from %s to %s" %(len(e.similiars),e.similiars[0].get('dtstart').dt.date(),e.similiars[-1].get('dtstart').dt.date())
		print

	with open(ofilename,'wb') as ofile:
		ofile.write(cal.to_ical())
