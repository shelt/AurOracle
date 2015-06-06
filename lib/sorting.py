"""
    Convert a combination of
    sections to a list containing
    5 sorted lists of MTWRF
"""
def get_sorted_daylists(comb):
    mon_sections = []
    tues_sections = []
    wed_sections = []
    thurs_sections = []
    fri_sections = []
    for section in comb:
        if "M" in section.day:
            mon_sections.append(section)
        if "T" in section.day:
            tues_sections.append(section)
        if "W" in section.day:
            wed_sections.append(section)
        if "R" in section.day:
            thurs_sections.append(section)
        if "F" in section.day:
            fri_sections.append(section)
    
    # Sort
    return [quicksort_sections(l) for l in [mon_sections,tues_sections,wed_sections,thurs_sections,fri_sections]]



###############
## QUICKSORT ##
###############

"""
    Quicksorts a list of sections by
    their start times.
"""
def quicksort_sections(olist):
    nlist = list(olist)
    return quickSortHelper(nlist,0,len(nlist)-1)
    
    

def quickSortHelper(nlist,first,last):
    if first<last:

        splitpoint = partition(nlist,first,last)

        quickSortHelper(nlist,first,splitpoint-1)
        quickSortHelper(nlist,splitpoint+1,last)
    
    return nlist

    
def partition(nlist,first,last):
    pivot = nlist[first]

    leftmark = first+1
    rightmark = last

    done = False
    while not done:

        while leftmark <= rightmark and  nlist[leftmark].start_time <= pivot.start_time:
            leftmark = leftmark + 1

        while nlist[rightmark].start_time >= pivot.start_time and rightmark >= leftmark:
            rightmark = rightmark -1

        if rightmark < leftmark:
            done = True
        else:
            temp = nlist[leftmark]
            nlist[leftmark] = nlist[rightmark]
            nlist[rightmark] = temp

    temp = nlist[first]
    nlist[first] = nlist[rightmark]
    nlist[rightmark] = temp


    return rightmark


##################
## OPTIMIZATION ##
##################
"""
    Sorts the section combinations by average distance
    between sections in ascending order. I.e., the
    most "squished" sections are at the bottom.
"""
def squish(combs):
    comb_avgs = {}   # (Combination of sections) : (avg time between sections)
    for comb in combs:
        daylist = get_sorted_daylist(comb)
        
        tdiff = 0 # Total difference between course starts and ends
        count = 0 # Total differences (total sections - 1)
        
        for day in daylists:
            day.reverse()
            day = iter(day)
            
            x1 = day.next()
            try:
                while True:
                    x2 = day.next()
                    tdiff = (time.mktime(x2.start_time) - time.mktime(x1.end_time)) / 60
                    count += 1
                    x1 = x2
            except StopIteration:
                pass
        comb_avgs[comb] = tdiff / count
        
    return sorted(comb_avgs.iteritems(), key=lambda (k,v): (v,k)).keys()
