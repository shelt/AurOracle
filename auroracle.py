# .:: AurOracle ::.
# A utility to generate course schedules for University of Manitoba students.
#
# Written by Sam Shelton (sam@shelt.ca)

import os
import time
import threading
import urllib2
import lxml.html as lh
import itertools
import argparse
import re
from math import factorial

from lib.sorting import quicksort_sections,get_sorted_daylists
from lib.sorting import compress,prefer_free
from lib.classes import Section,Course

DEBUG = False
MAX_GET_PER_SECOND = 1

terms = {
"fall15":"201590",
"winter16":"201610",
"summer16":"201650",
"fall16":"201590",
"winter17":"201710",
"summer17":"201750"
}

"""
    The function to print schedule data
    to the outfile. Debug and error messages
    instead use print().
"""
def print_write(text, verbose=False):
    print >> outfile, text
    
"""
    Print a combination of courses to the
    outfile as a calendar.
"""
def print_calendar(comb):
    print_write("*********************  CALENDAR  **********************")
    print_write("| MONDAY  || TUESDAY ||WEDNESDAY||THURSDAY || FRIDAY  |")
    
    # Create day lists (the columns of the calendar)
    day_lists = get_sorted_daylists(comb)
    
    # Convert to iterators
    day_iters = [iter(l) for l in day_lists]

    still_printing = True
    while still_printing:
        l1 = "" #line 1
        l2 = "" #line 2
        l3 = "" #line 3
        stops = 0 # number of times nothing was printed
        print_write("|---------||---------||---------||---------||---------|")
        for day_iter in day_iters:
            try:
                section = day_iter.next()
                l1day = section.root_course.name.ljust(9)
                l2day = section.name.center(9)
                l3day = time.strftime("%I:%M %p",section.start_time).center(9)
            except StopIteration:
                stops+=1
                l1day = "         "
                l2day = "         "
                l3day = "         "
            l1 += "|" + l1day + "|"
            l2 += "|" + l2day + "|"
            l3 += "|" + l3day + "|"
        if(stops == 5):
            still_printing = False
        if still_printing:
            print_write(l1)
            print_write(l2)
            print_write(l3)


"""
    DECORATOR: Prevents function func
    from being called more than max times
    per second.
    Used to rate limit get_course calls.
"""
def rate_limit(max):
    lock = threading.Lock()
    minInterval = 1.0 / float(max)
    def decorate(func):
        delta = [0.0]
        def rate_limited_function(args,*kargs):
            lock.acquire()
            elapsed = time.clock() - delta[0]
            remaining = minInterval - elapsed

            if remaining>0:
                time.sleep(remaining)

            lock.release()

            ret = func(args,*kargs)
            delta[0] = time.clock()
            return ret
        return rate_limited_function
    return decorate

"""
    Prints a combination of sections
    to the outfile.
"""
def print_section_comb(comb):
    print_write("**************  SCHEDULE  *******************")
    for section in comb:
        print_write(section.root_course.name + " : " + section.name + "    " + time.strftime("%I:%M %p",section.start_time) + " - " + time.strftime("%I:%M %p",section.end_time) + "    " + section.day)

