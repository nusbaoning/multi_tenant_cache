from cache_algorithm import PLRU
import random
import sys
danwei = 10**7

# assume that the cache is larger than time period 
# the evict result of potentials are the same as original cache when evict
class SampleCache(object):
    """docstring for SampleSSD"""
    def __init__(self, p, size, cache):
        self.p = p
        self.size = size
        self.add = {}
        self.minus = {}
        self.update = cache.get_update()
        self.hit = cache.get_hit()
        if self.size < cache.size:
            l = cache.get_tail_n(cache.size - self.size)
            for item in l:
                self.minus[item] = True

    # no call from outside! only call by update_cache
    def is_hit(self, req, rw, hit):
        myhit = hit
        if myhit:
            if req in self.minus:
                myhit = False
        else:
            if req in self.add:
                myhit = True
        if myhit:
            self.hit += 1
        return myhit

    def add_update(self):
        self.update += 1

    def get_len(self, cache):
        return len(cache) + len(self.add) - len(self.minus)

    def evict(self, blkid):
        if blkid in self.minus:
            del self.minus[blkid]
        elif blkid in self.add:
            del self.add[blkid]

    def update_cache(self, roll, blkid, rw, hit, update, cache):
        myhit = self.is_hit(blkid, rw, hit)
        myupdate = False
        myevict = False
        if myhit and rw==1:
            self.add_update()
        # in old ssd -> not in add
        # if in minus and updated in sample, del minus
        if not myhit and roll<self.p:
            self.add_update()
            myupdate = True
# need to modify, possible that shadow cache and original cache evict different block
            if self.size <= self.get_len(cache):
                myevict = True
        if new_in_cache(hit, update) == new_in_cache(myhit, myupdate):
            self.evict(blkid)
        else:
            if new_in_cache(hit, update):
                minus[blkid] = True
            else:
                add[blkid] = True
        if evicted == myevict:
             self.evict(tail)
        else:
            if evicted:
                add[tail] = True
            else:
                minus[tail] = True            

def is_valid_sp(sizeRatio, p):
    if p > 1 or p <= 0:
        return False
    if sizeRatio > 0.8 or sizeRatio < 0.1:
        return False
    return True



class Device(object):
    """docstring for Device"""
    def get_total_size(self):
        s = 0
        for trace in self.cacheDict:
            cache = self.cacheDict[trace]
            s += cache.cache.size
        return s

    def __init__(self, size, g, cacheDict):
        self.size = size
        self.g = g
        self.cacheDict = cacheDict
        self.usedSize = self.get_total_size()

    def get_cost(self, write, time):
        print("write=", write, ",size=", self.size, ",g=", self.g, ",time=", time)
        if write > self.size * self.g * time:
            return write/self.size/self.g/time
        return 1
    

    def try_modify(self, scheme1, scheme2):
        if scheme1!=None:            
            (deltas, deltap) = scheme1
            if deltas <= self.size - self.usedSize:
                self.usedSize += deltas
                return (deltas, deltap)
        if scheme2==None:
            return None
        (deltas, deltap) = scheme2
        if deltas <= self.size - self.usedSize:
            self.usedSize += deltas
            return (deltas, deltap)
        return None


    def get_best_config_help(self, potentials, selected, size, write):

        if potentials==[]:
            # print("minWrite=", self.minWrite, ",write=", write, ",size=", size)
            if self.minWrite == None or write < self.minWrite:
                self.minWrite = write
                self.configList = []
                for item in selected:
                    self.configList.append(item)
                    # print("item,", item.p, item.size)
            return
        items = potentials[0]
        for item in items:
            s = item.size
            w = item.get_update()
            if size + s > self.size:
                continue
            selected.append(item)
            # print("before", len(selected))
            self.get_best_config_help(potentials[1:], selected, size+s, write+w)
            selected = selected[:-1]
            # print("after", len(selected))


        

    def get_best_config(self, potentials):
        self.minWrite = None
        self.configList = []
        self.get_best_config_help(potentials, [], 0, 0)
        # print("size", len(self.configList))
        return self.configList

        

