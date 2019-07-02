from __future__ import print_function
import math
import mtc_data_structure
import time
# path = "/home/trace/ms-cambridge/part/"
path = "./"
danwei = 10**7

# assume that s|ttl%3600=0
def load_lines(trace, ttl, ul, s, lines, uclnDict):
    start = time.clock()
    traceFileLength = 3600*danwei
    # ul=1, s=0/3600, fileStart=0/1, ttl=3600/7200, fileEnd=1/2/2/3
    fileStart = s / traceFileLength
    fileEnd = (s+ttl) / traceFileLength

    nrfile = ttl/traceFileLength
    print("trace", trace, "fileStart", fileStart, "fileEnd", fileEnd, "nrfile", nrfile)
    for i in range(fileStart, fileEnd):
        filename = path + trace + "_" + str(i+1) + ".req"
        fp = open(filename, "r")
        l = fp.readlines()
        lines.extend(l[:-2])
        d = eval(l[-1])
        uclnDict.update(d)
        # print("test", trace, len(d), len(uclnDict))
        fp.close()
    print("load lines consumed", time.clock()-start)

def parse_line(line, mode):
    # print("line", line)
    items = line.strip().split(' ')
    # print("items", items)
    if mode=="gen":
        time = int(items[0])
        rw = int(items[1])
        blkid = int(items[3])
        return (time, rw, blkid)
    # trace, time, rw, blkid
    trace = items[0]
    time = int(items[1])
    rw = int(items[2])
    blkid = int(items[3])
    return (trace, time, rw, blkid)

# assume that unit length is 1s and do not need to mix inside a unit
def generate_reqs(traces, totalTimeLength, unitLength, start):
    print("traces", traces)
    timeUnitEnd = start + unitLength
    timeEnd = start + totalTimeLength
    lines = []
    idxlist = []
    uclnDict = []
    filename = path + "mix" + "_" + str(len(traces)) + ".req"
    logfile = open(filename, 'w')
    for trace in traces:
        lines.append([])
        idxlist.append(0)
        uclnDict.append({})
    for i in range(len(traces)):
        load_lines(traces[i], totalTimeLength, unitLength, start, lines[i], uclnDict[i])
    while True:
        for i in range(len(traces)):
            while True:
                if idxlist[i] >= len(lines[i]):
                    break
                (time, rw, blkid) = parse_line(lines[i][idxlist[i]], "gen")
                if time > timeUnitEnd:
                    break
                print(traces[i], time, rw, blkid, file=logfile)
                idxlist[i] += 1
        # print("time", time, "timeUnitEnd", timeUnitEnd)
        timeUnitEnd += unitLength
        if timeUnitEnd > timeEnd:
            break
        sign = False
        for i in range(len(traces)):
            if idxlist[i] < len(lines[i]):
                sign = True
                break
        if not sign:
            break
    for i in range(len(traces)):
        print(traces[i], len(lines[i]), idxlist[i])
    logfile.close()
    return uclnDict
        
def get_reqs(traces, totalTimeLength, unitLength):
    filename = path + "mix" + "_" + str(len(traces)) + ".req"
    fp = open(filename, 'r')
    lines = fp.readlines()
    return lines

def get_total_write(cacheDict, mode):
    w = 0
    for trace in cacheDict:
        if mode == "cache":
            w += cacheDict[trace].cache.get_update()
        else:
            w += cacheDict[trace].baseline.get_update()
    return w

def get_total_size(cacheDict, mode):
    s = 0
    for trace in cacheDict:
        if mode == "cache":
            s += cacheDict[trace].cache.size
        else:
            s += cacheDict[trace].baseline.size
    return s

def print_result(traces, device, cacheDict, time):
    logfile = "./total_result.csv"
    fp = open(logfile, 'a')
    for trace in traces:
        print(trace, sep=',', end=',', file=fp)
    print(file=fp)
    write = get_total_write(cacheDict, "base")
    size = get_total_size(cacheDict, "base")
    cost = device.get_cost(time, write)
    print("base", write, size, cost, sep=',', file=fp)
    write = get_total_write(cacheDict, "cache")
    size = get_total_size(cacheDict, "cache")
    cost = device.get_cost(time, write)
    print("cache", write, size, cost, sep=',',  file=fp)

    for trace in traces:
        base = cacheDict[trace].base.get_hit()/cacheDict[trace].req
        cache = cacheDict[trace].cache.get_hit()/cacheDict[trace].req
        print(trace, base, cache, (base-cache<=cacheDict[trace].policy.throt), sep=',', file=fp)


traces = ["prxy_0", "usr_1", "web_0" ]
totalTimeLength = 3600*danwei
unitLength = 1*danwei
start = 0
uclnDict = generate_reqs(traces, totalTimeLength, unitLength, start)
for i in range(len(traces)):
    print(traces[i], len(uclnDict[i]))

# init
cacheDict = {}
sizeRate = 0.1
p = 1
policy = {"nrsamples":3, "deltas":0.1, "deltap":0.1, "throt":0.01}
for i in range(len(traces)):    
    trace = traces[i]
    cache = mtc_data_structure.Cache(trace, sizeRate, len(uclnDict[i]), p, policy)
    cacheDict[trace] = cache
# g=tbw/lifespan/capacity
size = get_total_size(cacheDict, "base")
g = 0.014/3600/danwei
device = mtc_data_structure.Device(2*size, g, cacheDict)
periodStart = 0

# reqs = get_reqs(traces, totalTimeLength, unitLength)
    
# for req in reqs:
#     (trace, time, rw, blkid) = parse_line(req, "get")
#     (needInmediateM, scheme1, scheme2) = cacheDict[trace].do_req(rw, blkid)
#     if needInmediateM:
#         (s, p) = device.try_modify(scheme1, scheme2)
#         cacheDict[trace].change_config(s, p) 
#     if time - periodStart >= periodLength:
#         periodStart = time
#         potentials = []
#         for trace in traces:
#             potentials.append(cacheDict[trace].get_potential())
#         result = device.get_best_config(potentials)
#         for i in (0, len(traces)):
#             cacheDict[traces[i]].change_config(result[i].size, result[i].p)
#             cacheDict[trace[i]].init_samples()


# print_result(traces, device, cacheDict, totalTimeLength)
