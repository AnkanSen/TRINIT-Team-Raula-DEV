import datetime
from django.shortcuts import redirect, render
from django.contrib import messages
from .models import Student, Course, Announcement, Assignment, Submission, Material, Faculty, Department
from django.template.defaulttags import register
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from .forms import AnnouncementForm, AssignmentForm, MaterialForm
from django import forms
from django.core import validators
from . import models
import requests
from .utils import send_code
import uuid
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
from bs4 import BeautifulSoup as bb
from django import forms


class LoginForm(forms.Form):
    id = forms.CharField(label='ID', max_length=10, validators=[
                         validators.RegexValidator(r'^\d+$', 'Please enter a valid number.')])
    password = forms.CharField(widget=forms.PasswordInput)


def home(request):
    course = models.Course.objects.all()
    if request.session.get('student_id'):
        student = Student.objects.get(
            student_id=request.session['student_id'])
        course = models.Course.objects.all()
        oneonone=models.BookedClasses.objects.filter(student=student)
      
    else:
        student = None
    if request.session.get('faculty_id'):
        faculty = Faculty.objects.get(
            faculty_id=request.session['faculty_id'])
    else:
        faculty = None

    enrolled = student.course.all() if student else None
    accessed = Course.objects.filter(
        faculty_id=faculty.faculty_id) if faculty else None

    context = {
        'faculty': faculty,
        'courses': course,
        'student': student,
        'enrolled': enrolled,
        'accessed': accessed,
        
    }

    return render(request, 'main/index2.html', context)


def is_student_authorised(request, code):
    course = Course.objects.get(code=code)
    if request.session.get('student_id') and course in Student.objects.get(student_id=request.session['student_id']).course.all():
        return True
    else:
        return False


def is_faculty_authorised(request, code):
    if request.session.get('faculty_id') and code in Course.objects.filter(faculty_id=request.session['faculty_id']).values_list('code', flat=True):
        return True
    else:
        return False


def register_student(requests):
    if requests.method == 'POST':
        username = requests.POST['username']
        name = requests.POST['name']
        password = requests.POST.get('password', '')
        email = requests.POST['email']
        code: str = send_code(email=email)
        token=uuid.uuid4()
        # department=models.Department.objects.get(department_id=0)
        student = models.Student.objects.create(
            student_id=username, name=name, password=password, email=email,stucode=code,stutoken=token)
        student.save()
        return render(requests,'main/validate.html',{"token":token})
    return render(requests, 'register_student.html')
def validatestudent(request,token):
    if request.method=='POST':
        code: str = request.POST.get('code')
        student=Student.objects.get(stutoken=token)
        if student.stuis_active==True:
            messages.info(request,"Account already verified.Kindly login")
            return redirect('/login')
        if code==student.stucode:
            student.stuis_active=True
            messages.info(request,"Account  verified Successfully.Kindly login")
            return redirect('/login')
        else:
            messages.info(request,"Wrong code")
            return redirect(f'/validatestudent/{token}')
    else:
        return render(request,'main/validate.html',{"token":token})
def validatefaculty(request,token):
    if request.method=='POST':
        code: str = request.POST.get('code')
        student=Faculty.objects.get(factoken=token)
        if student.facis_active==True:
            messages.info(request,"Account already verified.Kindly login")
            return redirect('/login')
        if code==student.faccode:
            student.stuis_active=True
            messages.info(request,"Account  verified Successfully.Kindly login")
            return redirect('/login')
        else:
            messages.info(request,"Wrong code")
            return redirect(f'/validatefaculty/{token}')
    else:
        return render(request,'main/validate2.html',{"token":token})

def create_class(requests):
    if requests.session.get('faculty_id'):
        if requests.method=='POST':
            name=requests.POST['name']
            id=requests.POST['id']
            price=requests.POST['price']
        # dept=requests.POST['dept']
            time_slot=requests.POST['time_slot']
            access_code=requests.POST['access_code']
            time=time_slot.split()
            faculty=models.Faculty.objects.get(faculty_id=requests.session.get('faculty_id'))
            departments=models.Department.objects.get(department_id=faculty.department.department_id)
            one_course=models.OneCourse.objects.create(name=name,code=id,department=departments,faculty=faculty,price=price,access_code=access_code,time=time_slot)
            one_course.save()
    return render(requests, 'main/create_class.html')

