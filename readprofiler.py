#!/usr/bin/env python3
from pstats import Stats
from os.path import expanduser

def goCprofile(profFN):
    profFN = expanduser(profFN)
    p = Stats(profFN)

#p.strip_dirs() #strip path names

#p.sort_stats('cumulative').print_stats(10) #print 10 longest function
#p.print_stats()

    p.sort_stats('time','cumulative').print_stats(20)
