import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import csv
from collections import defaultdict
import random
import time

st.sidebar.page_link("Meetable.py", label="Meetable")
st.sidebar.page_link("pages/Lesson Swap Helper.py", label="Lesson Swap Helper")

st.title("Lesson Swap Helper (LSH)")

st.markdown("This app is currently available for: :red[**Term 3-4 2026**] (Ver2.1, 10 July 2026)")

'''

The Lesson Swap Helper (LSH) is designed to help you narrow down potential lesson swaps for those times when you are scheduled to be out of school (e.g. on course). While it is unable to propose swaps for you, it can identify teachers who are available during your lesson time and teach the same class you are trying to swap away. It can also list the other teachers who teach the class, if you are able to propose a 3-way swap with them.
'''
st.markdown(":blue[**Disclaimer:**]") 
st.markdown("* :blue[The identified available teachers are simply a first cut using the timetable. This app does not take into account ad hoc meetings or other commitments that teachers may have. After identifying the possible meeting times, please double-check with the teachers involved to confirm their availability.]")

'''
Made with :heart: by Jovita Tang

---

'''

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"],scopes = scope)

gc = gspread.authorize(credentials)

teachertt = "2026T3TeacherTT" #CHANGE THIS WHEN CHANGING TERM DATABASES!!!
    
db = dict()

def open_db(filename):
    spread = gc.open(filename)
    worksheet = spread.worksheet("2026T3-4") #CHANGE THIS WHEN CHANGING TERM DATABASES!!!
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

def open_class_db(filename):
    spread = gc.open(filename)
    worksheet = spread.worksheet("Class Allocation") #CHANGE THIS WHEN CHANGING TERM DATABASES!!!
    csvdb = worksheet.get_all_values()
    teacherdb = {}
    for row in csvdb:
        temprow = row[1:]
        while "" in temprow:
            temprow.remove("")
        if row[0] == "":
            break
        teacherdb[row[0]] = temprow
    return teacherdb
    
def availableper(teacher):
    teachfree = dict()
    for day in db.keys():
        teachfree[day] = []
        for per in db[day].keys():
            if teacher in db[day][per]:
                teachfree[day].append(per)
    return teachfree

def sublist(lst1, lst2):
    for e in lst1:
        if e not in lst2:
            return False
    return True
    
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

# ============================================================
# LOAD TIMETABLE FROM GOOGLE SHEETS
# ============================================================

@st.cache_data(ttl=300)

def load_timetable(spreadsheet_name):

    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ],
    )

    gc = gspread.authorize(credentials)

    # Open Google Sheet by filename/title
    spreadsheet = gc.open(spreadsheet_name)

    timetable = {}

    required_columns = {
        "Week",
        "Day",
        "Start Time",
        "End Time",
        "Periods",
        "Class(es)",
        "Subject",
        "Co-teacher(s)"
    }

    for worksheet in spreadsheet.worksheets():

        teacher = worksheet.title

        values = worksheet.get_all_values()

        # Headers are on Row 3
        if len(values) < 3:
            continue

        headers = [
            str(header).strip()
            for header in values[2]
        ]

        # Data starts from Row 4
        data = values[3:]

        df = pd.DataFrame(
            data,
            columns=headers
        )

        missing = required_columns - set(df.columns)

        if missing:
            continue

        # Remove completely empty rows
        df = df[
            ~df.apply(
                lambda row:
                all(
                    str(value).strip() == ""
                    for value in row
                ),
                axis=1
            )
        ].copy()

        # ====================================================
        # COMBINE WEEK + DAY
        #
        # Odd + Tuesday -> Odd Tuesday
        # ====================================================

        df["Day"] = (
            df["Week"].astype(str).str.strip()
            + " "
            + df["Day"].astype(str).str.strip()
        )

        # We no longer need the separate Week column
        df.drop(
            columns=["Week"],
            inplace=True
        )

        # ====================================================
        # CONVERT DATA TYPES
        # ====================================================

        df["Start Time"] = df["Start Time"].apply(to_time)
        df["End Time"] = df["End Time"].apply(to_time)

        df["Periods"] = pd.to_numeric(
            df["Periods"],
            errors="coerce"
        )

        timetable[teacher] = df

    return timetable

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def to_time(value):
    """Convert Google Sheet/string/pandas time values to datetime.time."""

    if pd.isna(value):
        return None

    if isinstance(value, time):
        return value

    if isinstance(value, datetime):
        return value.time()

    if hasattr(value, "time"):
        try:
            return value.time()
        except Exception:
            pass

    value = str(value).strip()

    if not value:
        return None

    return pd.to_datetime(value).time()


def normalise(value):
    """Normalise text for comparison."""
    return str(value).strip().lower()


