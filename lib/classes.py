import re,time

class Course:

    def __init__(self, name, haslab=False):
        self.name = name
        self.sections = []
        
        self.haslab = haslab
        if haslab:
            self.lab = Course(name + "LAB")
    
    
    
    
class Section:
    # time_string should be like: 3:30 pm - 3:50
    # day should be a string of one of [M T W R F MWF TR]
    
    

    def __init__(self, name, time_string, day, root_course=None):
        
        self.name = name
        self.day = day
        
        times = re.split(" *- *", time_string)
        self.start_time = times[0]
        self.start_time = time.strptime(times[0], "%I:%M %p")
        self.end_time = time.strptime(times[1], "%I:%M %p")
        
        self.root_course = root_course #** In practice, this is set later
    
    """
        If they are on the same day,
        and if one range is neither completely after the other,
        nor completely before the other, then they must overlap.
        same_day and (StartA <= EndB) and (EndA >= StartB)
    """
    def conflicts_with(self,other):
        same_day = False
        for letter in self.day:
            if letter in other.day:
                same_day = True
        return same_day and (self.start_time <= other.end_time) and (self.end_time >= other.start_time)
