# .:: AurOracle ::.
# A utility to generate course schedules for University of Manitoba students.
#
# Written by Sam Shelton (sam@shelt.ca)

import time
import urllib2
import lib.ElementSoup as esoup
import itertools
import argparse
import re
from math import factorial

from lib.sorting import quicksort_sections
from lib.classes import Section,Course
"""     PARAMETERS
    n                : The number of courses wanted.
    term             : The term you wish to generate for.
    m_course_strings : Mandatory courses; courses that must be in your schedule.
    p_course_strings : Potential courses; courses you would be up for taking as electives.
    offline_mode     : Grab data from "Class Schedule Listing" HTML pages downloaded to the
                       /offline directory. Implemented because web scraping might be against
                       Aurora's TOS. NOTE: name of HTML file must be the same as the
                       coursename below.
"""
terms = {
"fall15":"201590",
"winter16":"201610",
"summer16":"201650",
"fall16":"201590",
"winter17":"201710",
"summer17":"201750"
}



#TODO multiple entries in meeting times?
"""
    Prints an iterable of sections.
"""
def print_section_comb(sections):
    sorted_sections = quicksort_sections(list(sections))
    print("-----------")
    for section in sorted_sections:
        print(section.root_course.name + " : " + section.name + "    " + time.strftime("%I:%M %p",section.start_time) + " - " + time.strftime("%I:%M %p",section.end_time) + "    " + section.day)

"""
    Retrieves the course from Aurora.
"""
def get_course(name, term, earliest, latest, offlinemode):
    name = name.upper()
    course = Course(name)
    subj,crse = name.split(" ")
    
    if offlinemode:
        html = esoup.parse("offline/" + name + ".html")
    else:
        url = "http://aurora.umanitoba.ca/banprod/bwckctlg.p_disp_listcrse?term_in="+term+"&subj_in="+subj+"&crse_in="+crse+"&schd_in=F02"
        
        request = urllib2.Request(url)
        request.add_header('User-Agent', "Mozilla/5.0 (X11; U; Linux i686) AppleWebKit/536.16 (KHTML, like Gecko) Chrome/35.0.2049.59 Safari/536.16")
        request.add_header('Referer', "https://aurora.umanitoba.ca/banprod/bwckctlg.p_disp_course_detail?cat_term_in="+term+"&subj_code_in="+subj+"&crse_numb_in=" + crse)
        response = urllib2.urlopen(request)
        html = esoup.parse(response)
    
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
        
        # Time
        
        section_time = tablenode.find("./td[2]").text
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
                course.lab = Course(course.name + "LAB")
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
    
    if len(p_courses) + len(m_courses) < number:
        print("The number of courses specified does not match the number desired.")
        exit()
    
    # This is just looping nCr times, so the length of p_combs.
    n = len(p_courses)
    r = number-len(m_courses)
    for i in range(factorial(n) // factorial(r) // factorial(n-r)):
        courselist = list(next(p_combs)) + m_courses
        for i in courselist:
            print(i.name)
        print('----')
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
                print_section_comb(section_comb)
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
    parser.add_argument('-e', '--earliest')
    parser.add_argument('-l', '--latest')
    args = parser.parse_args()
    
    if not args.must:
        args.must = []
    if not args.would:
        args.would = []
    args.must = [i.replace("-", " ") for i in args.must]
    args.would = [i.replace("-", " ") for i in args.would]
    
    # Convert termnames
    args.term = terms[args.term]
    
    # Earliest / latest
    if args.earliest:
        args.earliest = time.strptime(args.earliest, "%I:%M %p")
    if args.latest:
        args.latest = time.strptime(args.latest, "%I:%M %p")
    
    valid_combs = get_valid_combs(args.number, args.term, args.must, args.would, args.earliest, args.latest, args.offline)
    print("Completed.")
            
            
            
            