def times_overlap(start1, end1, start2, end2):
    """
    Return True if two time ranges overlap.

    Examples:
        09:00-10:00 and 09:40-10:40 -> True
        09:00-10:00 and 10:00-11:00 -> False
    """
    return start1 < end2 and start2 < end1


def split_classes(value):
    """
    Convert Class(es) into a set.

    Supports:
        S4-01
        S4-01, S4-02
        S4-01/S4-02
        S4-01; S4-02
    """

    if pd.isna(value):
        return set()

    value = str(value)

    value = value.replace("/", ",")
    value = value.replace(";", ",")

    return {
        item.strip()
        for item in value.split(",")
        if item.strip()
    }


def get_week(day):
    """
    Extract Odd/Even from combined Day.

    Examples:
        Odd Tuesday -> Odd
        Even Friday -> Even
    """

    return str(day).strip().split()[0]

# ============================================================
# FIND SPECIFIED LESSON
# ============================================================

def find_lesson(
    timetable,
    teacher,
    day,
    start,
    end
):
    """
    Find a lesson using:

        Teacher
        Day, e.g. Odd Tuesday
        Start Time
        End Time
    """

    df = timetable[teacher]

    matches = df[
        (df["Day"].apply(normalise) == normalise(day))
        &
        (df["Start Time"] == start)
        &
        (df["End Time"] == end)
    ]

    if matches.empty:
        return None

    return matches.iloc[0]

# ============================================================
# CHECK WHETHER TEACHER IS FREE
# ============================================================

def teacher_is_free(
    timetable,
    teacher,
    day,
    start,
    end
):
    """
    Return True if teacher has no lesson overlapping
    the specified time.
    """

    df = timetable[teacher]

    lessons = df[
        df["Day"].apply(normalise)
        == normalise(day)
    ]

    for _, lesson in lessons.iterrows():

        lesson_start = lesson["Start Time"]
        lesson_end = lesson["End Time"]

        if lesson_start is None or lesson_end is None:
            continue

        if times_overlap(
            start,
            end,
            lesson_start,
            lesson_end
        ):
            return False

    return True


# ============================================================
# FIND WHAT A TEACHER TEACHES
# ============================================================

def get_teacher_classes(df):
    """Return all classes taught by a teacher."""

    classes = set()

    for value in df["Class(es)"].dropna():
        classes.update(
            split_classes(value)
        )

    return classes


def get_teacher_subjects(df):
    """Return all subjects taught by a teacher."""

    return {
        normalise(value)
        for value in df["Subject"].dropna()
    }


# ============================================================
# FIND FREE TEACHERS
# ============================================================

def find_free_teachers(
    timetable,
    original_teacher,
    original_lesson,
    day,
    start,
    end
):
    """
    Find teachers who are free during the original lesson.

    Categorise into:

        1. Teach same class
        2. Teach same subject
        3. Others

    Same class takes priority over same subject.
    """

    original_classes = split_classes(
        original_lesson["Class(es)"]
    )

    original_subject = normalise(
        original_lesson["Subject"]
    )

    same_class = []
    same_subject = []
    others = []

    for teacher_name, df in timetable.items():

        # Don't include original teacher
        if teacher_name == original_teacher:
            continue

        # Teacher must be free
        if not teacher_is_free(
            timetable,
            teacher_name,
            day,
            start,
            end
        ):
            continue

        teacher_classes = get_teacher_classes(df)
        teacher_subjects = get_teacher_subjects(df)

        if original_classes & teacher_classes:

            same_class.append(
                teacher_name
            )

        elif original_subject in teacher_subjects:

            same_subject.append(
                teacher_name
            )

        else:

            others.append(
                teacher_name
            )

    return (
        sorted(same_class),
        sorted(same_subject),
        sorted(others)
    )


# ============================================================
# FIND POSSIBLE LESSON SWAPS
# ============================================================

