from __future__ import print_function
import math
path = "/home/trace/ms-cambridge/part/"

# assume that s|ttl%3600=0
def load_lines(trace, ttl, ul, s, lines):
    traceFileLength = 3600
    # ul=1, s=0/3600, fileStart=0/1, ttl=3600/7200, fileEnd=1/2/2/3
    fileStart = s / (traceFileLength/ul)
    fileEnd = (s+ttl) / (traceFileLength/ul)
    nrfile = ttl/traceFileLength
    for i in range(fileStart, fileEnd):
        filename = path + trace + "_" + str(i+1) + ".req"
        fp = open(filename, "r")
        l = fp.readlines()
        lines.extend(l)
        fp.close()


def parse_line(line, mode):
    items = line.split(',')
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
    
    timeUnitEnd = start + unitLength
    timeEnd = start + totalTimeLength
    lines = []
    idxlist = []
    filename = path + "mix" + "_" + str(len(traces)) + ".req"
    logfile = open(filename, 'w')
    for trace in traces:
        lines.append([])
        idxlist.append(0)
    for i in range(len(traces)):
        load_lines(traces[i], totalTimeLength, unitLength, start, lines[i])
    while True:
        for i in range(len(traces)):
            while True:
                (time, rw, blkid) = parse_line(lines[i][idxlist[i]], "gen")
                if time > timeUnitEnd:
                    break
                print(trace, time, rw, blkid, file=logfile)
                idxlist[i] += 1
        timeUnitEnd += unitLength
        if timeUnitEnd >= timeEnd:
            break
    logfile.close()
        
def get_reqs(traces, totalTimeLength, unitLength):
    filename = path + "mix" + "_" + str(len(traces)) + ".req"
    fp = open(filename, 'r')
    lines = fp.readlines()
    return lines

generate_reqs(traces, totalTimeLength, unitLength, start)

# init
cacheDict = {}
for trace in traces:
    cache = Cache(trace, size, p, policy)
    cacheDict[trace] = cache
# g=tbw/lifespan/capacity
device = Device(size, g, cacheDict)
periodStart = 0

reqs = get_reqs(traces, totalTimeLength, unitLength)
    
for req in reqs:
    (trace, time, rw, blkid) = parse_line(req, "get")
    (needInmediateM, scheme1, scheme2) = cacheDict[trace].do_req(rw, blkid)
    if needInmediateM:
        (s, p) = device.try_modify(scheme1, scheme2)
        cacheDict[trace].change_config(s, p) 
    if time - periodStart >= periodLength:
        periodStart = time
        potentials = []
        for trace in traces:
            potentials.append(cacheDict[trace].get_potential())
        result = device.get_best_config(potentials)
        for i in (0, len(traces)):
            cacheDict[traces[i]].change_config(result[i].size, result[i].p)
            cacheDict[trace[i]].init_samples()

write = get_total_write(cacheDict)
cost = device.get_cost(time, write)
print_result(device, cacheDict)
