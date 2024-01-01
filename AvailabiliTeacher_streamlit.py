import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import csv
from collections import defaultdict
import random
import time

'''
# SST MeetSched
Previously AvailabiliTeacher
(Ver 3.3, dated 01 Jan 2024)
'''

st.markdown("This app is currently available for: :red[**Term 1 2024**] (Ver4/ 4.1)")

'''

This is a simple app to identify the common available periods across two or more teachers, based on their timetable. This may be useful to identify viable timings for meetings that are not reflected in the timetable, such as committee meetings.
'''
st.markdown(":blue[**Disclaimer:**]") 
st.markdown("* :blue[The identified common available periods are simply a first cut using the timetable. This app does not take into account ad hoc meetings or other commitments that teachers may have. After identifying the possible meeting times, please double-check with the teachers involved to confirm their availability.]")
st.markdown("* :blue[Public and school holidays are not taken into consideration when identifying common available periods. Please cross-check with a calendar to ensure your proposed meeting does not fall on a holiday.]")

'''
Made with :heart: by Jovita Tang

---

'''

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"],scopes = scope)

gc = gspread.authorize(credentials)
    
db = dict()

def open_db(filename):
    spread = gc.open(filename)
    worksheet = spread.worksheet("2024T1") #CHANGE THIS WHEN CHANGING TERM DATABASES!!!
    csvdb = worksheet.get_all_values()
    
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
    cols = []
    headers = []
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
                col = []
                headers.append(key)
                for time in current:
                    col.append("{} - {}".format(time[0],time[1]))
                cols.append(col)
                break

    longest = max([len(x) for x in cols])
    for col in cols:
        while len(col) < longest:
            col.append("")
        
    df = pd.DataFrame(zip(*cols), columns = headers)
    
    # style
    th_props = [
    ('font-size', '14px'),
    ('text-align', 'center'),
    ('font-weight', 'bold'),
    ('color', '#6d6d6d'),
    ('background-color', '#f7ffff')
    ]
                               
    td_props = [
    ('font-size', '14px')
    ]
                                 
    styles = [
    dict(selector="th", props=th_props),
    dict(selector="td", props=td_props)
    ]

    # table
    df2=df.style.set_properties().set_table_styles(styles)
    
    # CSS to inject contained in a string
    hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
    
    # Inject CSS with Markdown
    st.markdown(hide_table_row_index, unsafe_allow_html=True)
    
    # Display a static table
    st.table(df2)

teachers = gc.open('TeacherList')
worksheet = teachers.worksheet("Sheet1")
teachers_list = [x[0] for x in worksheet.get_all_values()]

meeting = []

'''
### Enter Teachers' Names

This is where you select the teachers whom you need to find a common timeslot with. Use the dropdown list, or start typing their name in the box and press 'Enter'. 

Don't forget to select yourself too!

'''

all_avail = dict()
meeting = st.multiselect("", teachers_list,key='multiselect')
st.write("Number of teachers selected:", len(meeting))

if st.button("Click me to generate common free periods!"):
    exp = 0
    while True:
        try:
            open_db('TeacherAvailDatabase_ODD')
            break
        except:
            if 2**exp > 120: 
                st.write("Sorry, we are having issues connecting to our database. Please try again later.")
                st.stop()
            else:
                st.write("Error connecting to database... We will try again in {} seconds...".format(2**exp))
                waittime = 2**exp + random.random()/100
                time.sleep(waittime)
                exp += 1
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

    '''
    ### Results
    '''

    if meeting == []:
        st.write("Select some teachers to see the common available timeslots!")
    else:
        st.write("***Odd Week***")
        time_converter(all_avail)
        exp = 0
        while True:
            try:
                open_db('TeacherAvailDatabase_EVEN')
                break
            except:
                if 2**exp > 120: 
                    st.write("Sorry, we are having issues connecting to our database. Please try again later.")
                    st.stop()
                else:
                    st.write("Error connecting to database... We will try again in {} seconds...".format(2**exp))
                    waittime = 2**exp + random.random()/100
                    time.sleep(waittime)
                    exp += 1

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

        st.write("\n\n")
        st.write("***Even Week***")
        time_converter(all_avail)
        st.write("\n\n")
    
'''
***Thank you for using AvailabiliTeacher!*** :smile:
'''
