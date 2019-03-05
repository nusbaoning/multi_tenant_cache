# -*- coding: utf-8 -*-  
import random
import csv
import sys
from matplotlib import pyplot as plt
from matplotlib import cm
from matplotlib import axes
from matplotlib.font_manager import FontProperties
font = FontProperties(fname='/Library/Fonts/Songti.ttc')
# https://baijiahao.baidu.com/s?id=1608586625622704613&wfr=spider&for=pc
# https://www.cnblogs.com/altlb/p/7160191.html
csvfile = open('mtvt_data.csv', 'rb')
reader = csv.reader(csvfile, delimiter=',')
pList = []
sList = [] 
for row in reader:
    print row
    p = float(row[0])
    s = float(row[1])
    pList.append(p)
    sList.append(s)
csvfile.close()

trace = "probuild"
plt.plot(pList, sList, marker='*')
plt.xticks(rotation=45)
plt.xlabel('p')
plt.ylabel('size rate')
plt.title('Motivation')
# plt.show()
plt.savefig(trace + '_mtvt.png', dpi=300)
# sys.exit(-1)