class Cache(object):
    """docstring for Cache"""
    def __init__(self, trace, sizeRatio, ucln, p, policy):
        self.trace = trace
        self.cacheSizeRatio = sizeRatio
        # self.p = p
        self.ucln = ucln
        # policy = nrsamples, hit throt, +-s, +-p
        self.policy = policy
        self.baseline = PLRU(int(sizeRatio*ucln), p)
        self.cache = PLRU(int(sizeRatio*ucln), p)
        self.req = 0
        self.init_samples()

    def init_samples(self):
        self.samples = []
        for i in range(-self.policy["nrsamples"], self.policy["nrsamples"]):
            for j in range(-self.policy["nrsamples"], self.policy["nrsamples"]):
                if i == 0 and j == 0:
                    continue
                # print("i=", i, ",j=", j)
                sizeRatio = self.cacheSizeRatio + i * self.policy["deltas"]
                p = self.cache.p + j * self.policy["deltap"]
                # print("sr=", sizeRatio, ",p=", p)
                if is_valid_sp(sizeRatio, p):
                    size = int(sizeRatio*self.ucln)
                    # print("valid", size, p)
                    s = PLRU(int(sizeRatio*self.ucln), p)
                    s.copy(self.cache, size, p)
                    s.update = 0
                    self.samples.append(s)
                # sizeRatio = self.cacheSizeRatio - i * self.policy["deltas"]
                # p = self.cache.p - j * self.policy["deltap"]
                # print("sr=", sizeRatio, ",p=", p)
                # if is_valid_sp(sizeRatio, p):
                #     size = int(sizeRatio*self.ucln)
                #     print("valid", size, p)
                #     s = PLRU(size, p)
                #     s.copy(self.cache, size, p)
                #     s.update = 0
                #     self.samples.append(s)
        
    def do_req_help(self, cache, rw, blkid, roll):
        hit = cache.is_hit(blkid)
        if rw==1 and hit:
            cache.add_update()
        (evicted, update) = cache.update_cache(blkid, roll)
        if update==-1:
            update=False
        else:
            update=True
        return (hit, update, evicted)

    # def get_delta_hit(c1, c2):
    #     h1 = c1.get_hit()
    #     h2 = c2.get_hit()
    #     return (h1-h2)/h1

    def exceed_throt(self, hit):
        # print("exceed_throt self=", self)
        baseline = self.baseline.get_hit()

        h = 1.0*(baseline - hit)/self.req
        # if (hit!=baseline):            
        #     print("baseline", baseline, ",cache", hit, ",Dratio=", h)
        if h > self.policy["throt"]:
            return True
        return False

    def get_close_potentials(self):
        # print("enter get close potentials")
        sizeRatio = self.cacheSizeRatio
        size = int(sizeRatio*self.ucln)
        p = self.cache.p
        pt1 = None
        pt2 = None
        for pt in self.samples:
            if pt.size == size and pt.p==p+self.policy["deltap"]:
                pt1 = pt
            elif pt.size == size+self.policy["deltas"] and pt.p == p:
                pt2 = pt
            if pt1!=None and pt2!=None:
                return (pt1, pt2)
        return (pt1, pt2)

    def do_req(self, rw, blkid):
        random.seed()
        roll = random.random()
        self.req += 1
        self.do_req_help(self.baseline, rw, blkid, roll)
        self.do_req_help(self.cache, rw, blkid, roll)
        for s in self.samples:
            self.do_req_help(s, rw, blkid, roll)
        # print("self=", self)
        if self.exceed_throt(self.cache.hit):
            # print("after self=", self)
            (p1, p2) = self.get_close_potentials()
            if p1==None and p2==None:
                return (False, None, None)
            elif p1==None:
                return (True, (p2.size-self.cache.size, p2.p-self.cache.p), None)
            elif p2==None:
                return (True, (p1.size-self.cache.size, p1.p-self.cache.p), None)
            if p1.get_hit() > p2.get_hit():
                return (True, (p1.size-self.cache.size, p1.p-self.cache.p), (p2.size-self.cache.size, p2.p-self.cache.p))
            return (True, (p2.size-self.cache.size, p2.p-self.cache.p), (p1.size-self.cache.size, p1.p-self.cache.p))
        return (False, None, None)


    def change_config(self, s, p):
        # size = s+self.cache.size
        # p = p+self.cache.p
        self.cache.change_size(s)
        self.cache.change_p(p)
        self.cacheSizeRatio = round(1.0*s/self.ucln, 1)
        assert self.cacheSizeRatio >= 1
        # if self.cacheSizeRatio >= 1:
        #     print("trace", self.trace, ",sr=", self.cacheSizeRatio, ",s=", s, "p=", p)
        #     sys.exit(-1)
        # print("sr=", self.cacheSizeRatio)
    # give potentials inside the hit range
    # remove bad ones (both s and p are larger)
    def get_potential(self):
        potentials = []
        results = []
        for sample in self.samples:
            if self.exceed_throt(sample.get_hit()):
                continue
            potentials.append(sample)
        
        # print("sample", sample)
        for i in range(len(potentials)):
            sign = False
            for j in range(len(potentials)):
                # print(i, j, potentials[i].size, potentials[j].size, potentials[i].update, potentials[j].update)
                # print(sign)
                if i==j:
                    continue
                if potentials[i].size > potentials[j].size and potentials[i].update > potentials[j].update:
                    sign = True
                    break
            # print(sign)
            if not sign:
                results.append(potentials[i])

        return results
            
        
        
                    