from __future__ import print_function
import sys
import os
import time




log = "/root/bn/metadata.csv"
logFile = open(log, "a")

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
    outfile.close()

l = ["ts_0", "wdev_0"]
for i in l:
    print(i)
    start = time.clock()
    handle_csv(i, i + ".csv")            
    end = time.clock()
    print("consumed ", end-start, "s")
logFile.close()                   
                 
  







