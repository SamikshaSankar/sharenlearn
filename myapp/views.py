from django.contrib.auth.decorators import login_required
import json
from django.core.mail import EmailMultiAlternatives, send_mail
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from random import randint
import re
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import *
from django.contrib.auth import authenticate, login, logout
from datetime import date

from django.contrib import messages
from django.db import IntegrityError


from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password


import requests

from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
import re

# Make a regular expression
# for validating an Email
regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'

def check(email):
    if(re.search(regex, email)):
        return True

    else:
        return False


def index(request):
    if request.user.is_authenticated:
        return redirect('/profile')
    context = {'auth': request.user.is_authenticated}
    return render(request, 'home.html', context)

def about(request):
    return redirect('/#about')

def contact(request):
    context = {'auth': request.user.is_authenticated}
    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        subject = request.POST['subject']
        message = request.POST['message']
        if check(email) == False:
            messages.error(request, "Looks like email is not valid")
            return redirect('/#contact')
        # try:
        #     # send_mail('Contact Form',fmessage, settings.EMAIL_HOST_USER,['reciever@gmail.com'], fail_silently=False)
        #     pass
        # except Exception as e:
        #     messages.error(
        #         request, "Some Error Occured We are sorry for that Please Try again!!")
        messages.success(request, 'Thanks for contacting us, we will reach you soon')
        return redirect('index')
    else:
        return redirect('/#contact')



def Logout(request):
    logout(request)
    return redirect('index')



########################################################################################################
###################################        USER        ################################################
########################################################################################################

def signup1(request):
    if request.method == 'POST':
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        password = request.POST['password']
        contact = request.POST['contact']
        role = request.POST['role']
        dept = request.POST['dept']
        try:
            user = User.objects.create_user(username=email, password=password, first_name=fname, last_name=lname)
            user.save()
            signup = Signup.objects.create(user=user, contact=contact, branch=dept, role=role)
            signup.save()
            messages.success(request, "Account Created")
            return redirect("login")
        except IntegrityError:
            messages.info(request, "Username taken, Try different")
            return render(request, "signup.html")
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'signup.html')


