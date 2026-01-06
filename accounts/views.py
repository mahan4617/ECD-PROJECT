from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm
import random
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            user.profile.otp_code = otp
            user.profile.save()
            
            # Send Email
            try:
                print(f"DEBUG: EMAIL_HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}")
                print(f"Sending OTP to {user.email}...")
                email_message = f"""Hello {user.username},

Your One-Time Password (OTP) is: {otp}

This OTP is valid for 5 minutes.
Do not share this OTP with anyone.

Regards,
ECD Project Team."""
                
                send_mail(
                    'Your OTP Code',
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                print("Email sent successfully.")
                messages.success(request, f'OTP sent to {user.email}')
            except Exception as e:
                # In production handle this better, for now maybe just print or pass
                print(f"Error sending email: {e}")
                messages.error(request, f"Error sending email: {e}")
            
            # Store user ID in session
            request.session['pre_mfa_user_id'] = user.id
            return redirect('otp_verify')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

def otp_verify_view(request):
    user_id = request.session.get('pre_mfa_user_id')
    if not user_id:
        return redirect('login')
    
    if request.method == 'POST':
        otp = request.POST.get('otp')
        try:
            user = User.objects.get(id=user_id)
            if user.profile.otp_code == otp:
                login(request, user)
                if 'pre_mfa_user_id' in request.session:
                    del request.session['pre_mfa_user_id']
                user.profile.otp_code = None 
                user.profile.save()
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid OTP')
        except User.DoesNotExist:
            return redirect('login')
            
    return render(request, 'accounts/otp_verify.html')

def resend_otp_view(request):
    user_id = request.session.get('pre_mfa_user_id')
    if not user_id:
        return redirect('login')
    
    try:
        user = User.objects.get(id=user_id)
        
        # Generate new OTP
        otp = str(random.randint(100000, 999999))
        user.profile.otp_code = otp
        user.profile.save()
        
        # Send Email
        try:
            print(f"DEBUG: EMAIL_HOST={settings.EMAIL_HOST}, PORT={settings.EMAIL_PORT}")
            email_message = f"""Hello {user.username},

Your One-Time Password (OTP) is: {otp}

This OTP is valid for 5 minutes.
Do not share this OTP with anyone.

Regards,
ECD Project Team."""

            send_mail(
                'Your OTP Code',
                email_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            messages.success(request, f'New OTP sent to {user.email}')
        except Exception as e:
            messages.error(request, f"Error sending email: {e}")
            
    except User.DoesNotExist:
        return redirect('login')
        
    return redirect('otp_verify')

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('/accounts/login/')
