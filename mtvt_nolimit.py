from __future__ import print_function
from mtc_test_size_p import PLRU
import time
import sys
import random
# baoning
# created 2019.04.25
# latest edited 2019.04.25

#function: no limit of total cache capacity
# every trace can be treated separately
# use sample ssd to find min cost

class SamplePolicy(object):
    """docstring for samplePolicy"""
    def __init__(self, samplePolicy):
        (p, myround, matrix, minS, maxS, minP, maxP, parp, pars) = samplePolicy
        self.p = p
        self.myround = myround
        self.matrix = matrix
        self.maxS = maxS
        self.minS = minS
        self.minP = minP
        self.maxP = maxP
        # [0.3, 0.2, 0.1]
        self.parp = parp
        # [0.1, 0.05, 0.02]
        self.pars = pars

    def get_range(present, mymin, mymax, par, matrix):
        l = [present]
        n = 1
        start = present
        end = present
        while(n<matrix):
            if start > mymin:
                start = max(mymin, start-par)
                l.append(start)
                n += 1
            if end < mymax:
                end = min(mymax, end+par)
                l.append(end)
                n += 1    
        return l

    def getSamples(self, parameters):
        l = []
        presentP = parameters.presentP
        presentS = parameters.presentS
        
        plist = get_range(presentP, self.minP, 
            self.maxP, self.parp[-p+myround-1], self.matrix)
        slist = get_range(presentS, self.minS, self.maxS, 
            self.pars[-p+myround-1], self.matrix)
        cost = presentP * presentS

        for p in plist:
            for s in slist:
                if p*s < cost:
                    l.append((p,s))
        return l                            

class SampleSSD(object):
    """docstring for SampleSSD"""
    def __init__(self, p, s):
        self.p = p
        self.s = s
        self.add = {}
        self.minus = {}
        self.update = 0

    def is_hit(self, req, rw, hit):
        myhit = hit
        if myhit:
            if req in self.minus:
                myhit = False
        else:
            if req in self.add:
                myhit = True
        return myhit

    def add_update(self):
        self.update += 1

    def update_cache(self, roll, req, rw, hit, update):
        myhit = self.is_hit(req, rw, hit)
        if myhit and rw==1:
            self.add_update()
        # in old ssd -> not in add
        # if in minus and updated in sample, del minus
        if hit:
            if req in self.minus and roll<self.p:
                del self.minus[req]
                self.add_update()
        # not in old ssd -> not in minus
        else:
            # in new ssd
            # if in add, del add
            # else if not updated in sample, add minus
            if update:
                if req in self.add:
                    del self.add[req]
                elif roll>=self.p:
                    self.minus[req] = True
            elif roll<self.p:
                self.add[req] = True
                self.add_update()

        # another way to program is to calculate inssd and insample
        # directly change add and minus

class SampleSSDs(object):
    """docstring for SampleSSDs"""
    def __init__(self, parameters):
        self.ssds = []
        samplePolicy = parameters.samplePolicy
        l = samplePolicy.getSamples(parameters)
        for (p,s) in l:
            self.ssds.append(SampleSSD(p,s))
    
    def update_cache(self, roll, req, rw, hit, update):
        for ssd in self.ssds:
            ssd.update_cache(roll, req, rw, hit, update)

class Parameters(object):
    """docstring for Parameter"""
    def __init__(self, size, p, periodLength, hitRange, samplePolicy):
        self.size = size
        self.p = p
        self.periodLength = periodLength
        self.hitRange = hitRange
        self.samplePolicy = SamplePolicy(samplePolicy)
        

    def present(self, size, p):
        self.presentS = size
        self.presentP = p

def load_trace(fin):
    reqs = []
    lines = fin.readlines()
    for line in lines:
        items = line.split(' ')
        reqtype = int(items[0])
        block = int(items[2])
        reqs.append((reqtype, block))
    return reqs

def do_single_trace(traceName, parameters):

    #load trace
    fin = open(traceName, 'r')
    reqs = load_trace(fin)
    fin.close()

    #initial
    baseline = PLRU(parameters.size, parameters.p)
    ssd = PLRU(parameters.size, parameters.p)
    samples = SampleSSDs(parameters)
    log = Log(parameters)

    for (rw, req) in reqs:        
        #?what about write request?
        update_cache(req, baseline)
        update_cache(req, ssd)
        samples.update_cache(roll, req, rw, hit, update)
        if log.tick():
            modify_config(samples, ssd, baseline, parameters, log)
    log.print(baseline, ssd)
