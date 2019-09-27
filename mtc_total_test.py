#coding=utf-8
from __future__ import print_function
import math
import mtc_data_structure
import time
import sys
import os
path = "/home/trace/ms-cambridge/part/"
# path = "./"
danwei = 10**7
traceFileName = None

# The program is used to simulate the total test for multi-tenent cache
# input: the output of handle_csv_time_partition of cambridge.py
#        (which means the req files are 1hr each)
# output: the result of original algorithm and advanced algorithm


# Function: 
# 每次调用把某个trace所有相关的lines都load到程序中

# Parameters:
# trace = fileid, "web_0"
# ttl = total time length, unit is 10^-7 second
# s = start, 10^-7
# lines用来存放所有的req lines
# uclnDict是所有的ucln，key是blockid，value没用

# assume that s|ttl%3600=0
def load_lines(trace, ttl, s, lines, uclnDict):
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

# 功能：把读到的一行转变成需要的内容
# mode = "gen", 是整个程序Input的req文件
# mode = "get", 是程序中间生成的mix文件，第一个元素是trace
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

# 功能：混合trace，输出到mix file中
# 目前的程序仍然是所有trace数据都存放到了内存，再输出到文件，再读入。
# 有点蠢。后期如果trace太多，内存不够，可以考虑把代码改成一秒一秒读，输出到文件，再读入

# unitLength the unit length you mix the traces, 10^-7 second
#      例如，ul=1s，说明各个trace file第一秒的req被连接在一起，然后是第2s的
#      1s内的req是不会再被切割的
#      ul设定原则是，必须倍数于后面cache内的优化操作。例如cache调整大小最小单位是0.5s
#      那仍然用1s去混合trace，就会不准
# assume that unit length is 1s and do not need to mix inside a unit
def generate_reqs(traces, totalTimeLength, unitLength, start):
    print("traces", traces)
    timeUnitEnd = start + unitLength
    timeEnd = start + totalTimeLength
    lines = []
    idxlist = []
    uclnDict = []
    global traceFileName
    traceFileName = path + "mix" + "_" + str(time.clock()) + ".req"
    logfile = open(traceFileName, 'w')
    for trace in traces:
        lines.append([])
        idxlist.append(0)
        uclnDict.append({})
    for i in range(len(traces)):
        load_lines(traces[i], totalTimeLength, start, lines[i], uclnDict[i])
    while True:
        for i in range(len(traces)):
            while True:
                if idxlist[i] >= len(lines[i]):
                    break
                (mytime, rw, blkid) = parse_line(lines[i][idxlist[i]], "gen")
                if mytime > timeUnitEnd:
                    break
                print(traces[i], mytime, rw, blkid, file=logfile)
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
    global traceFileName
    fp = open(traceFileName, 'r')
    lines = fp.readlines()
    return lines

# 返回"cache"或者"base"模式下的总写入量
def get_total_write(cacheDict, mode):
    w = 0
    for trace in cacheDict:
        if mode == "cache":
            w += cacheDict[trace].cache.get_update()
        else:
            w += cacheDict[trace].baseline.get_update()
    return w

# 返回"cache"或者"base"模式下的总空间
def get_total_size(cacheDict, mode):
    s = 0
    for trace in cacheDict:
        if mode == "cache":
            s += cacheDict[trace].cache.size
        else:
            s += cacheDict[trace].baseline.size
    return s

# 输出所有结果
def print_result(traces, device, cacheDict, time, start, periodLength, sizeRate, policy):

    logfile = "./total_result.csv"
    fp = open(logfile, 'a')
    print(time/danwei, start/danwei, periodLength/danwei, sizeRate, policy, sep=',', file=fp)
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
        # print(cacheDict[trace].baseline.get_parameters())
        (size, p, update, hit) = cacheDict[trace].baseline.get_parameters()
        print("base", size, p, update, hit, file=fp)
        (size, p, update, hit) = cacheDict[trace].cache.get_parameters()
        print("cache", size, p, update, hit, cacheDict[trace].req, file=fp)