"""
    Retrieves the course from Aurora.
"""
@rate_limit(MAX_GET_PER_SECOND)
def get_course(name, term, earliest, latest, offlinemode):
    name = name.upper() # Note that name could be "MATH-1500" or "MATH-1500-A05-A06" etc.
    name_parts = name.split(" ")
    subj = name_parts[0]
    crse = name_parts[1]
    course = Course(subj + " " + crse)

    
    specific_sections = []
    # Sections specified?
    for sec_i in range(2, len(name_parts)):
        specific_sections.append(name_parts[sec_i])
    
    # Retrieval
    if offlinemode:
        try:
            html = lh.parse("offline/" + subj + " " + crse + ".html")
        except IOError:
            html = lh.parse("offline/" + subj + "-" + crse + ".html")
    else:
        # Caching
        dpath = "cache/"+term+"/"
        fpath = dpath + subj+"-"+crse+".html"
        if os.path.exists(fpath):
            with open(fpath) as f:
                html = lh.parse(f)
        else:
            url = "http://aurora.umanitoba.ca/banprod/bwckctlg.p_disp_listcrse?term_in="+term+"&subj_in="+subj+"&crse_in="+crse+"&schd_in=F02"
            
            request = urllib2.Request(url)
            request.add_header('User-Agent', "Mozilla/5.0 (X11; U; Linux i686) AppleWebKit/536.16 (KHTML, like Gecko) Chrome/35.0.2049.59 Safari/536.16")
            request.add_header('Referer', "https://aurora.umanitoba.ca/banprod/bwckctlg.p_disp_course_detail?cat_term_in="+term+"&subj_code_in="+subj+"&crse_numb_in=" + crse)
            response = urllib2.urlopen(request)
            data = response.read()
            html =  lh.parse(response)
            
            # Add to cache
            if not os.path.exists(os.path.dirname(fpath)):
                os.makedirs(os.path.dirname(fpath))
            with open(fpath,'wb') as f:
                f.write(data)
            
    
    nodes = {}
    """
        "nodes" refers to the entries in the section table.
        The table looks like this:
        <tr><th><a>section title</a></th></tr>
        <tr><td><a>section body</td></tr>
        ...
        We find all title elements (tr/th/a) and
        associate their titles to the bodies (tr/td)
        (which are two levels up and one sibling down)
        using the nodes dict.
        
        The elements on Aurora don't use IDs, so it's safest
        to use the long summaries.
    """
    # Downloaded HTML files may have tbody elements inserted by the browser.
    if len(html.xpath(".//table[@summary='This layout table is used to present the sections found']/tr")) == 0:
        tbody = "tbody/"
    else:
        tbody = ""
    
    # NODE EXTRACTION
    titlenodes = html.xpath(".//table[@summary='This layout table is used to present the sections found']/"+tbody+"tr/th[@class='ddtitle']/a")
    
    for title_a in titlenodes:
        body_tr = title_a.getparent().getparent().getnext() # From tr/th/a to tr/ and the next tr is the body of the entry.
        tablenode = body_tr.xpath("./td/table[@summary='This table lists the scheduled meeting times and assigned instructors for this class..']/"+tbody+"tr[2]")[0]
        nodes[title_a.text] = tablenode
    
    for title,tablenode in nodes.items():
        # Section
        section_num = title[-3:]
        
        # Is a section specified?
        if len(specific_sections) > 0 and section_num not in specific_sections:
            continue
        
        # Only allow courses and labs
        if not (section_num[0] == "A" or section_num[0] == "B"):
            continue
        
        # Day
        section_day = tablenode.find("./td[3]").text
        if not section_day or ("TBD" in section_day) or ("TBA" in section_day):
            continue
        
        # Time
        section_time = tablenode.find("./td[2]").text
        if not section_time:
            continue
        times = re.split(" *- *", section_time)
        start_time = time.strptime(times[0], "%I:%M %p")
        end_time = time.strptime(times[1], "%I:%M %p")
        
        # Earliest / latest checking
        if (earliest and (start_time < earliest)) or (latest and (end_time > latest)):
            continue
        # It's a course
        if section_num[0] == "A":
            course.sections.append(Section(section_num, start_time, end_time, section_day, course))
            
        # It's a lab
        elif section_num[0] == "B":
            #create lab if not exists
            if not course.haslab:
                course.haslab = True
                course.lab = Course(course.name)
            course.lab.sections.append(Section(section_num, start_time, end_time, section_day, course))
    return course


    """
    MAIN FUNCTION
    """
