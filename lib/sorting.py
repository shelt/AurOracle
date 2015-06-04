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