def find_swaps(
    timetable,
    original_teacher,
    original_lesson,
    free_same_class_teachers
):
    """
    Find reciprocal lesson swaps.

    Candidate teacher must already be FREE during
    the original lesson.

    Their candidate lesson must:

        1. Be in the same Odd/Even week
        2. Be with the same class
        3. Have the same number of periods
        4. Occur when the original teacher is free
    """

    original_day = original_lesson["Day"]

    original_week = get_week(
        original_day
    )

    original_classes = split_classes(
        original_lesson["Class(es)"]
    )

    original_periods = original_lesson["Periods"]

    swaps = []

    for other_teacher in free_same_class_teachers:

        df = timetable[other_teacher]

        # ----------------------------------------------------
        # Only look at lessons in the same Odd/Even week
        # ----------------------------------------------------

        lessons = df[
            df["Day"].apply(get_week).apply(normalise)
            == normalise(original_week)
        ]

        for _, lesson in lessons.iterrows():

            lesson_classes = split_classes(
                lesson["Class(es)"]
            )

            common_classes = (
                original_classes
                & lesson_classes
            )

            # ------------------------------------------------
            # Must involve the same class
            # ------------------------------------------------

            if not common_classes:
                continue

            # ------------------------------------------------
            # Must have the same NUMBER OF PERIODS
            # ------------------------------------------------

            if lesson["Periods"] != original_periods:
                continue

            lesson_start = lesson["Start Time"]
            lesson_end = lesson["End Time"]

            if lesson_start is None or lesson_end is None:
                continue

            # ------------------------------------------------
            # Original teacher must be free during
            # the other teacher's lesson
            # ------------------------------------------------

            if not teacher_is_free(
                timetable,
                original_teacher,
                lesson["Day"],
                lesson_start,
                lesson_end
            ):
                continue

            # ------------------------------------------------
            # Valid reciprocal swap
            # ------------------------------------------------

            swaps.append({
                "Teacher": other_teacher,
                "Class": ", ".join(
                    sorted(common_classes)
                ),
                "Subject": lesson["Subject"],
                "Day": lesson["Day"],
                "Start Time": lesson_start,
                "End Time": lesson_end,
                "Periods": lesson["Periods"]
            })

    return swaps


# ============================================================
# MAIN STREAMLIT SWAP FUNCTION
# ============================================================

def show_lesson_swap_options(
    timetable,
    teacher,
    day,
    lesson_start,
    lesson_end
):
    """
    Display availability and swap options.

    Existing variables expected:

        teacher
            e.g. "Jovita Tang"

        day
            e.g. "Odd Tuesday"

        lesson_start
            e.g. 10:40

        lesson_end
            e.g. 11:40
    """

    lesson_start = to_time(
        lesson_start
    )

    lesson_end = to_time(
        lesson_end
    )

    # --------------------------------------------------------
    # Find original lesson
    # --------------------------------------------------------

    original_lesson = find_lesson(
        timetable,
        teacher,
        day,
        lesson_start,
        lesson_end
    )

    if original_lesson is None:

        st.warning(
            "Unable to find this lesson in the timetable."
        )

        return

    # --------------------------------------------------------
    # Find teachers who are free
    # --------------------------------------------------------

    same_class, same_subject, others = (
        find_free_teachers(
            timetable,
            teacher,
            original_lesson,
            day,
            lesson_start,
            lesson_end
        )
    )

    # --------------------------------------------------------
    # Find reciprocal swaps
    # --------------------------------------------------------

    swaps = find_swaps(
        timetable,
        teacher,
        original_lesson,
        same_class
    )

    # ========================================================
    # DISPLAY
    # ========================================================

    st.subheader(
        "Lesson Swap Options"
    )

    st.markdown(
        f"**{original_lesson['Class(es)']} — "
        f"{original_lesson['Subject']}**"
    )

    st.write(
        f"{day}, "
        f"{lesson_start.strftime('%H:%M')}–"
        f"{lesson_end.strftime('%H:%M')} "
        f"({int(original_lesson['Periods'])} periods)"
    )

    # --------------------------------------------------------
    # Possible reciprocal swaps
    # --------------------------------------------------------

    st.markdown(
        "#### Possible reciprocal swaps"
    )

    if swaps:

        for swap in swaps:

            st.success(
                f"**{swap['Teacher']}** — "
                f"{swap['Subject']} with "
                f"{swap['Class']}  \n"
                f"{swap['Day']}, "
                f"{swap['Start Time'].strftime('%H:%M')}–"
                f"{swap['End Time'].strftime('%H:%M')} "
                f"({int(swap['Periods'])} periods)"
            )

    else:

        st.info(
            "No reciprocal lesson swaps were found."
        )

    # --------------------------------------------------------
    # Available teachers
    # --------------------------------------------------------

    with st.expander(
        "Other teachers who are free"
    ):

        st.markdown(
            "**Teach the same class**"
        )

        if same_class:
            st.write(
                ", ".join(same_class)
            )
        else:
            st.write("None")

        st.markdown(
            "**Teach the same subject**"
        )

        if same_subject:
            st.write(
                ", ".join(same_subject)
            )
        else:
            st.write("None")

        st.markdown(
            "**Other teachers**"
        )

        if others:
            st.write(
                ", ".join(others)
            )
        else:
            st.write("None")