def connect(request,code):
    roomno=code
    curr = datetime.datetime.now()
    email = "ak21eeb0b08@student.nitw.ac.in"
    SERVER = "smtp.gmail.com"
    PORT = 587
    FROM = "ankitch860@gmail.com"
    TO = email
    PASS = 'stcuyuhbivtltoey'
    msg = MIMEMultipart()
    msg['subject'] = 'Join the meet '+str(curr.day)+"-"+str(curr.year)
    msg['From'] = FROM
    msg['To'] = TO
    co=f"Join the meet using this link. https:127.0.0.1:8000/connect/{code}"
    msg.attach(MIMEText(co, 'html'))
    print("Creating mail")
    server = SMTP(SERVER, PORT)
    server.set_debuglevel(1)
    server.ehlo()
    server.starttls()
    server.login(FROM, PASS)
    server.sendmail(FROM, TO, msg.as_string())
    print('Sending Email')
    server.quit()
    print('Email sent ......')
    return render(request,"main/index.html")
def book_class(requests):
    context = {
        'student': None,
        'faculty': None
    }
    if 'student_id' in requests.session:
        student = models.Student.objects.get(
            student_id=requests.session['student_id'])
        faculty = None
        one_course=models.OneCourse.objects.all()
        if requests.method=='POST':
            time=requests.POST['time']
            name=requests.POST.get('name','')
            id=requests.POST['id']
            student=models.Student.objects.get(student_id=requests.session['student_id'])
            faculty=models.Faculty.objects.get(faculty_id=name)
            courses=models.OneCourse.objects.get(code=id)
            booked=models.BookedClasses.objects.create(student=student,faculty=faculty,time=time,code=id)
            course=models.Course.objects.create(code=id,faculty=faculty,studentKey=courses.price,facultyKey=time,department=courses.department,name=courses.name)
            course.save()
            booked.save()
            
        context = {
            'student': student,
            'faculty': faculty,
            'course':one_course
        }

    return render(requests, 'main/book_class.html', context)


def register_faculty(requests):
    department = models.Department.objects.all()
    if requests.method == 'POST':
        username = requests.POST['username']
        name = requests.POST['name']
        password = requests.POST.get('password', '')
        email = requests.POST['email']
        departments = requests.POST.get('department', '')
        code: str = send_code(email=email)
        token=uuid.uuid4()
        sdep = models.Department.objects.get(department_id=departments)
        faculty = models.Faculty.objects.create(
            faculty_id=username, name=name, password=password, email=email, department=sdep,faccode=code,factoken=token)
        faculty.save()
        return render(requests,'main/validate2.html',{"token":token})
    return render(requests, 'register_faculty.html', {'department': department})


# Custom Login page for both student and faculty
def std_login(request):
    error_messages = []

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            id = form.cleaned_data['id']
            password = form.cleaned_data['password']

            if Student.objects.filter(student_id=id, password=password).exists():
                request.session['student_id'] = id
                return redirect('myCourses')
            elif Faculty.objects.filter(faculty_id=id, password=password).exists():
                request.session['faculty_id'] = id
                return redirect('facultyCourses')
            else:
                error_messages.append('Invalid login credentials.')
        else:
            error_messages.append('Invalid form data.')
    else:
        form = LoginForm()

    if 'student_id' in request.session:
        return redirect('/my/')
    elif 'faculty_id' in request.session:
        return redirect('/facultyCourses/')

    context = {'form': form, 'error_messages': error_messages}
    return render(request, 'login_page.html', context)


def login_student(request):
    error_messages = []

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            id = form.cleaned_data['id']
            password = form.cleaned_data['password']

            if Student.objects.filter(student_id=id, password=password).exists():
                request.session['student_id'] = id
                return redirect('myCourses')
            # elif Faculty.objects.filter(faculty_id=id, password=password).exists():
            #     request.session['faculty_id'] = id
            #     return redirect('facultyCourses')
            else:
                error_messages.append('Invalid login credentials.')
        else:
            error_messages.append('Invalid form data.')
    else:
        form = LoginForm()

    if 'student_id' in request.session:
        return redirect('/my/')
    elif 'faculty_id' in request.session:
        return redirect('/facultyCourses/')

    context = {'form': form, 'error_messages': error_messages}
    return render(request, 'login_student.html', context)


