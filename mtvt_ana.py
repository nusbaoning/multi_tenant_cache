# -*- coding: utf-8 -*-  
import csv
import sys

traceMtvtDict = {'prn_1': [26, 34, 38], 'ts_0': [14, 48, 79], 'usr_0': [72, 77, 80], 
'wdev_0': [20, 63, 86], 'proj_3': [24, 36, 67], 'prxy_0': [41, 49, 67], 
'hm_0': [31, 38, 52], 'src2_0': [36, 39, 48]}

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
            hr = float(100*row[4])
            key = trace
            value = (p, size, hr)
            if key in d and value not in d[key]:
                d[key].append(value)
            else:
                d[key] = [value]
    csvfile.close()
    return d



# whether p1<=p2 and s1<=s2, hr1<=hr2
def check_ps_principle(filename, d): 
    result = []
    rate = 0
    
    traces = d.keys()
    traces.sort()
    for trace in traces:
        s = 0
        r = 0
        l = d[trace]
        for i in range(0, len(l)):
            for j in range(i+1, len(l)):
                a = l[i]
                b = l[j]
                if a[0] <= b[0]:
                    if a[1] <= b[1]:
                        s += 1
                        if a[2] <= b[2]:
                            r += 1
                elif a[1] >= b[1]:
                    s += 1
                    if a[2] >= b[2]:
                        r += 1
        result.append((r, s, 1.0*r/s))
        rate += 1.0*r/s
    print(result)
    print(rate/len(traces))

# input key=trace, value=[(p,s,hr)]
# output key = (trace, p, s), value = hr
def convert_d(d, hitRange):
    dLookup = {}
    for key in d.keys():
        l = d[key]
        for item in l:
            (p, s, hr) = item
            dLookup[(key, p, s)] = hr
    return dLookup

# return the best config as（cost, p, s)
def get_config():
    pass


filename = "mtvt_result.csv"
d = load_mtvt_file(filename)    
hitRange = 1
pList = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
sList = [0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.15, 0.2, 0.25, 0.3]
dLookup = convert_d(d)
indexList = []
for trace in traceMtvtDict:
    print(trace)
    l = traceMtvtDict[trace]
    for hr in l:
        (defaults, allcons) = find_default(dLookup, hr, hitRange)

        templ = []        
        for cons in allcons:
            (p, s) = cons
            templ.append(p*s, p, s)
        templ.sort()

        for default in defaults:
            bestCon = get_config(dLookup, default, hr, hitRange)
            index = templ.index(bestCon)
            print(bestCon, templ, templ.index)
            indexList.append(index)
print(indexList)
print(1.0*sum(indexList)/len(indexList))

