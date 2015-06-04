# AurOracle

This is a utility to generate valid ways to take the courses you must take and courses you would take.

## How it works

Give the utility the following:
* The total number of courses you wish to take.
* The term you wish to generate potential schedules for.
* The list of courses you MUST take.
* The list of courses you would take as electives to fill the remaining slots.

It will then generate potential course combinations.

### Usage Example
    auroracle.py -n 5 -term f15 -must MATH 1500 CHEM 1500 -would BIOL 3290 FREN 1152 COMP 1010
    
    ARGUMENTS GUIDE
    n       : Number of courses you are taking
    term    : The term in which you are taking them. (ex. fall15, winter16, summer16, fal16)
    must    : The courses you must take. Obviously shouldn't be larger than n.
    would   : The courses you would take as electives.
    offline : If this argument is provided, offline mode is enabled. See the source for more info.


## Disclaimer
Aurora/the university may or may not care about light web scraping from students. I have yet to hear back. As it stands now, I take no responsibility if you get into trouble using this utility.


## TODO
* Make "term" parameter easier
* Error handling
* Command line parameters
* Make the output create a monday list, tuesday list, etc.
* caching
* out to file