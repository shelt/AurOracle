# .:: AurOracle ::.
# A utility to generate course schedules for University of Manitoba students.
#
# Written by Sam Shelton (sam@shelt.ca)

import time
import urllib
import lib.ElementSoup as esoup
import itertools
import argparse

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
def get_course(name, term, offlinemode):
    name = name.upper()
    course = Course(name)
    subj,crse = name.split(" ")
    
    if offlinemode:
        html = esoup.parse("offline/" + name + ".html")
    else:
        url = "https://aurora.umanitoba.ca/banprod/bwckctlg.p_disp_listcrse?term_in="+term+"&subj_in="+subj+"&crse_in="+crse+"&schd_in=F02"
        html = esoup.parse(urllib.urlopen(url))
        
    
    nodes = {}
    # This loop builds a dict associating titles to section nodes.
    # This tedium is a direct result of (a) aurora's strange HTML and
    # (b) python's poor HTML parsing support.
    last_title = ""
    for i,node in enumerate(html.iterfind(".//table[@summary='This layout table is used to present the sections found']/tbody/tr")):
        title = node.find("./th/a")
        if title != None: # It's a title node
            last_title = title.text
        else:          # It's a section node
            nodes[last_title] = node.find("./td/table/tbody/tr[2]")
    
    for title,tablenode in nodes.items():
        section_num = title[-3:]
        
        section_time = tablenode.find("./td[2]").text
        section_day = tablenode.find("./td[3]").text
        if section_num[0] == "A":
            course.sections.append(Section(section_num, section_time, section_day, course))
        elif section_num[0] == "B":
            #create lab if not exists
            if not course.haslab:
                course.haslab = True
                course.lab = Course(course.name + "LAB")
            course.lab.sections.append(Section(section_num, section_time, section_day, course))
    
   #debug print("SIZE: " + str(len(course.sections)))
    return course


    """
    MAIN FUNCTION
    """
def get_valid_combs(number, term_string, m_course_strings, p_course_strings, offlinemode):
    valid_combs = []
    m_courses = []
    p_courses = []
    
    for coursename in m_course_strings:
        course = get_course(coursename, term_string, offlinemode)
        if course != None:
            m_courses.append(course)
    for coursename in p_course_strings:
        course = get_course(coursename, term_string, offlinemode)
        if course != None:
            p_courses.append(course)
        
                
    p_combs = itertools.combinations(p_courses, number-len(m_courses)) # set of tuples of possible ways to fill remaining spots
    for p_comb in p_combs:                                             # for each way to combine the potential courses
        courselist = list(p_comb) + m_courses                           # set of n courses to take
        assert(number == len(courselist)) #debugging
        
        combs = generate_valid_combinations(courselist)               # (local) list of possible combinations of courses.
        for comb in combs:
            if len(comb) > 0:
                valid_combs.append(valid_comb)
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
    args = parser.parse_args()
    
    args.must = [i.replace("-", " ") for i in args.must]
    args.would = [i.replace("-", " ") for i in args.would]
    
    # Convert termnames
    args.term = terms[args.term]
    
    valid_combs = get_valid_combs(args.number, args.term, args.must, args.would, args.offline)
    print("Completed.")
            
            
            
            
