from __future__ import print_function
from mtc_test_size_p import PLRU
import sys
import os
import time

uclnDict = {"usr_1": 172674631, 
"prxy_0": 230657,
"web_0": 1915690}


log = "/root/bn/metadata.csv"
logFile = open(log, "a")
danwei = 10**7


# order starts from 0
# only deal with continuous case 
# in warm mode, try not to use negative order or too big order
# it will take long time to really replace the cache
def handle_csv_time(fileid, filename, order, time, pattern, ssd, fileIdx):
    print("enter handle_csv_time", fileid, order, time, fileIdx)
    block_size = 4096
    flag=False
    readcount=1
    writecount=1   
    readsize = 1
    writesize = 1
    # outname = filename +'.req'
    count = fileIdx
    totalDict = {}
    readDict = {}
    writeDict = {}
    lba=[[sys.maxsize,0], [sys.maxsize,0], [sys.maxsize,0]]
    infile = open(filename, 'r')
    # outfile = open(outname, 'w')
    nrreq = 0
    lines = infile.readlines()
    if pattern=="warm":
        if fileIdx == 0:
            timeStart = -1
            timeEnd = 10**25
        else:
            line = lines[fileIdx]
            line = line.strip().split(',')
            timeBase = int(line[0])
            timeStart = timeBase + order * time
            timeEnd = timeStart + time
        if ssd == None:
            ssd = PLRU(int(0.1 * uclnDict[fileid]), 1)
            oldhit = -1
            oldupdate = -1
        else:
            oldhit = ssd.hit
            oldupdate = ssd.update
    
    if order < 0  and fileIdx == 0:
        line = lines[-1]
    else:
        line = lines[fileIdx]
    line = line.strip().split(',')
    timeBase = int(line[0])
    if fileIdx > 0:
        timeStart = timeBase
    else:
        timeStart = timeBase + order * time
    timeEnd = timeStart + time
    print("time", timeBase/danwei, timeStart/danwei, timeEnd/danwei)
    for line in lines[fileIdx:]:
        count += 1
        line = line.strip().split(',')
        timestamp = int(line[0])
        # print(timestamp, timestamp < timeStart, timestamp > timeEnd)
        if timestamp < timeStart:
            continue
        elif timestamp > timeEnd:
            break
        # first coming
        if not flag:
            lineStart = count
            flag = True
        block_id = int((float(line[4]))/block_size)
        block_end = int((float(line[4])+float(line[5])-1)/block_size)
        if count % 100000 == 0:
            print(count)
        if line[3]=='Write':
            rw = 1
            writecount += 1
            writesize+=block_end-block_id+1
        elif line[3]=='Read':
            rw = 0
            readcount+=1
            readsize+=block_end-block_id+1
        else:
            rw = 2
        if lba[2][0] > block_id:
            lba[2][0] = block_id
        if lba[2][1] < block_end:
            lba[2][1] = block_end
        if lba[rw][0] > block_id:
            lba[rw][0] = block_id
        if lba[rw][1] < block_end:
            lba[rw][1] = block_end
        for i in range(block_id,block_end+1):
            # print('{0} {1} {2}'.format(rw,line[2],i),file=outfile)
            # print>>outfile, '{0} {1} {2}'.format(rw,line[2],i)
            totalDict[i] = True
            
            if rw == 0:
                readDict[i] = True
            elif rw == 1:
                writeDict[i] = True
            if pattern == "warm":
                nrreq += 1
                hit = ssd.is_hit(i)
                if line[3]=='Write' and hit:
                    ssd.add_update()
                ssd.update_cache(i)
        if pattern == "warm" and oldhit<0 and ssd.is_full():
            timeBase = timestamp
            timeStart = timeBase + order * time
            timeEnd = timeStart + time
            nrreq = 0
            ssd.oldhit = ssd.hit
            ssd.oldupdate = ssd.update
            readsize = 0
            writesize = 0
            flag = False
    # print("read write", readcount, writecount, readcount/writecount, readsize, writesize, readsize/writesize, sep=',')
    # print("ucln", len(totalDict), len(readDict), len(writeDict), 
        # lba[2][1]-lba[2][0]+1, lba[0][1]-lba[0][0]+1, lba[1][1]-lba[1][0]+1, sep=',')
    lineStop = count
    print(fileid, pattern, order, time/danwei,  
        readsize, writesize, round(1.0*readsize/(readsize+writesize), 2), 
        sep=',', end=',', file=logFile)
    infile.close()
    # outfile.close()
    if pattern!="warm":
        nrreq = 0
        assert len(totalDict)>0
        ssd = PLRU(int(0.1 * len(totalDict)), 1)
        infile = open(filename, 'r')
        # outfile = open(outname, 'w')
        lines = infile.readlines()
        for line in lines[lineStart-1: lineStop]:
            line = line.strip().split(',')
            timestamp = int(line[0])
            # if timestamp < timeStart:
            #     continue
            # elif timestamp > timeEnd:
            #     break
            block_id = int((float(line[4]))/block_size)
            block_end = int((float(line[4])+float(line[5])-1)/block_size)
            if count % 100000 == 0:
                print(count)
            for req in range(block_id, block_end+1):
                nrreq += 1
                hit = ssd.is_hit(req)
                if line[3]=='Write' and hit:
                    ssd.add_update()
                ssd.update_cache(req)
        hit = ssd.hit
        update = ssd.update
    else:
        hit = ssd.hit - oldhit
        update = ssd.update - oldupdate

    print(fileid, hit, nrreq, 1.0*hit/nrreq, update)
    print(nrreq, ssd.size, hit, 1.0*hit/nrreq, update, sep=',', file=logFile)
    logFile.flush()
    return (ssd, count)