def table_display(lst):
    cols = []
    length = int(len(lst)/2 + 0.5)
    col1 = lst[:length]
    col2 = lst[length:]
    if length%2 == 1: col2.append("")
    cols = [col1, col2]
        
    df = pd.DataFrame(zip(*cols), columns = None)
    
    # style
    th_props = [
    ('font-size', '14px'),
    ('text-align', 'center'),
    ('font-weight', 'bold'),
    ('color', '#ffffff'),
    ('background-color', '#ffffff')
    ]
                               
    td_props = [
    ('font-size', '14px')
    ]
                                 
    styles = [
    dict(selector="th", props=th_props),
    dict(selector="td", props=td_props)
    ]

    # table
    df2 = df.style.set_properties().set_table_styles(styles)
    df2 = df.style
    
    # CSS to inject contained in a string
    hide_table_rowcol_index = """
            <style>
            thead th {display:none}
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """
    
    # Inject CSS with Markdown
    st.markdown(hide_table_rowcol_index, unsafe_allow_html=True)

    # Display a static table
    st.table(df2)

teachers = gc.open('TeacherList')
worksheet = teachers.worksheet("Sheet1")
teachers_list = [x[:2] for x in worksheet.get_all_values()]
teachers_only = [x[0] for x in worksheet.get_all_values()]
class_list = ['S1-01','S1-02','S1-03','S1-04','S1-05','S1-06','S1-07','S1-08','S1-09','S1-10',
              'S2-01','S2-02','S2-03','S2-04','S2-05','S2-06','S2-07','S2-08','S2-09','S2-10',
              'S3-01','S3-02','S3-03','S3-04','S3-05','S3-06','S3-07','S3-08','S3-09','S3-10',
              'S4-01','S4-02','S4-03','S4-04','S4-05','S4-06','S4-07','S4-08','S4-09','S4-10']
time_list = ['8:00','8:20','8:40','9:00','9:20','9:40','10:00','10:20','10:40','11:00','11:20','11:40',
             '12:00','12:20','12:40','13:00','13:20','13:40','14:00','14:20','14:40','15:00','15:20','15:40',
             '16:00','16:20','16:40','17:00','17:20','17:40','18:00','18:20']

'''
### Enter Lesson to Swap

'''
teacher = st.selectbox("Select your name...", teachers_only)
class_toswap = st.selectbox("Select a class...", class_list)
day = st.selectbox("Select the lesson day...", ["Odd Monday", "Odd Tuesday", "Odd Wednesday", "Odd Thursday", "Odd Friday", "Even Monday", "Even Tuesday", "Even Wednesday", "Even Thursday", "Even Friday"])
lesson_start = st.selectbox("Select the lesson start time...", time_list)
lesson_end = st.selectbox("Select the lesson end time...", time_list)
lesson_period_start = [key for key in timings.keys() if timings[key][0] == lesson_start]
lesson_period_end = [key for key in timings.keys() if timings[key][1] == lesson_end]

teacherdb = open_class_db('TeacherList')
teachers_free = defaultdict(list)
teachers_class_free = []
other_teachers = []

if st.button("Click to see who is free!"):
    if lesson_period_end <= lesson_period_start: 
        st.write("Error! Please ensure that your lesson end time is after your lesson start time!")
        st.stop()
    lesson_period = lesson_period_start + lesson_period_end
    while lesson_period[0] + 1 != lesson_period[1]:
        lesson_period.insert(1, lesson_period[1] - 1)
    exp = 0
    while True:
        try:
            if day[0] == "O": open_db('TeacherAvailDatabase_ODD')
            elif day[0] == "E": open_db('TeacherAvailDatabase_EVEN')
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
    for teach in teachers_list:
        teacher = teach[0]
        dept = teach[1]
        x = availableper(teacher)
        if teacher in teacherdb.keys() and sublist(lesson_period, x[day.split()[1]]):
            if class_toswap in teacherdb[teacher]:
                teachers_class_free.append(teacher)
            else:
                teachers_free[dept].append(teacher)
        elif teacher in teacherdb.keys() and class_toswap in teacherdb[teacher]:
            other_teachers.append(teacher)

    st.divider()
    '''
    ### Proposed Swaps
    '''
    timetable = load_timetable(teachertt)
  
    show_lesson_swap_options(
        timetable=timetable,
        teacher=teacher,
        day=day,
        lesson_start=lesson_start,
        lesson_end=lesson_end
    )
    
    '''
    ### Other Possibilities to Explore
    '''

    st.subheader("Teachers from my Department who are available during the lesson:")
    for dept in sorted(list(teachers_free.keys())):
        st.write("**"+dept+"**")
        table_display(teachers_free[dept])

    st.subheader("Teachers who are available during the lesson and teach the class:")
    st.write("If you decide you can give the lesson away...")
    table_display(teachers_class_free)
  
    st.subheader("Other teachers who teach the class:")
    st.write("These teachers are not available during your lesson, but you may wish to consider them for a multi-way swap.")
    table_display(other_teachers)