def get_valid_combs(number, term_string, m_course_strings, p_course_strings, earliest, latest, offlinemode):
    valid_combs = []
    m_courses = []   # A list of all mandatory courses. All are included in each iteration below.
    p_courses = []   # A list of all potential courses. Used to fill up remaining spots, though all combinations are exausted.
    
    for coursename in m_course_strings:
        course = get_course(coursename, term_string, earliest, latest, offlinemode)
        m_courses.append(course)
    for coursename in p_course_strings:
        course = get_course(coursename, term_string, earliest, latest, offlinemode)
        p_courses.append(course)

    p_combs = itertools.combinations(p_courses, number-len(m_courses)) # set of tuples of possible ways to fill remaining spots
    
    # This is just looping nCr times, so the length of p_combs.
    n = len(p_courses)
    r = number-len(m_courses)
    
    for i in range(factorial(n) // factorial(r) // factorial(n-r)):
        courselist = list(next(p_combs)) + m_courses
        assert(number == len(courselist)) #debugging
        
        combs = generate_valid_combinations(courselist)               # (local) list of possible combinations of courses.
        for comb in combs:
            if len(comb) > 0:
                valid_combs.append(comb)
        
    return valid_combs


    """
    Given a list of courses, generates a list of each
    way to take each course (each section), and then
    generates the Cartesian product of all of those
    subsets. It iterates over the results and returns
    those that are valid.
    """
def generate_valid_combinations(courselist):
    
    valid_combs = []                                               # list of valid combinations

    s_lists = []                                                   # list of section lists of each course

    for course in courselist:
        s_lists.append(course.sections)
        # Lab?
        if (course.haslab):
            s_lists.append(course.lab.sections)
    
    
    section_combs = itertools.product(*s_lists)                     # set of tuples of ways to combine courses by section
    count = 0
    try:
        while True:
            section_comb = next(section_combs)
            if is_valid_combination(section_comb):
                valid_combs.append(section_comb)
            count += 1
            if args.cap and count >= args.cap:
                break
    except StopIteration:
        pass
    return valid_combs

"""
    Checks combinations for conflicts
"""
def is_valid_combination(sectionlist):

    for section in sectionlist:                                    # loop through each section in the combination
        for othersection in set(sectionlist) ^ set([section]):          # loop through all sections but this one
            if section.conflicts_with(othersection):
                return False
    return True
    

if __name__ == "__main__":
    # PARSING
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--number', type=int)
    parser.add_argument('-t', '--term')
    
    parser.add_argument('-f', '--file')
    
    parser.add_argument('-m', '--must', nargs='+')
    parser.add_argument('-w', '--would', nargs='+')
    
    parser.add_argument('-o', '--offline',  action='store_true')
    parser.add_argument('-v', '--verbose',  action='store_true')

    parser.add_argument('-e', '--earliest')
    parser.add_argument('-l', '--latest')
    
    parser.add_argument('-c', '--cap', type=int)
    
    # Optimization args
    parser.add_argument('--prefer-free-days', action='store_true')
    parser.add_argument('--no-compression', action='store_true')
    
    
    args = parser.parse_args()
    
    # Error checking
    if not args.number:
        print("You must specify a number of courses desired. \nExample: '--number 5'")
        exit()
    if not args.must and not args.would:
        print("You must specify at least one course.")
        exit()
    
    # Course parsing
    if not args.must:
        args.must = []
    if not args.would:
        args.would = []
    args.must = [i.replace("-", " ") for i in args.must]
    args.would = [i.replace("-", " ") for i in args.would]
    
        
    if (len(args.would) + len(args.must) < args.number or len(args.must) > args.number):
        print("The number of courses specified does not match the number desired.")
        exit()
    
    # Convert term names
    if not args.term:
        print("You must specify an academic term. \nExample: '--term winter16'")
        exit()
    args.term = terms[args.term]
    
    # Earliest / latest time parsing
    if args.earliest:
        args.earliest = time.strptime(args.earliest, "%I:%M %p")
    if args.latest:
        args.latest = time.strptime(args.latest, "%I:%M %p")
    
    # File out
    if args.file:
        args.file = args.file.replace(".txt","") + ".out.txt"
        if os.path.dirname(args.file) and not os.path.exists(os.path.dirname(args.file)):
            os.makedirs(os.path.dirname(args.file))
    else:
        # Construct name
        args.file = " ".join(args.must + args.would)
        args.file = args.term + "-" + args.file
        args.file = args.file[:250] + (args.file[250:] and '..')
        args.file = args.file.replace(" ","-") + ".out.txt"
    outfile = file(args.file, 'w')
    
    # Main call
    print("Generating schedules...")
    valid_combs = get_valid_combs(args.number, args.term, args.must, args.would, args.earliest, args.latest, args.offline)
    if len(valid_combs) == 0:
        print("No courses could be generated. Perhaps your request was too specific?")
        exit()
    
    
    # Pre-schedule output
    print_write("- Generated "+str(len(valid_combs))+" schedules.")
    
    # Optimization
    print("Optimizing...")
    if not args.no_compression:
        valid_combs = compress(valid_combs)
        print_write("- These schedules are sorted by most compression to least compression.")
    if args.prefer_free_days:
        valid_combs = prefer_free(valid_combs)
        print_write("- Schedules with free days are listed first. (--prefer-free-days)")
    # Schedule output
    print("Writing to file...")
    print_write("\n\n")
    for comb in valid_combs:
        print_section_comb(comb)
        print_write("\n")
        print_calendar(comb)
        print_write("\n\n\n\n\n")
    print("Completed. Outputted to \"" + args.file + "\"")
        