def handle_csv(fileid, filename):
    block_size = 4096
    flag=False
    readcount=0
    writecount=0   
    readsize = 0
    writesize = 0 
    outname = filename +'.req'
    count = 0
    totalDict = {}
    readDict = {}
    writeDict = {}
    lba=[[sys.maxsize,0], [sys.maxsize,0], [sys.maxsize,0]]
    infile = open(filename, 'r')
    outfile = open(outname, 'w')

    for line in infile.readlines():
        count += 1
        line = line.strip().split(',')
        block_id = int((float(line[4]))/block_size)
        block_end = int((float(line[4])+float(line[5])-1)/block_size)
        if count % 100000 == 0:
            print(count)
        if line[3]=='Write':
            rw = 1
            writecount += 1
            writesize+=block_end-block_id+1
        elif line[3]=='Read':
            rw = 0
            readcount+=1
            readsize+=block_end-block_id+1
        else:
            rw = 2
        if lba[2][0] > block_id:
            lba[2][0] = block_id
        if lba[2][1] < block_end:
            lba[2][1] = block_end
        if lba[rw][0] > block_id:
            lba[rw][0] = block_id
        if lba[rw][1] < block_end:
            lba[rw][1] = block_end
        for i in range(block_id,block_end+1):
            print('{0} {1} {2}'.format(rw,line[2],i),file=outfile)
            # print>>outfile, '{0} {1} {2}'.format(rw,line[2],i)
            totalDict[i] = True
            
            if rw == 0:
                readDict[i] = True
            elif rw == 1:
                writeDict[i] = True

    print("read write", readcount, writecount, readcount/writecount, readsize, writesize, readsize/writesize, sep=',')
    print("ucln", len(totalDict), len(readDict), len(writeDict), 
        lba[2][1]-lba[2][0]+1, lba[0][1]-lba[0][0]+1, lba[1][1]-lba[1][0]+1, sep=',')
    print(fileid, readcount+writecount, readcount, writecount, round(readcount/writecount, 2), 
        readsize+writesize, readsize, writesize, round(readsize/writesize, 2), 
        len(totalDict), len(readDict), len(writeDict), 
        lba[2][1]-lba[2][0]+1, lba[0][1]-lba[0][0]+1, lba[1][1]-lba[1][0]+1, sep=',', file=logFile)
    # l = [readcount, writecount, readcount/writecount, readsize, writesize, readsize/writesize]
    # print "read write",
    # for item in l:
    # 	print item,
    # print

    # l = [len(totalDict), len(readDict), len(writeDict), lba[2][1]-lba[2][0]+1, lba[0][1]-lba[0][0]+1, lba[1][1]-lba[1][0]+1]
    # print "ucln",
    # for item in l:
    # 	print item,
    # print

    # l = [fileid, readcount+writecount, readcount, writecount, round(readcount/writecount, 2),  
    # readsize+writesize, readsize, writesize, round(readsize/writesize, 2), len(totalDict), len(readDict), 
    # len(writeDict), lba[2][1]-lba[2][0]+1, lba[0][1]-lba[0][0]+1, lba[1][1]-lba[1][0]+1]
    # for item in l:
    # 	print >> logFile, item,
    # print
    infile.close()
    outfile.close()