def login_faculty(request):
    error_messages = []

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            id = form.cleaned_data['id']
            password = form.cleaned_data['password']

            if Faculty.objects.filter(faculty_id=id, password=password).exists():
                request.session['faculty_id'] = id
                return redirect('facultyCourses')
            else:
                error_messages.append('Invalid login credentials.')
        else:
            error_messages.append('Invalid form data.')
    else:
        form = LoginForm()

    if 'student_id' in request.session:
        return redirect('/my/')
    elif 'faculty_id' in request.session:
        return redirect('/facultyCourses/')

    context = {'form': form, 'error_messages': error_messages}
    return render(request, 'login_faculty.html', context)

# Clears the session on logout


def std_logout(request):
    request.session.flush()
    return redirect('std_login')


# Display all courses (student view)
def myCourses(request):
    # try:
    if request.session.get('student_id'):
        student = Student.objects.get(
            student_id=request.session['student_id'])
        courses = student.course.all()
        one_courses=models.BookedClasses.objects.filter(student=student)
        # print(one_courses)
        faculty = student.course.all().values_list('faculty_id', flat=True)
        departments = models.Department.objects.all()
        context = {
            'courses': courses,
            'booked':one_courses,
            'student': student,
            'faculty': faculty,
            'department': departments
        }

        return render(request, 'main/myCourses.html', context)
    else:
        return redirect('std_login')
    # except:
    return render(request, 'error.html')


def facultyCourses(request):

    if request.session['faculty_id']:
        faculty = Faculty.objects.get(faculty_id=request.session['faculty_id'])
        courses = Course.objects.filter(
            faculty_id=request.session['faculty_id'])
        # Student count of each course to show on the faculty page
        studentCount = Course.objects.all().annotate(student_count=Count('students'))

        studentCountDict = {}

        for course in studentCount:
            studentCountDict[course.code] = course.student_count

        @register.filter
        def get_item(dictionary, course_code):
            return dictionary.get(course_code)

        context = {
            'courses': courses,
            'faculty': faculty,
            'studentCount': studentCountDict
        }

        return render(request, 'main/facultyCourses.html', context)

    else:
        return redirect('std_login')

# Particular course page (student view)


def course_page(request, code):
    try:
        course = Course.objects.get(code=code)
        if is_student_authorised(request, code):
            try:
                announcements = Announcement.objects.filter(course_code=course)
                assignments = Assignment.objects.filter(
                    course_code=course.code)
                materials = Material.objects.filter(course_code=course.code)

            except:
                announcements = None
                assignments = None
                materials = None

            context = {
                'course': course,
                'announcements': announcements,
                'assignments': assignments[:3],
                'materials': materials,
                'student': Student.objects.get(student_id=request.session['student_id'])
            }

            return render(request, 'main/course.html', context)

        else:
            return redirect('std_login')
    except:
        return render(request, 'error.html')


def add_courses(requests):
    if requests.session.get('faculty_id'):
        try:
            if requests.method == 'POST':
                code = requests.POST['code']
                name = requests.POST['name']
                price = requests.POST['price']
                time = requests.POST['time']
                faculty = models.Faculty.objects.get(
                    faculty_id=requests.session.get('faculty_id'))
                couse = models.Course.objects.create(
                    code=code, name=name, department=faculty.department, faculty=faculty, studentKey=price, facultyKey=time)
                couse.save()
        except:
            return render(requests, 'error.html')
    return render(requests, 'main/add_courses.html')

# Particular course page (faculty view)


def videochat(request, code):
    name = request.user.username
    return render(request, "main/mumble2/room.html", {"code": code, "name": name})


def videoochat(request):
    return render(request, "main/mumble2/lobby.html")


def course_page_faculty(request, code):
    course = Course.objects.get(code=code)
    if request.session.get('faculty_id'):
        try:
            announcements = Announcement.objects.filter(course_code=course)
            assignments = Assignment.objects.filter(
                course_code=course.code)
            materials = Material.objects.filter(course_code=course.code)
            studentCount = Student.objects.filter(course=course).count()

        except:
            announcements = None
            assignments = None
            materials = None

        context = {
            'course': course,
            'announcements': announcements,
            'assignments': assignments[:3],
            'materials': materials,
            'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id']),
            'studentCount': studentCount
        }

        return render(request, 'main/faculty_course.html', context)
    else:
        return redirect('std_login')


