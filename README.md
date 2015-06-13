<!---
********************************************************
                     NOTICE
This file is meant to be read with a markdown viewer.
Viewing it as a text file will likely be difficult and
confusing. Please visit the following link to view it
as intended:
https://github.com/shelt/AurOracle/blob/master/README.md
********************************************************
-->


# AurOracle

This is a course selection utility for Aurora. Tell it the courses you want to take, and it tells you the ways you can take them.

It generates course schedules that are free from [time conflicts](http://umanitoba.ca/student/records/registration/access/639.html) and that include courses you must take and courses you would take. It also attempts to determine which schedules are best and sort them accordingly.

I made this because I was sick of spending large amounts of time trying out potential combinations of sections of courses, only to encounter another conflict and be forced to move everything around.

**NOTE:** Schedules generated from this utility are no longer outputted to the command prompt, but rather directly to a text file. Generation can perform much faster when not printing every iteration.

## How it works

Give the utility the following:
* The total number of courses you wish to take.
* The term you wish to generate schedules for.
* The list of courses you are taking for sure.
* Optional: The list of courses you would take as electives to fill any remaining slots.

It will then generate potential course schedules, detailing which sections to take.

By default, it will attempt to "compress" schedules, reducing potential for courses hours apart. Other optimizations can be performed, such as preferring class-free days.

You can also limit a course to specific sections by including them in the course name (`MATH-1500-A01-A02`)

<p align="center"><img src="https://i.imgur.com/DLbHCkV.png" /></p>

## Usage

### Example
    auroracle.py --term fall15 --must COMP-1010 MATH-1500 GEOL-1420-A01 FREN-1152 --earliest "9:30 AM" --latest "3:30 PM"
    
### Arguments

Argument  | Function
---|---
`--number`  | Number of courses you are taking. Only required if the `--would` option is used.
`--term`    | The term in which you are taking them. (ex. fall15, winter16, summer16, fall16)
`--must`    | The courses you must take. Obviously shouldn't be larger than `--number` value.
`--would`   | The courses you would take as electives to fill the remaining spots (optional)
<span style="white-space: nowrap;">`--earliest`</span>| The earliest time you could stand being in class at. (Format: "10:00 PM") (optional)
`--latest`  | The latest time you could stand being in class at.   (Format: "10:00 PM") (optional)

#### Advanced options
Argument  | Function
---|---
<span style="white-space: nowrap;">`--offline`</span>| If this argument is provided, offline mode is enabled. The utility will then only grab data from aptly named HTML pages downloaded to the /cache directory. (ex: "MATH-1500.html")
`--file`    | Custom filename for the output file. (optional)
`--cap`     | Caps the generation count. If the utility is taking over 10 minutes, you may want to set the cap to 100K-200K.

#### Optimization options
Argument  | Function
---|---
`--prefer-free-days`  | Lists schedules offering the most class-free days first, if any exist.
`--no-compression`    | Do not sort schedules by least-time-between-courses.

    
*For course names you need to use a dash, such as MATH-1500, or quotes, such as "MATH 1500"*

An example of input and output can be seen in the [example-output.txt](example-output.txt) file.

## Installation
This utility uses **Python 2.7**.

### Install steps
* Download and run the Python 2.7 installer found [here](https://www.python.org/downloads/).
* Download a zip file of the utility from [here](https://github.com/shelt/AurOracle/archive/master.zip)
* Unzip to a directory.
* Open a command line in that directory, and run `auroracle.py` followed by the arguments you want.

## Benchmarking
Some combinations of courses yield more potential schedules than others. The following are benchmarks of the time it took the utility to generate a large amount of schedules (297590).
    
    auroracle.py -n 3 -t fall15 -m COMP-1010 MATH-1300 ARTS-1110

    x64 HP Pavillion laptop, 8GB RAM, 1.60 GHz (AMD a8-455M APU)
    Generation:   214s
    Optimization:  93s
    Writing:      142s
    TOTAL:        449s
    
    x64 desktop, 8GB RAM, 3.20 GHz (AMD Phenom II X6 1090T)
    Generation:    56s
    Optimization:  27s
    Writing:       38s
    TOTAL:        121s
    
    output file size: 356MB

## Disclaimer
Aurora/the university may or may not care about light web scraping from students. I have yet to hear back. As it stands now, I take no responsibility if you get into trouble using this utility.

Also note that because of the large amounts of time between when course schedules are typically made, the HTML structure on Aurora could potentially change, and this utility might break as a result.  Please feel free to email me at any time if the utility isn't working (sam@shelt.ca), or even submit a fix via a pull request.


## TODO
* Implement a cannot-attend-on-these-days feature.
* Have the script recognize when classes are full.
* Implement the ability to specify a single section (or range of sections) that you need to be in for a particular course.
* More user error handling
* Some departments (such as math) limit which lab you can take with which lecture section.
* Verify that course sections with multiple entries in meeting times (such as CS) are handled correctly
* Verify that other things in meeting times (such as finals) are handled correctly
