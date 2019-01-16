from __future__ import print_function
import operator 
import time
import sys
import math
import random
# add trace workflow:
# add ucln
# add path

# run overflow:
# 

uclnDict = {"netsfs":47949, "mix":195423,
# "mds_0":	769376,
"hm_0":	488986,
"prn_0":	985474,
"proj_0":	462462,
"prxy_0":	79483,
"rsrch_0":	20855,
# "src1_0":	31656826,
# "usr_1":	171538746,
"src2_0":	104953,
# "stg_0":	1608935,
# "ts_0":	131140,
# "wdev_0":	52111,
# "web_0":	1887115,

"probuild": 1970,
"bs24":	4155,
"bs39":	12190,
"dev5.3.7.19":	1873854,
"dev5.3.11.19":	1081695,
"live6.31":	30393264,
"live3.31":	6920465,
"mfs253":	2222973,
"mfs101":	1408158,
"msc116":	216158,
"msc651":	128895,
"dad807":	294190,
"dap812":	224019,

"prn_1" :	19343730 ,
# "proj_2" : 	107472935,
"proj_3" : 	1383543,
# "prxy_1" : 	196870,
# "src1_1" : 	30780233,
# "src2_1" : 	5019544,
"usr_0" : 	554527,
# "web_2" :	17610218,

"fileserver":	3840461,
"mongo":	287694,
"webproxy":	378100,

"web_3":	58776,
"rsrch_2":	174674,
"wdev_0":	52111,
"mds_0":	769376,
"ts_0":	131140,
"web_1":	962441,
"stg_0":	1608935,
"hm_0":	488986,
"web_0":	1887115,
"src2_2":	5325043,
"proj_3":	1383543,
"usr_0":	554527,
"src2_1":	5019544,
"stg_1":	20865229,
"mds_1":	22014981,
"proj_4":	32411052,
"prn_1":	19343730,
"web_2":	17610218,
"usr_2":	99264060,
"prxy_1":	196870,
"src1_0":	31656826,
"proj_1":	183030933,
"proj_2":	107472935,
"src1_1":	30780233,
"usr_1":	171538746,
"usr_10":	34659971,
"usr_20":	31968051,
"prxy_10":	33713	

}
pathDirCam = "/home/trace/ms-cambridge/"
pathDictHome = "/home/trace/"

pathDict = {
"bs24":	"/mnt/raid5/trace/MS-production/BuildServer/Traces/24.hour.BuildServer.11-28-2007.07-24-PM.trace.csv.req",
"bs39":	"/mnt/raid5/trace/MS-production/BuildServer/Traces/24.hour.BuildServer.11-28-2007.07-39-PM.trace.csv.req",
"dev5.3.7.19":	"/home/bn/python/DevelopmentToolsRelease/Traces/DevDivRelease.03-05-2008.07-19-PM.trace.csv.req",
"dev5.3.11.19":	"/home/bn/python/DevelopmentToolsRelease/Traces/DevDivRelease.03-05-2008.11-19-PM.trace.csv.req",
"live6.31":	"/home/bn/python/LiveMapsBackEnd/Traces/LiveMapsBE.02-21-2008.06-31-PM.trace.csv.csv.req",
"live3.31":	"/home/bn/python/LiveMapsBackEnd/Traces/LiveMapsBE.02-21-2008.03-31-PM.trace.csv.csv.req",
"mfs253": "/home/bn/python/MSNStorageFileServer/Traces/MSNFS.2008-03-10.02-53.trace.csv.csv.req",
"mfs101": "/home/bn/python/MSNStorageFileServer/Traces/MSNFS.2008-03-10.01-01.trace.csv.csv.req",
"msc116": "/home/bn/python/MSNStorageCFS/Traces/CFS.2008-03-10.01-16.trace.csv.csv.req",
"msc651": "/home/bn/python/MSNStorageCFS/Traces/CFS.2008-03-10.06-51.trace.csv.csv.req",
"dad807": "/home/bn/python/DisplayAdsDataServer/Traces/DisplayAdsDataServer.2008-03-08.08-07.trace.csv.csv.req",
"dap812": "/home/bn/python/DisplayAdsPayload/Traces/DisplayAdsPayload.2008-03-08.08-12.trace.csv.csv.req",
"netsfs" : "filebench-netsfs.req",
"mix" : "mix-trace.req",
"probuild" : "production-build00-1-4K.req"
}