def error(request):
    return render(request, 'error.html')


# Display user profile(student & faculty)
def profile(request, id):
    try:
        if request.session['student_id'] == id:
            student = Student.objects.get(student_id=id)
            return render(request, 'main/profile.html', {'student': student})
        else:
            return redirect('std_login')
    except:
        try:
            if request.session['faculty_id'] == id:
                faculty = Faculty.objects.get(faculty_id=id)
                return render(request, 'main/faculty_profile.html', {'faculty': faculty})
            else:
                return redirect('std_login')
        except:
            return render(request, 'error.html')


def addAnnouncement(request, code):
    if is_faculty_authorised(request, code):
        if request.method == 'POST':
            form = AnnouncementForm(request.POST)
            form.instance.course_code = Course.objects.get(code=code)
            if form.is_valid():
                form.save()
                messages.success(
                    request, 'Announcement added successfully.')
                return redirect('/faculty/' + str(code))
        else:
            form = AnnouncementForm()
        return render(request, 'main/announcement.html', {'course': Course.objects.get(code=code), 'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id']), 'form': form})
    else:
        return redirect('std_login')


def deleteAnnouncement(request, code, id):
    if is_faculty_authorised(request, code):
        try:
            announcement = Announcement.objects.get(course_code=code, id=id)
            announcement.delete()
            messages.warning(request, 'Announcement deleted successfully.')
            return redirect('/faculty/' + str(code))
        except:
            return redirect('/faculty/' + str(code))
    else:
        return redirect('std_login')


def editAnnouncement(request, code, id):
    if is_faculty_authorised(request, code):
        announcement = Announcement.objects.get(course_code_id=code, id=id)
        form = AnnouncementForm(instance=announcement)
        context = {
            'announcement': announcement,
            'course': Course.objects.get(code=code),
            'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id']),
            'form': form
        }
        return render(request, 'main/update-announcement.html', context)
    else:
        return redirect('std_login')


def updateAnnouncement(request, code, id):
    if is_faculty_authorised(request, code):
        try:
            announcement = Announcement.objects.get(course_code_id=code, id=id)
            form = AnnouncementForm(request.POST, instance=announcement)
            if form.is_valid():
                form.save()
                messages.info(request, 'Announcement updated successfully.')
                return redirect('/faculty/' + str(code))
        except:
            return redirect('/faculty/' + str(code))

    else:
        return redirect('std_login')


def addAssignment(request, code):
    if is_faculty_authorised(request, code):
        if request.method == 'POST':
            form = AssignmentForm(request.POST, request.FILES)
            form.instance.course_code = Course.objects.get(code=code)
            if form.is_valid():
                form.save()
                messages.success(request, 'Assignment added successfully.')
                return redirect('/faculty/' + str(code))
        else:
            form = AssignmentForm()
        return render(request, 'main/assignment.html', {'course': Course.objects.get(code=code), 'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id']), 'form': form})
    else:
        return redirect('std_login')


def assignmentPage(request, code, id):
    course = Course.objects.get(code=code)
    if is_student_authorised(request, code):
        assignment = Assignment.objects.get(course_code=course.code, id=id)
        try:

            submission = Submission.objects.get(assignment=assignment, student=Student.objects.get(
                student_id=request.session['student_id']))

            context = {
                'assignment': assignment,
                'course': course,
                'submission': submission,
                'time': datetime.datetime.now(),
                'student': Student.objects.get(student_id=request.session['student_id']),
                'courses': Student.objects.get(student_id=request.session['student_id']).course.all()
            }

            return render(request, 'main/assignment-portal.html', context)

        except:
            submission = None

        context = {
            'assignment': assignment,
            'course': course,
            'submission': submission,
            'time': datetime.datetime.now(),
            'student': Student.objects.get(student_id=request.session['student_id']),
            'courses': Student.objects.get(student_id=request.session['student_id']).course.all()
        }

        return render(request, 'main/assignment-portal.html', context)
    else:

        return redirect('std_login')


