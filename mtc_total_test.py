from __future__ import print_function
import math
import mtc_data_structure
import time
import sys
path = "/home/trace/ms-cambridge/part/"
# path = "./"
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
        print(filename)
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
        
def get_reqs(traces):
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
    cost = device.get_cost(write, time)
    print("base", write, size, cost, sep=',', file=fp)
    write = get_total_write(cacheDict, "cache")
    size = get_total_size(cacheDict, "cache")
    cost = device.get_cost(write, time)
    print("cache", write, size, cost, sep=',',  file=fp)

    for trace in traces:
        base = 1.0*cacheDict[trace].baseline.get_hit()/cacheDict[trace].req
        cache = 1.0*cacheDict[trace].cache.get_hit()/cacheDict[trace].req
        print(trace, base, cache, (base-cache<=cacheDict[trace].policy["throt"]), sep=',', file=fp)
        print(cacheDict[trace].baseline.get_parameters())
        (size, p, update, hit) = cacheDict[trace].baseline.get_parameters()
        print("base", size, p, update, hit, file=fp)
        (size, p, update, hit) = cacheDict[trace].cache.get_parameters()
        print("cache", size, p, update, hit, cacheDict[trace].req, file=fp)

traces = ["prxy_0", "usr_1", "web_0" ]
# traces = ["prxy_0"]
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
policy = {"nrsamples":3, "deltas":0.02, "deltap":0.1, "throt":0.01}
myupdate = {}
for i in range(len(traces)):    
    trace = traces[i]
    cache = mtc_data_structure.Cache(trace, sizeRate, len(uclnDict[i]), p, policy)
    cacheDict[trace] = cache
    myupdate[trace] = 0
# g=tbw/lifespan/capacity
size = get_total_size(cacheDict, "base")
g = 0.014/3600/danwei
device = mtc_data_structure.Device(2*size, g, cacheDict)
periodStart = 0
periodLength = 60*danwei
reqs = get_reqs(traces)

print("Reqs = ", len(reqs))
start = time.clock()

for req in reqs:
    (trace, mytime, rw, blkid) = parse_line(req, "get")
    hit = cacheDict[trace].cache.get_hit()
    (needInmediateM, scheme1, scheme2) = cacheDict[trace].do_req(rw, blkid)
    if cacheDict[trace].cache.get_hit() > hit:
        if rw == 0:
            pass
        else:
            myupdate[trace] += 1
    elif cacheDict[trace].cache.get_top_n(1) == [blkid]:
        myupdate[trace] += 1
    if needInmediateM:
        (deltas, deltap) = device.try_modify(scheme1, scheme2)
        s = deltas + cacheDict[trace].cache.get_size()
        p = deltap + cacheDict[trace].cache.get_p()
        cacheDict[trace].change_config(s, p) 
        # print("test error needInmediateM")
        # sys.exit(0)
    if mytime - periodStart >= periodLength:
        periodStart = mytime
        potentials = []
        for trace in traces:
            potentials.append(cacheDict[trace].get_potential())
        result = device.get_best_config(potentials)
        if len(result) == 0:
            continue
        for i in range(len(traces)):
            cacheDict[traces[i]].change_config(result[i].get_size(), result[i].get_p())
            cacheDict[traces[i]].init_samples()

print("myupdate", myupdate)
print("consumed", time.clock()-start, "s")
print_result(traces, device, cacheDict, totalTimeLength)
for trace in traces:
    for cache in cacheDict[trace].samples:
        print(trace)
        cache.print_sample()