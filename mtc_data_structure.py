#coding=utf-8
from cache_algorithm import PLRU
import random
import sys
import copy

danwei = 10**7

# 本来想用sampleCache的shadow来模拟候选cache
# 后面发现结果很容易不准，暂时不用这个方案了，等后期实在内存不够运行太慢了再说
# class SampleCache(object):
#     """docstring for SampleSSD"""
#     def __init__(self, p, size, cache):
#         self.p = p
#         self.size = size
#         self.add = {}
#         self.minus = {}
#         self.update = cache.get_update()
#         self.hit = cache.get_hit()
#         if self.size < cache.size:
#             l = cache.get_tail_n(cache.size - self.size)
#             for item in l:
#                 self.minus[item] = True

#     # no call from outside! only call by update_cache
#     def is_hit(self, req, rw, hit):
#         myhit = hit
#         if myhit:
#             if req in self.minus:
#                 myhit = False
#         else:
#             if req in self.add:
#                 myhit = True
#         if myhit:
#             self.hit += 1
#         return myhit

#     def add_update(self):
#         self.update += 1

#     def get_len(self, cache):
#         return len(cache) + len(self.add) - len(self.minus)

#     def evict(self, blkid):
#         if blkid in self.minus:
#             del self.minus[blkid]
#         elif blkid in self.add:
#             del self.add[blkid]

#     def update_cache(self, roll, blkid, rw, hit, update, cache):
#         myhit = self.is_hit(blkid, rw, hit)
#         myupdate = False
#         myevict = False
#         if myhit and rw==1:
#             self.add_update()
#         # in old ssd -> not in add
#         # if in minus and updated in sample, del minus
#         if not myhit and roll<self.p:
#             self.add_update()
#             myupdate = True
# # need to modify, possible that shadow cache and original cache evict different block
#             if self.size <= self.get_len(cache):
#                 myevict = True
#         if new_in_cache(hit, update) == new_in_cache(myhit, myupdate):
#             self.evict(blkid)
#         else:
#             if new_in_cache(hit, update):
#                 minus[blkid] = True
#             else:
#                 add[blkid] = True
#         if evicted == myevict:
#              self.evict(tail)
#         else:
#             if evicted:
#                 add[tail] = True
#             else:
#                 minus[tail] = True            

def is_valid_sp(sizeRatio, p):
    if p > 1 or p <= 0:
        return False
    if sizeRatio > 0.8 or sizeRatio < 0.1:
        return False
    return True


# 这是和整个device有关的类
class Device(object):
    """docstring for Device"""

    def __init__(self, size, g, cacheDict):
        self.size = size
        self.g = g
        self.cacheDict = cacheDict
        self.usedSize = self.get_total_size()

    # 返回当前device被使用的size
    def get_total_size(self):
        s = 0
        for trace in self.cacheDict:
            cache = self.cacheDict[trace]
            s += cache.cache.size
        return s

    # 返回给定的时间和写入量下device的单位时间内租用size大小的缓存，默认k1为1的情况下的cost
    def get_cost(self, write, time, size):
        # print("write=", write, ",size=", size, ",g=", self.g, ",time=", time)
        if write > self.size * self.g * time:
            return 1.0*write/self.g/time
        return size
    
    # 判断给定方案的size是否越界，返回修改方案改变的s和p，如果不改变返回空值
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

    # 选择最佳配置的帮助函数
    def get_best_config_help(self, potentials, selected, size, write):
        # print("len(potentials)=", len(potentials))
        # print("selected目前组成是：")
        # for i in range(len(selected)):
        #     print(i, selected[i].get_size(), selected[i].get_p())
        # assert(len(selected)<=3)
        if potentials==[]:
            # print("minWrite=", self.minWrite, ",write=", write, ",size=", size)
            if self.minWrite == None or write < self.minWrite:
                self.minWrite = write
                self.configList = []
                # i = 0
                for item in selected:
                    self.configList.append(item)
                    # print("item,", i, item.p, item.size)
                    # i += 1
            return
        items = potentials[0]
        tempSelected = copy.copy(selected)
        for item in items:
            s = item.size
            w = item.get_update()
            if size + s > self.size:
                continue
            tempSelected.append(item)
            # print("before", len(selected))
            self.get_best_config_help(potentials[1:], tempSelected, size+s, write+w)
            tempSelected = tempSelected[:-1]
            # print("after", len(selected))


        

    def get_best_config(self, potentials):
        self.minWrite = None
        self.configList = []
        self.get_best_config_help(potentials, [], 0, 0)
        # print("size", len(self.configList))
        # for i in range(len(self.configList)):
        #     print("get_best_config结果：")
        #     print(i)
        #     item = self.configList[i]
        #     item.print_sample()
        return self.configList

        