def allAssignments(request, code):
    if is_faculty_authorised(request, code):
        course = Course.objects.get(code=code)
        assignments = Assignment.objects.filter(course_code=course)
        studentCount = Student.objects.filter(course=course).count()

        context = {
            'assignments': assignments,
            'course': course,
            'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id']),
            'studentCount': studentCount

        }
        return render(request, 'main/all-assignments.html', context)
    else:
        return redirect('std_login')


def allAssignmentsSTD(request, code):
    if is_student_authorised(request, code):
        course = Course.objects.get(code=code)
        assignments = Assignment.objects.filter(course_code=course)
        context = {
            'assignments': assignments,
            'course': course,
            'student': Student.objects.get(student_id=request.session['student_id']),

        }
        return render(request, 'main/all-assignments-std.html', context)
    else:
        return redirect('std_login')


def addSubmission(request, code, id):
    try:
        course = Course.objects.get(code=code)
        if is_student_authorised(request, code):
            # check if assignment is open
            assignment = Assignment.objects.get(course_code=course.code, id=id)
            if assignment.deadline < datetime.datetime.now():

                return redirect('/assignment/' + str(code) + '/' + str(id))

            if request.method == 'POST' and request.FILES['file']:
                assignment = Assignment.objects.get(
                    course_code=course.code, id=id)
                submission = Submission(assignment=assignment, student=Student.objects.get(
                    student_id=request.session['student_id']), file=request.FILES['file'],)
                submission.status = 'Submitted'
                submission.save()
                return HttpResponseRedirect(request.path_info)
            else:
                assignment = Assignment.objects.get(
                    course_code=course.code, id=id)
                submission = Submission.objects.get(assignment=assignment, student=Student.objects.get(
                    student_id=request.session['student_id']))
                context = {
                    'assignment': assignment,
                    'course': course,
                    'submission': submission,
                    'time': datetime.datetime.now(),
                    'student': Student.objects.get(student_id=request.session['student_id']),
                    'courses': Student.objects.get(student_id=request.session['student_id']).course.all()
                }

                return render(request, 'main/assignment-portal.html', context)
        else:
            return redirect('std_login')
    except:
        return HttpResponseRedirect(request.path_info)


def viewSubmission(request, code, id):
    course = Course.objects.get(code=code)
    if is_faculty_authorised(request, code):
        try:
            assignment = Assignment.objects.get(course_code_id=code, id=id)
            submissions = Submission.objects.filter(
                assignment_id=assignment.id)

            context = {
                'course': course,
                'submissions': submissions,
                'assignment': assignment,
                'totalStudents': len(Student.objects.filter(course=course)),
                'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id']),
                'courses': Course.objects.filter(faculty_id=request.session['faculty_id'])
            }

            return render(request, 'main/assignment-view.html', context)

        except:
            return redirect('/faculty/' + str(code))
    else:
        return redirect('std_login')


def gradeSubmission(request, code, id, sub_id):
    try:
        course = Course.objects.get(code=code)
        if is_faculty_authorised(request, code):
            if request.method == 'POST':
                assignment = Assignment.objects.get(course_code_id=code, id=id)
                submissions = Submission.objects.filter(
                    assignment_id=assignment.id)
                submission = Submission.objects.get(
                    assignment_id=id, id=sub_id)
                submission.marks = request.POST['marks']
                if request.POST['marks'] == 0:
                    submission.marks = 0
                submission.save()
                return HttpResponseRedirect(request.path_info)
            else:
                assignment = Assignment.objects.get(course_code_id=code, id=id)
                submissions = Submission.objects.filter(
                    assignment_id=assignment.id)
                submission = Submission.objects.get(
                    assignment_id=id, id=sub_id)

                context = {
                    'course': course,
                    'submissions': submissions,
                    'assignment': assignment,
                    'totalStudents': len(Student.objects.filter(course=course)),
                    'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id']),
                    'courses': Course.objects.filter(faculty_id=request.session['faculty_id'])
                }

                return render(request, 'main/assignment-view.html', context)

        else:
            return redirect('std_login')
    except:
        return redirect('/error/')


def addCourseMaterial(request, code):
    if is_faculty_authorised(request, code):
        if request.method == 'POST':
            form = MaterialForm(request.POST, request.FILES)
            form.instance.course_code = Course.objects.get(code=code)
            if form.is_valid():
                form.save()
                messages.success(request, 'New course material added')
                return redirect('/faculty/' + str(code))
            else:
                return render(request, 'main/course-material.html', {'course': Course.objects.get(code=code), 'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id']), 'form': form})
        else:
            form = MaterialForm()
            return render(request, 'main/course-material.html', {'course': Course.objects.get(code=code), 'faculty': Faculty.objects.get(faculty_id=request.session['faculty_id']), 'form': form})
    else:
        return redirect('std_login')