def getPath(traceID, typeID):
	if typeID == "home":
		return pathDictHome + pathDict[traceID]
	if typeID == "cam":
		return pathDirCam + traceID + ".csv.req"
	if typeID == "production":
		return pathDict[traceID]
	if typeID == "filebench":
		return "/home/chai/go_filebench-1.4.8.fsl.0.8/workloads/" + traceID + "/test1_short.txt.req"

PERIODNUM = 10
PERIODLEN = 10 ** 5
logFilename = "/root/bn/result.csv"
# SIZERATE = 0.1

class MyNode(object):
    """docstring for MyNode"""
    def __init__(self):
        self.empty = True

class PLRU(object):
    """docstring for LRU"""
    def __init__(self, size, p):
        # 	super().__init__()
        # print(size, p)
        self.hit = 0
        self.update = 0
        self.size = size
        self.ssd = {}
        self.head = MyNode()
        self.head.next = self.head
        self.head.prev = self.head
        self.p = p
        self.listSize = 1
        # Adjust the size
        self.change_size(size)
    def __len__(self):
        return len(self.ssd)

    def clear(self):
        for node in self.dli():
            node.empty = True
        self.ssd.clear()


    def is_hit(self, key):
        if key in self.ssd:
            self.hit += 1
            return True
        return False

    def get_hit(self):
    	return self.hit

    def add_hit(self):
    	self.hit += 1

    def get_update(self):
    	return self.update

    def add_update(self):
    	self.update += 1


     #para : block to update
     #function : if hit, move block to head; else, p probabity to update new block
     #return : {evictedBlock, updatedBlock} if updated; None if not
    def update_cache(self, key):
        # First, see if any value is stored under 'key' in the cache already.
        # If so we are going to replace that value with the new one.
        if key in self.ssd:
            # Lookup the node
            node = self.ssd[key]
            # Update the list ordering.
            self.mtf(node)
            self.head = node
            return (None, None)

        # Ok, no value is currently stored under 'key' in the cache. We need
        # to choose a node to place the new item in. There are two cases. If
        # the cache is full some item will have to be pushed out of the
        # cache. We want to choose the node with the least recently used
        # item. This is the node at the tail of the list. If the cache is not
        # full we want to choose a node that is empty. Because of the way the
        # list is managed, the empty nodes are always together at the tail
        # end of the list. Thus, in either case, by chooseing the node at the
        # tail of the list our conditions are satisfied.

        # test p
        random.seed()
        roll = random.random()
        if roll>=self.p:
        	return (None, -1)

        # Since the list is circular, the tail node directly preceeds the
        # 'head' node.




        self.update += 1
        node = self.head.prev
        oldKey = None
        # If the node already contains something we need to remove the old
        # key from the dictionary.
        if not node.empty:
        	oldKey = node.key
        	del self.ssd[node.key]

        # Place the new key and value in the node
        node.empty = False
        node.key = key
        
        # Add the node to the dictionary under the new key.
        self.ssd[key] = node

        # We need to move the node to the head of the list. The node is the
        # tail node, so it directly preceeds the head node due to the list
        # being circular. Therefore, the ordering is already correct, we just
        # need to adjust the 'head' variable.
        self.head = node
        return (oldKey, key)


    def delete_cache(self, key):

        # Lookup the node, then remove it from the hash ssd.
        if key not in self.ssd:
            return
        node = self.ssd[key]
        del self.ssd[key]

        node.empty = True

        

        # Because this node is now empty we want to reuse it before any
        # non-empty node. To do that we want to move it to the tail of the
        # list. We move it so that it directly preceeds the 'head' node. This
        # makes it the tail node. The 'head' is then adjusted. This
        # adjustment ensures correctness even for the case where the 'node'
        # is the 'head' node.
        self.mtf(node)
        self.head = node.next

    

    # This method adjusts the ordering of the doubly linked list so that
    # 'node' directly precedes the 'head' node. Because of the order of
    # operations, if 'node' already directly precedes the 'head' node or if
    # 'node' is the 'head' node the order of the list will be unchanged.
    def mtf(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

        node.prev = self.head.prev
        node.next = self.head.prev.next

        node.next.prev = node
        node.prev.next = node

    # This method returns an iterator that iterates over the non-empty nodes
    # in the doubly linked list in order from the most recently to the least
    # recently used.
    def dli(self):
        node = self.head
        for i in range(len(self.ssd)):
            yield node
            node = node.next

    def change_size(self, size):        
        if size > self.listSize:
            self.add_tail_node(size - self.listSize)
        elif size < self.listSize:
            self.remove_tail_node(self.listSize - size)
        return self.listSize

    # Increases the size of the cache by inserting n empty nodes at the tail
    # of the list.
    def add_tail_node(self, n):
        for i in range(n):
            node = MyNode()
            node.next = self.head
            node.prev = self.head.prev

            self.head.prev.next = node
            self.head.prev = node

        self.listSize += n

    # Decreases the size of the list by removing n nodes from the tail of the
    # list.
    def remove_tail_node(self, n):
        assert self.listSize > n
        for i in range(n):
            node = self.head.prev
            if not node.empty:
                del self.ssd[node.key]
            # Splice the tail node out of the list
            self.head.prev = node.prev
            node.prev.next = self.head
        self.listSize -= n

    def get_top_n(self, number):
        node = self.head
        l = []
        for i in range(0, min(number, len(self.ssd))):
            l.append(node.key)
            node = node.next
        # print("debug", len(l), l==None)
        return l

    def print_sample(self):
        print("print LRU ssd")
        if len(self.ssd) <= 100:            
            node = self.head
            for i in range(len(self.ssd)):
                print(node.key, end=",")
                node = node.next        
            print()
        print("hit", self.hit)
        print("write", self.update)

    def update_cache_k(self, throt, potentialDict):

        node = potentialDict.head
        # print("potential dict")
        # print(len(potentialDict.ssd))
        # potentialDict.print_sample()
        throt = min(throt, len(potentialDict.ssd))
        for i in range(1, throt):
            node = node.next
        for i in range(0, throt):
            self.update_cache(node.key)
            # print(node.key)
            node = node.prev
		


def load_file(traceID, typeID, sizerate=0.1, p=1):
	readReq = 0
	# print(traceID)

	size = int(sizerate*uclnDict[traceID])
	# print(sizerate*uclnDict[traceID], size)
	ssd = PLRU(size, p)
	fin = open(getPath(traceID, typeID), 'r')
	lines = fin.readlines()
	print("load file finished")
	for line in lines:
		items = line.split(' ')
		reqtype = int(items[0])
		block = int(items[2])
		if reqtype == 1:			
			ssd.delete_cache(block)
		else:		
			if readReq % 1000000 == 0:
				print(readReq)
			readReq += 1
			ssd.is_hit(block)				
			ssd.update_cache(block)
	fin.close()
	print("size", size, p)
	print("total hit rate", 1.0*ssd.hit/readReq, ssd.update)
	logFile = open(logFilename, "a")
	print(traceID, p, sizerate, size, 1.0*ssd.hit/readReq, ssd.update, sep=',', file=logFile)
	logFile.close()


def load_file_time(traceID, typeID, sizerate=0.1, p=1):
    readReq = 0
    # print(traceID)
    historyHit = 0
    historyReq = 0
    size = int(sizerate*uclnDict[traceID])
    # print(sizerate*uclnDict[traceID], size)
    ssd = PLRU(size, p)
    fin = open(getPath(traceID, typeID), 'r')
    lines = fin.readlines()
    print("load file finished")
    logFile = open(logFilename, "a")
    print(traceID, p, sizerate, size, sep=",", end=",", file=logFile)
    for line in lines:
        items = line.split(' ')
        reqtype = int(items[0])
        block = int(items[2])
        if reqtype == 1:            
            ssd.delete_cache(block)
        else:       
            if readReq % PERIODLEN == 0 and readReq!=0:
                localHitRatio = 1.0*(ssd.hit-historyHit)/(readReq-historyReq)
                historyHit = ssd.hit
                historyReq = readReq
                print(localHitRatio, sep=",", end=",", file=logFile)
            readReq += 1
            ssd.is_hit(block)               
            ssd.update_cache(block)
    fin.close()
    print("size", size, p)
    print("total hit rate", 1.0*ssd.hit/readReq, ssd.update)
    
    print(1.0*ssd.hit/readReq, ssd.update, 1.0*ssd.hit/ssd.update, sep=',', file=logFile)
    logFile.close()

# TRACELIST = ["src2_0", "prn_1", "prxy_0", "hm_0", "proj_3", "usr_0", "wdev_0", "ts_0", "probuild"]
# PLIST = [0.2, 0.4, 0.6, 0.8, 1]
# SIZERATELIST = [0.01, 0.05, 0.1, 0.2, 0.4, 0.6, 0.8]
# traceList = ["wdev_0"]
# for trace in traceList:
# 	for sizerate in [0.01, 0.1, 0.4, 0.8]:
# 		for p in [0.2, 0.6, 1]:
# 			start = time.clock()
# 			load_file_time(trace, "cam", sizerate, p)
# 			end = time.clock()
# 			print(trace, "cam", sizerate, p, "consumed ", end-start, "s")
# 			# sys.exit(-1) 
