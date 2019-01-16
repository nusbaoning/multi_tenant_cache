from __future__ import print_function
from mtc_test_size_p import PLRU
import time
import sys
# baoning
# created 2019.01.14
# latest edited 2019.01.14

#function: dynamically change cache size and update frequency
# but try not to change the hit ratio 

class Log(object):
	"""docstring for Log"""
	def __init__(self, parameters):
		self.reqNum = 0
		self.periodNum = 0
		self.periodLength = parameters.periodLength 
		self.start = time.clock()
		self.parameters = parameters

	def tick():
		self.reqNum += 1
		if self.reqNum % self.periodLength == 0:
			self.periodNum += 1
			return True
		return False



class Parameter(object):
	"""docstring for Parameter"""
	def __init__(self, size, p, evictQueue, shadowQueue):
		self.size = size
		self.p = p
		self.evictQueue = evictQueue
		self.shadowQueue = shadowQueue
		

class DPLRU(PLRU):
	"""docstring for DPLRU"""
	def __init__(self, parameters):
		super(DPLRU, self).__init__(parameters.size, parameters.p)
		self.evictQueue = ([-1]*parameters.evictQueue, 0, 0)
		self.shadowQueue = ([-1]*parameters.shadowQueue, 0, 0)
		self.log = {}

	def is_hit(self, req):
		if req in self.log:
			self.log[req] = (self.log[req][0]+1, False)
		else:
			self.log[req] = (0, True)
		return super(DPLRU, self).is_hit(req)

	def updateQueue(self, req, sign):
		if sign == "e":
			queue = self.evictQueue
		elif sign == "s":
			queue = self.shadowQueue
		(l, head, tail) = queue
		old = l[tail]
		if old!=-1:
			print(old, self.log, type(old), type(self.log))
			del self.log[old]
		l[tail] = req
		tail = (tail + 1) % len(l)
		if head==tail:
			head = (head + 1) % len(l)

	def update_cache(self, req):
		(evict, update) = super(DPLRU, self).update_cache(req)
		if evict != None:
			self.updateQueue(evict, "e")
		if update==-1:
			self.updateQueue(req, "s")	
		return (evict, update)	

	def get_log(self):
		return self.log

	def get_evictQueue(self):
		return self.evictQueue

	def get_shadowQueue(self):
		return self.shadowQueue

def eprint(s):
	print(s)
		
def load_trace(fin):
	reqs = []
	lines = fin.readlines()
	for line in lines:
		items = line.split(' ')
		reqtype = int(items[0])
		block = int(items[2])
		reqs.append((reqtype, block))
	return reqs

def update_cache(req, ssd):
	hit = ssd.is_hit(req[1])
	if req[0] == 1 and hit:
		ssd.add_update()
	return ssd.update_cache(req[1])

def do_single_trace(traceName, parameters):

	#load trace
	fin = open(traceName, 'r')
	reqs = load_trace(fin)
	fin.close()

	#initial
	baseline = PLRU(parameters.size, parameters.p)
	ssd = PLRU(parameters.size, parameters.p)
	evictQueue = ([(-1, -1)]*parameters.evictQueue, 0, 0)
	shadowQueue = ([(-1, -1)]*parameters.shadowQueue, 0, 0)
	log = Log(parameters)

	for req in reqs:
		if log.tick():
			modify_config(ssd, evictQueue, shadowQueue, log)
		#?what about write request?
		
		debug = baseline.hit + baseline.update
		update_cache(req, baseline)
		if baseline.hit + baseline.update - debug == 0:
			eprint("error")
			sys.exit(-1)

		(shadow, evict) = update_cache(req, ssd)
		updateQueue(evict, evictQueue)
		updateShadow(shadow, shadowQueue)

	log.print(baseline, ssd)
 

fin = open("test.req", "r")
reqs = load_trace(fin)
fin.close()
print(reqs)
pd = Parameter(3, 0.5, 2, 2)
ssd = DPLRU(pd)
for req in reqs:
	a = update_cache(req, ssd)
	print(a)
	print(ssd.get_hit(), ssd.get_update(), ssd.get_log(), ssd.get_evictQueue(), ssd.get_shadowQueue())