traces = ["prxy_0", "usr_1", "web_0" ]
# traces = ["prxy_0"]
totalTimeLength = 3600*danwei
for i in range(0,10):
    
    unitLength = 1*danwei
    start = i*3600*danwei
    uclnDict = generate_reqs(traces, totalTimeLength, unitLength, start)
    for i in range(len(traces)):
        print(traces[i], len(uclnDict[i]))

    # init
    cacheDict = {}
    sizeRate = 0.1
    p = 1
    policy = {"nrsamples":3, "deltas":0.02, "deltap":0.1, "throt":0.01, "interval":danwei}
    myupdate = {}
    dimdm = {}
    for i in range(len(traces)):    
        trace = traces[i]
        cache = mtc_data_structure.Cache(trace, sizeRate, len(uclnDict[i]), p, policy)
        cacheDict[trace] = cache
        myupdate[trace] = 0
        dimdm[trace] = start
    # g=tbw/lifespan/capacity
    size = get_total_size(cacheDict, "base")
    g = 0.014/3600/danwei
    device = mtc_data_structure.Device(2*size, g, cacheDict)
    periodStart = start
    periodLength = 60*danwei
    reqs = get_reqs(traces)

    print("Reqs = ", len(reqs))
    timestart = time.clock()

# for i in range(2,10):
    # 遍历每个req，进行处理
    for req in reqs:
        (trace, mytime, rw, blkid) = parse_line(req, "get")
        # mytime += i*totalTimeLength
        hit = cacheDict[trace].cache.get_hit()
        (needInmediateM, scheme1, scheme2) = cacheDict[trace].do_req(rw, blkid)
        # 命中
        if cacheDict[trace].cache.get_hit() > hit:
            if rw == 0:
                pass
            else:
                # 写hit
                myupdate[trace] += 1
        # Miss且触发更新操作
        elif cacheDict[trace].cache.get_top_n(1) == [blkid]:
            myupdate[trace] += 1
        # hit不足，触发更新操作
        if needInmediateM and mytime-dimdm[trace]>=policy["interval"]:
            (deltas, deltap) = device.try_modify(scheme1, scheme2)
            s = deltas + cacheDict[trace].cache.get_size()
            p = deltap + cacheDict[trace].cache.get_p()
            cacheDict[trace].change_config(s, p)
            print("hit不足需要更新", "trace=", trace, cacheDict[trace].req,
                "baseline=", cacheDict[trace].baseline.get_hit(),
                "cache=", cacheDict[trace].cache.get_hit(),
             "deltas=", deltas, "deltap=", deltap, "s=", s, "p=", p, sep="\t") 
            # print("test error needInmediateM")
            # sys.exit(0)
        # 一个周期结束，修改所有cache配置
        if mytime - periodStart >= periodLength:
            periodStart = mytime
            potentials = []
            for trace in traces:
                # print("输出", trace, "的候选集：")
                l = cacheDict[trace].get_potential()
                # for tempPotential in l:
                #     tempPotential.print_sample()
                if len(l) == 0:
                    print("debug 候选集为空")
                    break                
                potentials.append(l)
            # print("len(potentials)=", len(potentials))
            if len(potentials) < len(traces):
                result = []
            else:
                result = device.get_best_config(potentials)
                assert(len(result)<=len(traces))
            if len(result) == 0:
                continue
            for i in range(len(traces)):
                print("i=", i, ",trace=", traces[i], result[i].get_size(), result[i].get_p())
                cacheDict[traces[i]].change_config(result[i].get_size(), result[i].get_p())
                cacheDict[traces[i]].init_samples()
    for i in range(len(traces)):
        cacheDict[traces[i]].finish()
    print("myupdate", myupdate)
    print("consumed", time.clock()-timestart, "s")
    print_result(traces, device, cacheDict, totalTimeLength, start, periodLength, sizeRate, policy)
    os.remove(traceFileName)
# for trace in traces:
#     for cache in cacheDict[trace].samples:
#         print(trace)
#         cache.print_sample()