import streamlit as st

"""
# AvailabiliTeacher
(Ver 2.1, dated 4 Jan 2023)

A simple app to identify the common available periods across two or more teachers, based on their timetable. This may be useful to identify viable timings for meetings that are not reflected in the timetable, such as committee meetings.

This app is currently available for: **Term 1 2023**
"""
st.markdown(":blue[**Disclaimer:** The identified common periods do not take into account ad hoc meetings or other commitments that teachers may have. After identifying possible meeting times, it is advisable to double-check with the teachers involved to confirm their availability.]")

"""
Made with :heart: by Jovita Tang, Jan 2023

"""

import csv
from collections import defaultdict
    
db = dict()

def open_db(filename):
    file = open(filename)
    csvdb = csv.reader(file)
    db['Monday'] = defaultdict()
    db['Tuesday'] = defaultdict()
    db['Wednesday'] = defaultdict()
    db['Thursday'] = defaultdict()
    db['Friday'] = defaultdict()
    for row in csvdb:
        temprow = row[2:]
        while "" in temprow:
            temprow.remove("")
        if row[0] == "":
            break
        db[row[0]][int(row[1])] = temprow
        
def availableper(teacher):
    teachfree = dict()
    for day in db.keys():
        teachfree[day] = []
        for per in db[day].keys():
            if teacher in db[day][per]:
                teachfree[day].append(per)
    return teachfree

def time_converter(all_avail):
    cols = st.columns(5)
    count = 0
    all_avail_times = {}
    for key in all_avail.keys():
        timings = {
        1: ['8:00', '8:20'],
        2: ['8:20', '8:40'],
        3: ['8:40', '9:00'],
        4: ['9:00', '9:20'],
        5: ['9:20', '9:40'],
        6: ['9:40', '10:00'],
        7: ['10:00', '10:20'],
        8: ['10:20', '10:40'],
        9: ['10:40', '11:00'],
        10: ['11:00', '11:20'],
        11: ['11:20', '11:40'],
        12: ['11:40', '12:00'],
        13: ['12:00', '12:20'],
        14: ['12:20', '12:40'],
        15: ['12:40', '13:00'],
        16: ['13:00', '13:20'],
        17: ['13:20', '13:40'],
        18: ['13:40', '14:00'],
        19: ['14:00', '14:20'],
        20: ['14:20', '14:40'],
        21: ['14:40', '15:00'],
        22: ['15:00', '15:20'],
        23: ['15:20', '15:40'],
        24: ['15:40', '16:00'],
        25: ['16:00', '16:20'],
        26: ['16:20', '16:40'],
        27: ['16:40', '17:00'],
        28: ['17:00', '17:20'],
        29: ['17:20', '17:40'],
        30: ['17:40', '18:00'],
        31: ['18:00', '18:20']}
        all_avail_times[key] = []
        for period in all_avail[key]:
            all_avail_times[key].append(timings[int(period)])
        i = 0
        while True:
            current = all_avail_times[key]
            while i < len(current)-1 and current[i][1] == current[i+1][0]:
                current[i][1] = current[i+1][1]
                current.remove(current[i+1])
            i += 1
            if i >= len(current)-1:
                all_avail_times[key] = current
                with cols[count]:
                    st.write("**"+key+"**")
                    for time in current:
                        st.write("{} - {}".format(time[0],time[1]))
                count += 1
                break

with open('TeacherList.txt','r') as f:
    teachers_list = [line.rstrip() for line in f]

meeting = []

open_db('2023T1ODD.csv')

'''
### Enter Teachers' Names

This is where you select the teachers whom you need to find a common timeslot with. Don't forget to select yourself too!
'''

all_avail = dict()
meeting = st.multiselect("Please select the teachers' names, or start typing their name and press 'Enter' to select:", teachers_list)
st.write("You selected:", meeting)

for teach in meeting:
    x = availableper(teach)
    for key in x.keys():
        if key not in all_avail.keys():
            all_avail[key] = x[key]
        else:
            vals = all_avail[key].copy()
            for val in vals:
                if val not in x[key]:
                    all_avail[key].remove(val)    

st.write()
'''
### Results
'''

if meeting == []:
    st.write("Select some teachers to see the common available timeslots!")
else:
    st.write("***Odd Week***")
    time_converter(all_avail)
    st.write("\n")

    open_db('2023T1EVEN.csv')

    all_avail = dict()
    for teach in meeting:
        x = availableper(teach)
        for key in x.keys():
            if key not in all_avail.keys():
                all_avail[key] = x[key]
            else:
                vals = all_avail[key].copy()
                for val in vals:
                    if val not in x[key]:
                        all_avail[key].remove(val)

    st.write("\n\n\n")
    st.write("***Even Week***")
    time_converter(all_avail)
    st.write("\n")

'''
### Thank you for using AvailabiliTeacher! :smile:
'''