def handle_req(fileid, filename):
    fin = open(filename, 'r')
    lines = fin.readlines()
    totalDict = {}
    readDict = {}
    writeDict = {}
    lba=[[sys.maxsize,0], [sys.maxsize,0], [sys.maxsize,0]]
    readcount = writecount = 0
    for line in lines:
        items = line.split(' ')
        reqtype = int(items[0])
        block = int(items[2])
        if reqtype == 1:            
            writecount += 1   
            writeDict[block] = True         
        else:       
            readcount += 1
            readDict[block] = True
        totalDict[block] = True
        if lba[2][0] > block:
            lba[2][0] = block
        if lba[2][1] < block+1:
            lba[2][1] = block+1
        if lba[reqtype][0] > block:
            lba[reqtype][0] = block
        if lba[reqtype][1] < block+1:
            lba[reqtype][1] = block+1
    print("read write", readcount, writecount, readcount/writecount, -1, -1, -1, sep=',')
    print("ucln", len(totalDict), len(readDict), len(writeDict), 
        lba[2][1]-lba[2][0]+1, lba[0][1]-lba[0][0]+1, lba[1][1]-lba[1][0]+1, sep=',')
    print(fileid, readcount+writecount, readcount, writecount, round(readcount/writecount, 2), 
        -1, -1, -1, -1, 
        len(totalDict), len(readDict), len(writeDict), 
        lba[2][1]-lba[2][0]+1, lba[0][1]-lba[0][0]+1, lba[1][1]-lba[1][0]+1, sep=',', file=logFile)
    fin.close()

l = ["usr_1"] 
# l = ["usr_1", "prxy_0", "web_0" ]
# l = ["prn_1", "prxy_0", "hm_0", "proj_3", "usr_0", "ts_0", "wdev_0"]
# for root, dirs, files in os.walk('/home/trace/ms-cambridge'):  
# for i in l:
mode = "warm"
for i in l:
    ssd_stored = None
    fileIdx_stored = 0
    # 1s, 1h, 1day
    for timeLength in [60*danwei, 3600*danwei, 24*3600*danwei]:
        if mode=="warm":
            ssd = ssd_stored
            fileIdx = fileIdx_stored
        else:
            ssd = None
            fileIdx = 0
        for order in range(0, 5):
            start = time.clock()
            (ssd, fileIdx) = handle_csv_time(i, "/home/trace/ms-cambridge/" + i + ".csv", 
                order, timeLength, "warm", ssd, fileIdx)
            if ssd_stored==None:
                ssd_stored = ssd
                fileIdx_stored = fileIdx
    # handle_csv_time(i, "/home/trace/ms-cambridge/" + i + ".csv", 0, 3600*10000000)            
            end = time.clock()
            print(i, order, timeLength/danwei, start, end, "consumed ", end-start, "s")
                 
                 
# handle_req("probuild", "/home/trace/" + "production-build00-1-4K.req")
# logFile.close()