# mtc项目定制的缓存类
# 重要的元素是baseline, cache和samples
class Cache(object):
    """docstring for Cache"""
    def __init__(self, trace, bsizeRatio, csizeRatio, ucln, p, policy):
        self.trace = trace
        self.bsizeRatio = bsizeRatio
        self.cacheSizeRatio = csizeRatio
        # self.p = p
        self.ucln = ucln
        # policy = nrsamples, hit throt, +-s, +-p
        self.policy = policy
        self.baseline = PLRU(int(bsizeRatio*ucln), p)
        self.cache = PLRU(int(csizeRatio*ucln), p)
        self.req = 0
        self.lastBaseUpdate = 0
        self.lastCacheUpdate = 0
        self.init_samples()        

    def init_samples(self):
        self.samples = []
        self.lastBaseUpdate += self.baseline.get_update()
        self.lastCacheUpdate += self.cache.get_update()
        self.cache.update = 0
        self.baseline.update = 0
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
        # 极端情况：某个trace在第一个周期内没有req，在get_potential中调用此函数
        # 需要加个条件判断
        if self.req == 0:
            return False

        baseline = self.baseline.get_hit()

        h = 1.0*(baseline - hit)/self.req
        # if (hit!=baseline):            
        #     print("baseline", baseline, ",cache", hit, ",Dratio=", h)
        if h > self.policy["throt"]:
            return True
        return False

    # def get_close_potentials(self):
    #     # print("enter get close potentials")
    #     sizeRatio = self.cacheSizeRatio
    #     size = int(sizeRatio*self.ucln)
    #     p = self.cache.p
    #     pt1 = None
    #     pt2 = None
    #     for pt in self.samples:
    #         if pt.size == size and pt.p==p+self.policy["deltap"]:
    #             pt1 = pt
    # 这个地方代码写的有问题
    #         elif pt.size == size+self.policy["deltas"] and pt.p == p:
    #             pt2 = pt
    #         if pt1!=None and pt2!=None:
    #             return (pt1, pt2)
    #     return (pt1, pt2)

    def do_req(self, rw, blkid):
        random.seed()
        roll = random.random()
        self.req += 1
        self.do_req_help(self.baseline, rw, blkid, roll)
        self.do_req_help(self.cache, rw, blkid, roll)
        for s in self.samples:
            self.do_req_help(s, rw, blkid, roll)
        # print("self=", self)
        # 命中率过低
        if self.exceed_throt(self.cache.hit):
            return True
            # print("after self=", self)
            # (p1, p2) = self.get_close_potentials()
            # if p1==None and p2==None:
            #     return (False, self.policy["deltas"], self.policy["deltap"])
            # elif p1==None:
            #     return (True, (p2.size-self.cache.size, p2.p-self.cache.p), self.policy["deltas"])
            # elif p2==None:
            #     return (True, (p1.size-self.cache.size, p1.p-self.cache.p), None)
            # if p1.get_hit() > p2.get_hit():
            #     return (True, (p1.size-self.cache.size, p1.p-self.cache.p), (p2.size-self.cache.size, p2.p-self.cache.p))
            # return (True, (p2.size-self.cache.size, p2.p-self.cache.p), (p1.size-self.cache.size, p1.p-self.cache.p))
        return False

    def get_hit_scheme_help(self, scheme):
        (s, p) = scheme
        for item in self.samples:
            if item.size == s and item.p == p:
                return item.get_hit()
        return 0

    def get_hit_scheme(self):
        newSize = self.cache.size + int(self.policy["deltas"]*self.ucln)
        scheme1 = (newSize, self.cache.p)
        hit1 = 0
        if is_valid_sp(1.0*newSize/self.ucln, self.cache.p):
            hit1 = self.get_hit_scheme_help(scheme1)
        else:
            scheme1 = None
        newP = self.cache.p + self.policy["deltap"]
        scheme2 = (self.cache.size, newP)
        hit2 = 0
        if is_valid_sp(self.cache.size, newP):
            hit2 = self.get_hit_scheme_help(scheme2)
        else:
            scheme2 = None
        if hit1 >= hit2:
            return (scheme1, scheme2)
        return (scheme2, scheme1)

    def change_config(self, s, p):
        # size = s+self.cache.size
        # p = p+self.cache.p
        self.cache.change_size(s)
        self.cache.change_p(p)

        self.cacheSizeRatio = round(1.0*s/self.ucln, 2)
        # print(self.trace, s, p, self.ucln, self.req, self.cacheSizeRatio, self.cacheSizeRatio>=1)
        assert self.cacheSizeRatio < 1
        # if self.cacheSizeRatio >= 1:
        #     print("trace", self.trace, ",sr=", self.cacheSizeRatio, ",s=", s, "p=", p)
        #     sys.exit(-1)
        # print("sr=", self.cacheSizeRatio)
    # give potentials inside the hit range
    # remove bad ones (both s and p are larger)
    def get_potential(self):
        potentials = []
        results = []
        # print("debug", self.req, self.)
        for sample in self.samples:
            if self.exceed_throt(sample.get_hit()):
                continue
            potentials.append(sample)
            # 注释掉优化后加
            results.append(sample)
        # print("sample", sample)
        # 这段是想要优化的，先注释掉吧
        # for i in range(len(potentials)):
        #     sign = False
        #     for j in range(len(potentials)):
        #         # print(i, j, potentials[i].size, potentials[j].size, potentials[i].update, potentials[j].update)
        #         # print(sign)
        #         if i==j:
        #             continue
        #         if potentials[i].size >= potentials[j].size and potentials[i].update >= potentials[j].update:
        #             sign = True
        #             break
        #     # print(sign)
        #     if not sign:
        #         # print("debug", potentials[i].get_size(), potentials[i].get_update(), potentials[i].get_p())
            # results.append(potentials[i])

        results.append(self.cache)
        return results
    
    # 因为中间计算时把cache的update减去了，这里加回来
    def finish(self):
        self.baseline.update += self.lastBaseUpdate
        self.cache.update += self.lastCacheUpdate
        
                    