from cache_algorithm import PLRU
import random
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
        if write > self.size * self.g * time:
            return write/self.size/self.g/time
        return 1
    

    def try_modify(scheme1, scheme2):
        (s, p) = scheme1
        if s <= self.size - self.usedSize:
            self.usedSize += s
            return (s, p)
        (s, p) = scheme2
        if s <= self.size - self.usedSize:
            self.usedSize += s
            return (s, p)
        return None


    def get_best_config_help(self, potentials, selected, size, write):
        if potentials==[]:
            if self.minWrite == None or write < self.minWrite:
                self.minWrite = write
                self.configList = []
                for item in selected:
                    self.configList.append(item)
            return
        items = potentials[0]
        for item in items:
            s = item.size
            w = item.get_update()
            if size + s > self.size:
                continue
            selected.append(item)
            self.get_best_config_help(potentials[1:], selected, size+s, write+w)


        

    def get_best_config(self, potentials):
        self.minWrite = None
        self.configList = []
        self.get_best_config_help(potentials, [], 0, 0)
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
        for i in range(self.policy["nrsamples"]):
            for j in range(self.policy["nrsamples"]):
                if i == 0 and j == 0:
                    continue
                sizeRatio = self.cacheSizeRatio + i * self.policy["deltas"]
                p = self.cache.p + j * self.policy["deltap"]
                if is_valid_sp(sizeRatio, p):
                    s = PLRU(int(sizeRatio*self.ucln), p)
                    s.copy(self.cache)
                    s.update = 0
                    self.samples.append(s)
                sizeRatio = self.cacheSizeRatio - i * self.policy["deltas"]
                p = self.cache.p - j * self.policy["deltap"]
                if is_valid_sp(sizeRatio, p):
                    s = PLRU(int(sizeRatio*self.ucln), p)
                    s.copy(self.cache)
                    s.update = 0
                    self.samples.append(s)
        
    def do_req_help(cache, rw, blkid, roll):
        self.req += 1
        hit = cache.is_hit(req)
        if rw==1 and hit:
            cache.add_update()
        (evicted, update) = cache.update_cache(req, roll)
        if update==-1:
            update=False
        else:
            update=True
        return (hit, update, evicted)

    # def get_delta_hit(c1, c2):
    #     h1 = c1.get_hit()
    #     h2 = c2.get_hit()
    #     return (h1-h2)/h1

    def exceed_throt(hit):
        baseline = self.baseline.get_hit()
        h = (hit - baseline)/self.req
        if h > self.policy["throt"]:
            return True
        return False

    def get_close_potentials():
        sizeRatio = self.cache.sizeRatio
        size = int(sizeRatio*self.ucln)
        p = self.cache.p
        pt1 = None
        pt2 = None
        for pt in self.potentials:
            if pt.size == size and pt.p==p+self.policy["deltap"]:
                pt1 = pt
            elif pt.size == size+self.policy["deltas"] and pt.p == p:
                pt2 = pt
            if pt1!=None and pt2!=None:
                return (pt1, pt2)


    def do_req(self, rw, blkid):
        random.seed()
        roll = random.random()
        do_req_help(self.baseline, rw, blkid, roll)
        do_req_help(self.cache, rw, blkid, roll)
        for s in self.samples:
            do_req_help(s, rw, blkid, roll)
        if exceed_throt(self.cache.hit):
            (p1, p2) = get_close_potentials()
            if p1.get_hit() > p2.get_hit():
                return (True, (p1.size-self.cache.size, p1.p-self.cache.p), (p2.size-self.cache.size, p2.p-self.cache.p))
            return (True, (p2.size-self.cache.size, p2.p-self.cache.p), (p1.size-self.cache.size, p1.p-self.cache.p))
        return (False, None, None)


    def change_config(self, s, p):
        self.cache.change_size(s)
        self.cache.change_p(p)
        self.cacheSizeRatio = round(s/self.ucln, 1)
    
    # give potentials inside the hit range
    # remove bad ones (both s and p are larger)
    def get_potential():
        potentials = []
        results = []
        for sample in self.samples:
            if exceed_throt(sample.get_hit()):
                continue
            potentials.append(sample)

        for i in range(len(potentials)):
            sign = False
            for j in range(len(potentials)):
                if i==j:
                    continue
                if potentials[i].s >= potentials[j].s and potentials[i].p >= potentials[j].p:
                    sign = True
                    break
            if not sign:
                results.append(potentials[i])

        return results
            
        
        
                    