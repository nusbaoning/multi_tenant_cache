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
	hit = ssd.it_hit()
	if req[0] == 1 and hit:
		# maybe add a function in PLRU
		ssd.update += 1
	return ssd.update_cache(req)

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