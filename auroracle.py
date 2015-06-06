# .:: AurOracle ::.
# A utility to generate course schedules for University of Manitoba students.
#
# Written by Sam Shelton (sam@shelt.ca)

import os
import time
import urllib2
import lib.ElementSoup as esoup
import itertools
import argparse
import re
from math import factorial

from lib.sorting import quicksort_sections
from lib.classes import Section,Course

DEBUG = False

terms = {
"fall15":"201590",
"winter16":"201610",
"summer16":"201650",
"fall16":"201590",
"winter17":"201710",
"summer17":"201750"
}
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
    
    
    

"""
    A wrapper for print() adding
    verbosity checking and printing
    to file if specified.
"""
def print_out(text, verbose=False):
    if verbose and not args.verbose:
        return
        
    # Console out
    print(text)
    
    # File out
    if args.file and isinstance(args.file, file):
        print >> args.file, text
    

def print_calendar(comb):
    print_out("*********************  CALENDAR  **********************")
    print_out("| MONDAY  || TUESDAY ||WEDNESDAY||THURSDAY || FRIDAY  |")
    
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
        print_out("|---------||---------||---------||---------||---------|")
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
            print_out(l1)
            print_out(l2)
            print_out(l3)


"""
    Prints an iterable of sections.
"""
def print_section_comb(sections):
    print_out("**************  SCHEDULE  *******************")
    for section in sections:
        print_out(section.root_course.name + " : " + section.name + "    " + time.strftime("%I:%M %p",section.start_time) + " - " + time.strftime("%I:%M %p",section.end_time) + "    " + section.day)

"""
    Retrieves the course from Aurora.
"""
def get_course(name, term, earliest, latest, offlinemode):
    name = name.upper()
    course = Course(name)
    subj,crse = name.split(" ")
    
    if offlinemode:
        try:
            html = esoup.parse("offline/" + name + ".html")
        except IOError:
            html = esoup.parse("offline/" + subj + "-" + crse + ".html")
    else:
        # Caching
        dpath = "cache/"+term+"/"
        fpath = dpath + subj+"-"+crse+".html"
        if os.path.exists(fpath):
            print_out("! Fetching from cache: "+subj+"-"+crse , verbose=True)
            with open(fpath) as f:
                html = esoup.parse(f)
        else:
            print_out("! Fetching from Aurora: "+subj+"-"+crse , verbose=True)
            url = "http://aurora.umanitoba.ca/banprod/bwckctlg.p_disp_listcrse?term_in="+term+"&subj_in="+subj+"&crse_in="+crse+"&schd_in=F02"
            
            request = urllib2.Request(url)
            request.add_header('User-Agent', "Mozilla/5.0 (X11; U; Linux i686) AppleWebKit/536.16 (KHTML, like Gecko) Chrome/35.0.2049.59 Safari/536.16")
            request.add_header('Referer', "https://aurora.umanitoba.ca/banprod/bwckctlg.p_disp_course_detail?cat_term_in="+term+"&subj_code_in="+subj+"&crse_numb_in=" + crse)
            response = urllib2.urlopen(request)
            data = response.read()
            html = esoup.parse(data, rawmode=True)
            
            # Add to cache
            if not os.path.exists(os.path.dirname(fpath)):
                os.makedirs(os.path.dirname(fpath))
            with open(fpath,'wb') as f:
                f.write(data)
            
    
    nodes = {}
    # This loop builds a dict associating titles to section nodes.
    # This tedium is a direct result of (a) aurora's strange HTML and
    # (b) python's poor HTML parsing support.
    last_title = ""
    
    # Downloaded HTML files may use tbody elements from the browser.
    if len(html.findall(".//table[@summary='This layout table is used to present the sections found']/tr")) == 0:
        tbody_string = "tbody/"
    else:
        tbody_string = ""
    
    for node in html.iterfind(".//table[@summary='This layout table is used to present the sections found']/"+tbody_string+"tr"):
        title = node.find("./th/a")
        if title != None: # It's a title node
            last_title = title.text
        else:          # It's a section node
            nodes[last_title] = node.find("./td/table/"+tbody_string+"tr[2]")
    
    for title,tablenode in nodes.items():
        # Section
        section_num = title[-3:]
        
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

    
    if (len(p_courses) + len(m_courses) < number or len(m_courses) > number):
        print_out("The number of courses specified does not match the number desired.")
        exit()
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
    
    try:
        while True:
            section_comb = next(section_combs)
            if is_valid_combination(section_comb):
                valid_combs.append(section_comb)
                
                # Printing to console
                print_section_comb(section_comb)
                print_out("\n")
                print_calendar(section_comb)
                print_out("\n\n\n\n\n")
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
    parser.add_argument('-m', '--must', nargs='+')
    parser.add_argument('-w', '--would', nargs='+')
    parser.add_argument('-o', '--offline',  action='store_true')
    parser.add_argument('-v', '--verbose',  action='store_true')
    parser.add_argument('-f', '--file')
    parser.add_argument('-e', '--earliest')
    parser.add_argument('-l', '--latest')
    args = parser.parse_args()
    
    # Error checking
    if not args.number:
        print_out("You must specify a number of courses desired. \nExample: '--number 5'")
        exit()
    if not args.must and not args.would:
        print_out("You must specify at least one course.")
        exit()
    
    # Course parsing
    if not args.must:
        args.must = []
    if not args.would:
        args.would = []
    args.must = [i.replace("-", " ") for i in args.must]
    args.would = [i.replace("-", " ") for i in args.would]
    
    # Convert term names
    if not args.term:
        print_out("You must specify an academic term. \nExample: '--term winter16'")
        exit()
    args.term = terms[args.term]
    
    # Earliest / latest time parsing
    if args.earliest:
        args.earliest = time.strptime(args.earliest, "%I:%M %p")
    if args.latest:
        args.latest = time.strptime(args.latest, "%I:%M %p")
    
    # File out
    if args.file:
        if os.path.dirname(args.file) and not os.path.exists(os.path.dirname(args.file)):
            os.makedirs(os.path.dirname(args.file))
        args.file = file(args.file,'w')
    
    # Main call
    valid_combs = get_valid_combs(args.number, args.term, args.must, args.would, args.earliest, args.latest, args.offline)
    
    
    
    if len(valid_combs) == 0:
        print_out("No courses could be generated. Perhaps your request was too specific?")
    else:
        print_out("Generated "+str(len(valid_combs))+" schedules.")
            