def deleteCourseMaterial(request, code, id):
    if is_faculty_authorised(request, code):
        course = Course.objects.get(code=code)
        course_material = Material.objects.get(course_code=course, id=id)
        course_material.delete()
        messages.warning(request, 'Course material deleted')
        return redirect('/faculty/' + str(code))
    else:
        return redirect('std_login')


def courses(request):
    if request.session.get('student_id') or request.session.get('faculty_id'):
        departments = models.Department.objects.all()
        if request.session.get('faculty_id'):
            faculty = models.Faculty.objects.get(
                faculty_id=request.session.get('faculty_id'))
            courses = Course.objects.filter(department=faculty.department)
        else:
            courses = Course.objects.all()
        if request.session.get('student_id'):
            student = Student.objects.get(
                student_id=request.session['student_id'])
            course = models.Course.objects.all()
            oneonone=models.BookedClasses.objects.filter(student=student)
            codes=[]
            for j in oneonone:
                codes.append(j.code)
            print(codes)
            courses=[]
            for i in course:
                if i.code in codes:
                    courses.append(i)
            print(courses)
        else:
            student = None
        if request.session.get('faculty_id'):
            faculty = Faculty.objects.get(
                faculty_id=request.session['faculty_id'])
        else:
            faculty = None

        enrolled = student.course.all() if student else None
        accessed = Course.objects.filter(
            faculty_id=faculty.faculty_id) if faculty else None

        if request.method == "POST":
            dept = request.POST['dept']

            if dept == 0:
                courses = models.Course.objects.all()
            else:
                deptar = models.Department.objects.filter(
                    department_id=dept).first()
                courses = models.Course.objects.filter(department=deptar)
                course=[]
                print(courses)
        context = {
            'faculty': faculty,
            'courses': courses,
            'student': student,
            'enrolled': enrolled,
            'accessed': accessed,
            'department': departments
        }

        return render(request, 'main/all-courses.html', context)

    else:
        return redirect('std_login')


def departments(request):
    if request.session.get('student_id') or request.session.get('faculty_id'):
        departments = Department.objects.all()
        if request.session.get('student_id'):
            student = Student.objects.get(
                student_id=request.session['student_id'])
        else:
            student = None
        if request.session.get('faculty_id'):
            faculty = Faculty.objects.get(
                faculty_id=request.session['faculty_id'])
        else:
            faculty = None
        context = {
            'faculty': faculty,
            'student': student,
            'deps': departments
        }

        return render(request, 'main/departments.html', context)

    else:
        return redirect('std_login')


def access(request, code):
    if request.session.get('student_id'):
        course = Course.objects.get(code=code)
        access_code = ''
        student = Student.objects.get(student_id=request.session['student_id'])
        if request.method == 'GET':
            pay = request.GET.get('paid', '')
            if pay:
                access_code = str(course.studentKey)

        if request.method == 'POST':
            if (request.POST['key']) == str(course.studentKey):
                student.course.add(course)
                student.save()
                return redirect('/my/')
            else:
                messages.error(request, 'Invalid key')
                return HttpResponseRedirect(request.path_info)
        else:
            return render(request, 'main/access.html', {'course': course, 'student': student, 'access_code': access_code, 'pay': pay})

    else:
        return redirect('std_login')


def search(request):
    if request.session.get('student_id') or request.session.get('faculty_id'):
        if request.method == 'GET' and request.GET['q']:
            q = request.GET['q']
            courses = Course.objects.filter(Q(code__icontains=q) | Q(
                name__icontains=q) | Q(faculty__name__icontains=q))

            if request.session.get('student_id'):
                student = Student.objects.get(
                    student_id=request.session['student_id'])
            else:
                student = None
            if request.session.get('faculty_id'):
                faculty = Faculty.objects.get(
                    faculty_id=request.session['faculty_id'])
            else:
                faculty = None
            enrolled = student.course.all() if student else None
            accessed = Course.objects.filter(
                faculty_id=faculty.faculty_id) if faculty else None

            context = {
                'courses': courses,
                'faculty': faculty,
                'student': student,
                'enrolled': enrolled,
                'accessed': accessed,
                'q': q
            }
            return render(request, 'main/search.html', context)
        else:
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        return redirect('std_login')


