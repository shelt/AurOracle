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
import ssl

from modules.sorting import quicksort_sections,get_sorted_daylists
from modules.sorting import compress,prefer_free
from modules.classes import Section,Course

RATE_LIMIT = 1 # Max calls to get_course (and web requests) per second

terms = {
"fall15":"201590",
"winter16":"201610",
"summer16":"201650",
"fall16":"201690",
"winter17":"201710",
"summer17":"201750"
"fall17":"201690",
"winter18":"201710",
"summer18":"201750"
}

# Create bypass context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

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
@rate_limit(RATE_LIMIT)
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
    dpath = "cache/"+term+"/"
    fpath = dpath + subj+"-"+crse+".html"
    # Is it cached?
    if os.path.exists(fpath):
        html = lh.parse(fpath)
        root = html.getroot()
    elif not offlinemode:
        url = "https://aurora.umanitoba.ca/banprod/bwckctlg.p_disp_listcrse?term_in="+term+"&subj_in="+subj+"&crse_in="+crse+"&schd_in=F02"
        request = urllib2.Request(url)
        #request.add_header('User-Agent', "Mozilla/5.0 (X11; U; Linux i686) AppleWebKit/536.16 (KHTML, like Gecko) Chrome/35.0.2049.59 Safari/536.16")
        #request.add_header('Referer', "https://aurora.umanitoba.ca/banprod/bwckctlg.p_disp_course_detail?cat_term_in="+term+"&subj_code_in="+subj+"&crse_numb_in=" + crse)
        response = urllib2.urlopen(request, timeout=30, context=ctx)
        html = lh.parse(response)
        
        root = html.getroot()
        if root is None:
            print("Fatal error: failed to retrieve data for course "+name)
            exit()
        
        # Add to cache
        data = lh.tostring(root)
        if not os.path.exists(os.path.dirname(fpath)):
            os.makedirs(os.path.dirname(fpath))
        with open(fpath,'wb') as f:
            f.write(data)
    else:
        print("Offline mode failed: Course " + name + " not found in /cache.")
        exit()
            
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
    if len(root.xpath(".//table[@summary='This layout table is used to present the sections found']/tr")) == 0:
        tbody = "tbody/"
    else:
        tbody = ""
    
    # NODE EXTRACTION
    titlenodes = root.xpath(".//table[@summary='This layout table is used to present the sections found']/"+tbody+"tr/th[@class='ddtitle']/a")
    
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
            
        # Check for exclusion
        if args.xclude and (course.name + " " + section_num) in args.xclude:
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

def runwizard():
    # args.term
    print("Which term do you want to generate schedules for? (example: fall15)")
    while args.term == None:
        try:
            i = raw_input("> ").lower().replace(" ", "")
            if i not in terms.keys():
                raise ValueError
            args.term = i
        except ValueError:
            print("Not a valid option.")
            
    # args.number
    print("How many courses are you taking for this term? (example: 3)")
    while args.number == None:
        try:
            i = int(raw_input("> "))
            if i == 0:
                raise ValueError
            args.number = i
        except ValueError:
            print("Not a valid number.")
    
    # args.must
    print("List the courses you know you must take, separated by spaces. (example: MATH-1300 COMP-1010)")
    while args.must == None:
        i = raw_input("> ").split(" ")
        if not i or len(i) <= args.number:
            args.must = i
        else:
            print("Number of courses provided does not match number specified.")
    
    # args.would
    if len(args.must) < args.number:
        print("List any amount of courses that you'd take to fill the remaining "+str(args.number - len(args.must))+" slots. (example: GEOL-1420 FREN-1152)")
        while args.would == None:
            i = raw_input("> ").split(" ")
            if (len(i) + len(args.must)) >= args.number:
                args.would = i
            else:
                print("You need at least enough to fill the remaining slots.")
    
    # args.earliest
    print("What is the earliest you want to be in class? If you don't care, just leave it blank. (format: 8:30 AM)")
    i = raw_input("> ")
    if i:
        args.earliest = i
        
    # args.latest
    print("What is the latest you want to be in class? If you don't care, just leave it blank. (format: 3:30 PM)")
    i = raw_input("> ")
    if i:
        args.latest = i
    

if __name__ == "__main__":
    # PARSING
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--number', type=int)
    parser.add_argument('-t', '--term')
    
    parser.add_argument('-f', '--file')
    
    parser.add_argument('-m', '--must', nargs='+')
    parser.add_argument('-w', '--would', nargs='+')
    parser.add_argument('-x', '--xclude', nargs='+')
    
    parser.add_argument('-o', '--offline',  action='store_true')
    parser.add_argument('-v', '--verbose',  action='store_true')

    parser.add_argument('-e', '--earliest')
    parser.add_argument('-l', '--latest')
    
    parser.add_argument('-c', '--cap', type=int)
    
    # Optimization args
    parser.add_argument('--prefer-free-days', action='store_true')
    parser.add_argument('--no-compression', action='store_true')
    
    
    args = parser.parse_args()
    
    # Wizard
    if not any(vars(args).values()):
        runwizard()
    
    if not args.must and not args.would:
        print("You must specify at least one course.")
        exit()
    
    # Error checking
    if not args.number:
        if args.would:
            print("Because you used the --would parameter, you must specify a number of courses desired. \nExample: '--number 5'")
            exit()
        else:
            args.number = len(args.must)
    
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
        
    # Exclusion parsing
    if args.xclude:
        args.xclude = [i.replace("-", " ") for i in args.xclude]
    
    # Convert term names
    if not args.term:
        print("You must specify an academic term. \nExample: '--term winter16'")
        exit()
    args.term = args.term.lower()
    if args.term not in terms:
        print("Invalid academic term. \nExample: '--term winter16'")
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
        
