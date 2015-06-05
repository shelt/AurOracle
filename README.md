# AurOracle

This is a course selection utility for Aurora. Tell it the courses you want to take, and it tells you the ways you can take them.

It generates course schedules that are free from [time conflicts](http://umanitoba.ca/student/records/registration/access/639.html) and that include courses you must take and courses you would take.

I made this because I was sick of spending large amounts of time trying out potential combinations of sections of courses, only to encounter another conflict and be forced to move everything around.

## How it works

Give the utility the following:
* The total number of courses you wish to take.
* The term you wish to generate potential schedules for.
* The list of courses you MUST take.
* OPTIONAL: The list of courses you would take as electives to fill any remaining slots.
* OPTIONAL: The earliest time you could stand being in class.
* OPTIONAL: The latest time you could stand being in class.

It will then generate potential course schedules, detailing which sections to take.

<div style="text-align:center"><img src="https://i.imgur.com/gSgYQQW.png" /></div>

## Usage

### Example
    auroracle.py --number 3 --term fall15 --must MATH-1500 --would BIOL-3290 FREN-1152 COMP-1010
    
### Arguments

Argument  | Function
---|---
`--number`  | Number of courses you are taking
`--term`    | The term in which you are taking them. (ex. fall15, winter16, summer16, fal16)
`--must`    | The courses you must take. Obviously shouldn't be larger than `--number` value.
`--would`   | The courses you would take as electives to fill the remaining spots (optional)
`--earliest`| The earliest time you could stand being in class at. (Format: "10:00 PM") (optional)
`--latest`  | The latest time you could stand being in class at.   (Format: "10:00 PM") (optional)
`--offline` | If this argument is provided, offline mode is enabled. The utility will then only grab data from "Class Schedule Listing" HTML pages downloaded to the /offline directory. See [/offline/about.txt](offline/about.txt) for more info.
`--file`    | The file in which to write all output. (optional)
    
*For course names you need to use a dash, such as MATH-1500, or quotes, such as "MATH 1500"*



An example of input and output can be seen in the [example-output.txt](example-output.txt) file. Eventually the output will be viewable as a day-by-day schedule, perhaps if I make a web GUI for this utility.

## Installation
This utility uses **Python 2.7**.

### Install steps
* Download and run the Python 2.7 installer found [here](https://www.python.org/downloads/).
* Download a zip file of the utility from [here](https://github.com/shelt/AurOracle/archive/master.zip)
* Unzip to a directory.
* Open a command line in that directory, and run `auroracle.py` followed by the arguments you want.

## Disclaimer
Aurora/the university may or may not care about light web scraping from students. I have yet to hear back. As it stands now, I take no responsibility if you get into trouble using this utility.

Also note that because of the large amounts of time between when course schedules are typically made, the HTML structure on Aurora could potentially change, and this utility might break as a result.  Please feel free to email me at any time if the utility isn't working (sam@shelt.ca), or even submit a fix via a pull request.


## TODO
* Implement a cannot-attend-on-these-days feature.
* Have the script recognize when classes are full.
* Implement the ability to specify a single section (or range of sections) that you need to be in for a particular course.
* More user error handling
* out to file
* Some departments (such as math) limit which lab you can take with which lecture section.
* Verify that course sections with multiple entries in meeting times (such as CS) are handled correctly
* Verify that other things in meeting times (such as finals) are handled correctly