def userlogin(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
            # captcha_token = request.POST['g-recaptcha-response']
            # cap_url = "https://www.google.com/recaptcha/api/siteverify"
            # cap_data = {"secret": settings.GOOGLE_RECAPTCHA_SECRET_KEY, "response": captcha_token}
            # cap_server_response = requests.post(url=cap_url, data=cap_data)
            # cap_json = cap_server_response.json()
            # if cap_json['success'] == False:
            #     messages.error(request, "Captcha Invalid. Please Try Again")
            #     return redirect('login')
            u = request.POST['email']
            p = request.POST['password']
            user = authenticate(username=u, password=p)
            if user is not None:
                login(request, user)
                messages.success(request, "Logged In Successfully")
                return redirect('/profile')
            else:
                messages.error(request, "Invalid Login Credentials")
        return render(request, 'login.html')
    else:
        return redirect('index')
def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    user = User.objects.get(id=request.user.id)
    data = Signup.objects.get(user=user)
    d = {'data': data, 'user': user, 'auth': request.user.is_authenticated}
    return render(request, 'profile.html', d)


def edit_profile(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please login first")
        return redirect('login')
    user = User.objects.get(id=request.user.id)
    data = Signup.objects.get(user=user)
    if request.method == 'POST':
        fname = request.POST['fname']
        lname = request.POST['lname']
        contact = request.POST['contact']
        user.first_name, user.last_name, data.contact = fname, lname, contact
        user.save()
        data.save()
        messages.success(request, "Profile Updated Successfully")
        return redirect('/profile')
    d = {'data': data, 'user': user, 'auth': request.user.is_authenticated}
    return render(request, 'edit_profile.html', d)
    

def changepassword(request):
    if not request.user:
        return redirect('login')
    error = ""
    if request.method == "POST":
        o = request.POST['old']
        n = request.POST['new']
        c = request.POST['confirm']
        if c == n:
            u = User.objects.get(username__exact=request.user.username)
            u.set_password(n)
            u.save()
            error = "no"
            messages.info(request, f'Password Changed Successfully')
            return redirect('/logout')
        else:
            error = "yes"
            messages.info(request, f'Invalid Login Credentials, Try Again')
    d = {'error': error}
    return render(request, 'changepassword.html', d)

@csrf_exempt
def Forgot_Password(request):
    if(request.method =="POST"):
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = User.objects.get(username=email)
        user.set_password(password)
        user.save()
        messages.success(request, "You can now login with your new password.")
        return redirect("login")
    return render(request, 'forgotpassword.html')


########################################################################################################
###################################        ADMIN        ################################################
########################################################################################################

def admin_home(request):

    if not request.user.is_staff:
        return redirect('login_admin')

    pn = Notes.objects.filter(status="pending").count()
    an = Notes.objects.filter(status="Accepted").count()
    rn = Notes.objects.filter(status="Rejected").count()
    aln = Notes.objects.all().count()
    d = {'pn': pn, 'an': an, 'rn': rn, 'aln': aln}
    return render(request, 'admin_home.html', d)


def login_admin(request) :
    error = ""

    if request.method == 'POST':
        u = request.POST['uname']
        p = request.POST['pwd']
        user = authenticate(username=u, password=p)
        try:
            if user.is_staff:
                login(request, user)
                error = "no"
                messages.info(request, f'Logged in Successfully')
                return redirect('/admin_home')
            else:
                error = "yes"
                messages.info(request, f'Invalid Login Credentials, Try Again')

        except:
            error = "yes"
            messages.info(request, f'Invalid Login Credentials, Try Again')
    d = {'error': error}
    return render(request, 'login_admin.html', d)

########################################################################################################
########################################################################################################








def gen_otp():
    """This function returns a 6-digit OTP everytime it is called."""
    return randint(100000, 999999)


def send_otp(request):
    """This function saves the OTP in the database and sends an email to the user with that OTP."""

    user_email = request.GET['email']
    try:
        user_name = request.GET['fname']
    except Exception:
        user = User.objects.get(username=user_email)
        user_name = user.first_name
    otp = gen_otp()     # Generate OTP
    # Save OTP in database and send email to user
    try:
        OTPModel.objects.create(user=user_email, otp=otp)
        data = {
            'receiver': user_name.capitalize(),
            'otp': otp
        }
        html_content = render_to_string("emails/otp.html", data)
        text_content = strip_tags(html_content)

        email = EmailMultiAlternatives(
            f"One Time Password | Share N Learn",
            text_content,
            "Share N Learn <no-reply@sharenlearn.com>",
            [user_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        return JsonResponse({'otp_sent': f'An OTP has been sent to {user_email}.'})
    except Exception as e:
        print(e)
        return JsonResponse({'otp_error': 'Error while sending OTP, try again'})


def match_otp(email, otp):
    """This function matches the OTP entered by the user with that in the database."""

    otp_from_db = OTPModel.objects.filter(user=email).last().otp
    return str(otp) == str(otp_from_db)


def check_otp(request):
    """This function gets the OTP from the user and sends it to match_otp function."""

    req_otp = request.GET['otp']
    req_user = request.GET['email']
    if match_otp(req_user, req_otp):
        return JsonResponse({'otp_match': True})
    else:
        return JsonResponse({'otp_mismatch': 'OTP does not match.'})


def update_profile_photo(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({"message": "notlogin"});
        user = User.objects.get(id=request.user.id)
        data = Signup.objects.get(user=user)
        profile = request.FILES['profile']
        data.profile_photo = profile
        data.save();
        return JsonResponse({"message": "OK", "url": data.profile_photo.url})
    return redirect('login')

def delete_profile_photo(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({"message": "notlogin"});
        user = User.objects.get(id=request.user.id)
        data = Signup.objects.get(user=user)
        data.profile_photo = None
        data.save();
        return JsonResponse({"message": "OK"})
    return redirect('login')

def upload_notes(request):
    if not request.user.is_authenticated:
        messages.info(request, "Login to Upload Notes")
        return redirect('login')
    if request.method == 'POST':
        b = request.POST['dept']
        s = request.POST['subject']
        n = request.FILES['file']
        f = request.POST['ftype']
        d = request.POST['desc']
        u = User.objects.filter(username=request.user.username).first()
        try:
            Notes.objects.create(user=u, uploadingdate=date.today(), branch=b, subject=s,
                                 notesfile=n, filetype=f, description=d, status=False)
            messages.success(request, f'Notes Uploaded Successfully')
            return redirect('view_usernotes');
        except:
            messages.error(request, f'Something went wrong, Try Again')

    return render(request, 'upload_notes.html', {'auth': request.user.is_authenticated})


def view_usernotes(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please login to access your uploads")
        return redirect('login')
    user = User.objects.get(id=request.user.id)
    notes = Notes.objects.filter(user=user)
    d = {'notes': notes, 'auth': request.user.is_authenticated }
    return render(request, 'view_usernotes.html', d)


def delete_usernotes(request, pid):
    if not request.user:
        return redirect('login')
    notes = Notes.objects.get(id=pid)
    notes.delete()
    messages.info(request, f'Deleted Successfully')
    return redirect('view_usernotes')


def view_users(request):
    if not request.user.is_staff:
        return redirect('login')
    users = Signup.objects.all()

    d = {'users': users}
    return render(request, 'view_users.html', d)


def delete_users(request, pid):
    if not request.user:
        return redirect('login')
    users = User.objects.get(id=pid)
    users.delete()
    return redirect('view_users')


def pending_notes(request):
    if not request.user.is_authenticated:
        return redirect('login_admin')

    notes = Notes.objects.filter(status="pending")
    d = {'notes': notes, }
    return render(request, 'pending_notes.html', d)


def assign_status(request, pid):
    if not request.user.is_authenticated:
        return redirect('login')
    notes = Notes.objects.get(id=pid)
    error = ""
    if request.method == 'POST':
        s = request.POST['status']
        try:
            notes.status = s
            notes.save()
            error = "no"
            messages.info(request, f'Status Updated Successfullly')
            return redirect('/all_notes')
        except:
            error = "yes"
            messages.info(request, f'Something went wrong, Try Again')
    d = {'notes': notes, 'error': error}
    return render(request, 'assign_status.html', d)


def accepted_notes(request):
    if not request.user.is_authenticated:
        return redirect('login_admin')
    notes = Notes.objects.filter(status="Accepted")
    d = {'notes': notes}
    return render(request, 'accepted_notes.html', d)


def rejected_notes(request):
    if not request.user.is_authenticated:
        return redirect('login_admin')
    notes = Notes.objects.filter(status="Rejected")
    d = {'notes': notes}
    return render(request, 'rejected_notes.html', d)


def all_notes(request):
    if not request.user.is_authenticated:
        return redirect('login_admin')
    notes = Notes.objects.all()
    d = {'notes': notes}
    return render(request, 'all_notes.html', d)


def delete_notes(request, pid):
    if not request.user:
        return redirect('login')
    notes = Notes.objects.get(id=pid)
    notes.delete()
    return redirect('all_notes')


def viewall_usernotes(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please login to access all uploads")
        return redirect('login')
    notes = Notes.objects.filter(status=True)
    d = {'notes': notes, 'auth': request.user.is_authenticated}
    return render(request, 'viewall_usernotes.html', d)




# AJAX Validations Start Here

def email_validation(request):
    """This function will be used to validate email against a regex pattern as well as to check if a user is already registered."""

    data = json.loads(request.body)
    email = data['email']
    pattern = '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if User.objects.filter(username=email).exists():
        return JsonResponse({'email_error': 'You are already registered. Please login to continue.'}, status=409)
    if not bool(re.match(pattern, email)):
        return JsonResponse({'email_pattern_error': 'Please enter a valid email address.'})
    return JsonResponse({'email_valid': True})


def password_validation(request):
    """This function will be used to validate password against a regex pattern."""

    data = json.loads(request.body)
    password = data['password']
    pattern = '^(?=.*[0-9])(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%&_])(?=\S+$).{8,20}$'
    if bool(re.match(pattern, password)):
        return JsonResponse({'password_valid': True})
    else:
        return JsonResponse({'password_error': 'Password must be 8-20 characters long and must contain atleast one uppercase letter, one lowercase letter, one number(0-9) and one special character(@,#,$,%,&,_)'})
# AJAX Validations End Here