def changePasswordPrompt(request):
    if request.session.get('student_id'):
        student = Student.objects.get(student_id=request.session['student_id'])
        return render(request, 'main/changePassword.html', {'student': student})
    elif request.session.get('faculty_id'):
        faculty = Faculty.objects.get(faculty_id=request.session['faculty_id'])
        return render(request, 'main/changePasswordFaculty.html', {'faculty': faculty})
    else:
        return redirect('std_login')


def changePhotoPrompt(request):
    if request.session.get('student_id'):
        student = Student.objects.get(student_id=request.session['student_id'])
        return render(request, 'main/changePhoto.html', {'student': student})
    elif request.session.get('faculty_id'):
        faculty = Faculty.objects.get(faculty_id=request.session['faculty_id'])
        return render(request, 'main/changePhotoFaculty.html', {'faculty': faculty})
    else:
        return redirect('std_login')


def changePassword(request):
    if request.session.get('student_id'):
        student = Student.objects.get(
            student_id=request.session['student_id'])
        if request.method == 'POST':
            if student.password == request.POST['oldPassword']:
                # New and confirm password check is done in the client side
                student.password = request.POST['newPassword']
                student.save()
                messages.success(request, 'Password was changed successfully')
                return redirect('/profile/' + str(student.student_id))
            else:
                messages.error(
                    request, 'Password is incorrect. Please try again')
                return redirect('/changePassword/')
        else:
            return render(request, 'main/changePassword.html', {'student': student})
    else:
        return redirect('std_login')


def changePasswordFaculty(request):
    if request.session.get('faculty_id'):
        faculty = Faculty.objects.get(
            faculty_id=request.session['faculty_id'])
        if request.method == 'POST':
            if faculty.password == request.POST['oldPassword']:
                # New and confirm password check is done in the client side
                faculty.password = request.POST['newPassword']
                faculty.save()
                messages.success(request, 'Password was changed successfully')
                return redirect('/facultyProfile/' + str(faculty.faculty_id))
            else:
                print('error')
                messages.error(
                    request, 'Password is incorrect. Please try again')
                return redirect('/changePasswordFaculty/')
        else:
            print(faculty)
            return render(request, 'main/changePasswordFaculty.html', {'faculty': faculty})
    else:
        return redirect('std_login')


def changePhoto(request):
    if request.session.get('student_id'):
        student = Student.objects.get(
            student_id=request.session['student_id'])
        if request.method == 'POST':
            if request.FILES['photo']:
                student.photo = request.FILES['photo']
                student.save()
                messages.success(request, 'Photo was changed successfully')
                return redirect('/profile/' + str(student.student_id))
            else:
                messages.error(
                    request, 'Please select a photo')
                return redirect('/changePhoto/')
        else:
            return render(request, 'main/changePhoto.html', {'student': student})
    else:
        return redirect('std_login')


def changePhotoFaculty(request):
    if request.session.get('faculty_id'):
        faculty = Faculty.objects.get(
            faculty_id=request.session['faculty_id'])
        if request.method == 'POST':
            if request.FILES['photo']:
                faculty.photo = request.FILES['photo']
                faculty.save()
                messages.success(request, 'Photo was changed successfully')
                return redirect('/facultyProfile/' + str(faculty.faculty_id))
            else:
                messages.error(
                    request, 'Please select a photo')
                return redirect('/changePhotoFaculty/')
        else:
            return render(request, 'main/changePhotoFaculty.html', {'faculty': faculty})
    else:
        return redirect('std_login')


def guestStudent(request):
    request.session.flush()
    try:
        student = Student.objects.get(name='Guest Student')
        request.session['student_id'] = str(student.student_id)
        return redirect('myCourses')
    except:
        return redirect('std_login')


def guestFaculty(request):
    request.session.flush()
    try:
        faculty = Faculty.objects.get(name='Guest Faculty')
        request.session['faculty_id'] = str(faculty.faculty_id)
        return redirect('facultyCourses')
    except:
        return redirect('std_login')
