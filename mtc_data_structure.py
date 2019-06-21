from cache_algorithm import PLRU

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

def is_valid_sp(sizeRatio, p):
    if p > 1 or p <= 0:
        return False
    if s > 0.8 or s < 0.1:
        return False
    return True


class Cache(object):
    """docstring for Cache"""
    def __init__(self, trace, sizeRatio, ucln, p, policy):
        self.trace = trace
        self.sizeRatio = sizeRatio
        self.p = p
        self.ucln = ucln
        # policy = nrsamples, hit throt, +-s, +-p
        self.policy = policy
        self.baseline = PLRU(sizeRatio*ucln, p)
        self.cache = PLRU(sizeRatio*ucln, p)
        self.samples = self.init_samples()

    def init_samples(self):
        samples = []
        for i in range(self.policy.nrsamples):
            for j in range(self.policy.nrsamples):
                if i == 0 and j == 0:
                    continue
                sizeRatio = self.sizeRatio + i * policy.deltas
                p = self.p + j * policy.deltap
                if is_valid_sp(sizeRatio, p):
                    s = SampleCache(p, sizeRatio*ucln, self.cache)
                sizeRatio = self.sizeRatio - i * policy.deltas
                p = self.p - j * policy.deltap
                if is_valid_sp(sizeRatio, p):
                    s = SampleCache(p, sizeRatio*ucln, self.cache)

        
                    