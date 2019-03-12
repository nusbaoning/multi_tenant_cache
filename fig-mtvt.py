# -*- coding: utf-8 -*-  
import random
import csv
import sys
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib import axes
from matplotlib.font_manager import FontProperties
font = FontProperties(fname='/Library/Fonts/Songti.ttc')
mymarkers = ['*', 'o', 'v', 's', '+', 'x', 'd', 'D', '1', '2', '3', '4']
# https://baijiahao.baidu.com/s?id=1608586625622704613&wfr=spider&for=pc
# https://www.cnblogs.com/altlb/p/7160191.html
# csvfile = open('test.csv', 'rb')
# reader = csv.reader(csvfile, delimiter=',')
# pList = []
# sList = [] 
# i = 0

# 将mtvt_result.csv文件手动挑选+改格式之后画图的代码
# for row in reader:
#     i += 1
#     # print row
#     if i%2 == 0:
#         for item in row[1:]:
#             if item == '':
#                 break
#             sList.append(float(item))
#         plt.plot(pList, sList, marker=marker[i/2-1], label=title)
#         pList = []
#         sList = []
#     else:
#         title = row[0]
#         for item in row[1:]:
#             if item == '':
#                 break
#             pList.append(float(item))

# csv file style
# trace, p, size ratio, s, hit ratio, update
# data structure
# dict key = (trace, hit ratio), value = [(p,s)]
# in dict, hit ratio is int
def load_mtvt_file(filename):
    d = {}
    with open(filename, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            # print row
            trace = row[0]
            p = float(row[1])
            size = float(row[2])
            # value = int(1000*float(row[4]))
            hr = int(float(row[4])*100)
            key = (trace, hr)
            value = (p, size)
            if key in d and value not in d[key]:
                d[key].append(value)
            else:
                d[key] = [value]
    csvfile.close()
    return d

def do_trace(trace, l, d, num=3):
    fig = plt.figure()
    minhr = l[0][1]
    maxhr = l[-1][1]

    length = 1.0*(maxhr - minhr)/3
    present = minhr + length
    print(minhr, maxhr, length, present)
    maxnum = 0
    maxkey = None
    i = 0


    for j in range(0, len(l)):
        key = l[j]
        hr = key[1]
        if hr < present:
            num = len(d[key])
            if (trace, hr-1) in d:
                num += len(d[trace, hr-1])
            if (trace, hr+1) in d:
                num += len(d[trace, hr+1])

            if num > maxnum:
                maxnum = num
                maxkey = key
        else:
            pList = []
            sList = []
            print(maxkey)
            for (p,s) in d[maxkey]:
                pList.append(p)
                sList.append(s) 
            hr = maxkey[1] 
            if (trace, hr-1) in d:
                for (p,s) in d[(trace, hr-1)]:
                    pList.append(p)
                    sList.append(s) 
            if (trace, hr+1) in d:
                for (p,s) in d[maxkey]:
                    pList.append(p)
                    sList.append(s) 
            print(trace, maxnum)
            print("present", present)
            plt.plot(pList, sList, marker=mymarkers[i], label=hr)
            i += 1
            if i >= num:
                break
            maxnum = len(d[key])
            maxkey = key
            present += length
            

    # plt.plot(pList, sList, marker='*')
    plt.xticks(rotation=45)
    plt.xlabel('p')
    plt.ylabel('size rate')
    plt.title(trace)
    plt.legend()
    # plt.show()
    plt.savefig(trace + '_mtvt.png', dpi=300)
    # sys.exit(-1)

filename = "mtvt_result.csv"
d = load_mtvt_file(filename)
keys = d.keys()
keys.sort()
present = None
s = 0
i = 0
for key in keys:
    trace = key[0]
    if present == None:
        present = trace
        s = i
    elif present == trace:
        pass
    else:
        do_trace(present, keys[s:i], d)
        s = i
        present = trace
    i += 1


