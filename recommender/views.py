from django.shortcuts import render, redirect
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User 
# Create your views here.

def home(request):
    total_users = User.objects.filter(is_staff=False).count()
    total_predictions = Prediction.objects.count()
    return render(request,"homepage.html",locals())

def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email")
        password = request.POST.get("password")
        #basic validations
        if not name or not email or not phone or not password:
            messages.error(request,"Please fill all required fields")
            return redirect("signup")
        
        if len(password) < 6:
            messages.error(request,"Password should be atleast 6 characters")
            return redirect("signup")
        
        if User.objects.filter(username=email):
            messages.error(request,"Account already exists with this email")
            return redirect("signup")
    
        user = User.objects.create_user(username=email,password=password)
        if " " in name:
            first, last = name.split(" ",1)
        else:
            first, last = name, ""
        user.first_name, user.last_name = first, last
        user.save()

        UserProfile.objects.create(user=user, phone=phone)
        login(request,user)
        messages.success(request,"Account created successfully. Welcome!")
        return redirect("home")
    return render(request,"signup.html")

from .MachineLearning.loader import predict_one, load_bundle
from django.contrib.auth.decorators import login_required, user_passes_test
@login_required
def predict_view(request):
    feature_order = load_bundle()["feature_collumns"]
    result = None
    last_data = None

    if request.method == "POST":
        data = {}
        try:
            for c in feature_order:
                data[c] = float(request.POST.get(c))
        except ValueError:
            messages.error(request,"Please enter valid numeric values")
            return redirect("predict")
        label = predict_one(data)

        Prediction.objects.create(user=request.user,**data,predicted_crop=label)
        #**data kwargs/dictionary unpacking
        result = label
        last_data = data
        messages.success(request,f"Recommended Crop: {label}")

    return render(request,"predict.html",locals())

def logout_view(request):
    logout(request)
    messages.success(request,"Successfully Logged Out")
    return redirect("login")

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request,username=username,password=password)
        if not user:
            messages.error(request,"Invalid login credentials")
            return redirect("login")
        login(request,user)
        messages.success(request,"Succesfully Logged In")
        return redirect("home")
    return render(request,"login.html")


@login_required
def user_history_view(request):
    predictions = Prediction.objects.filter(user=request.user)
    return render(request,"history.html",locals())

from django.shortcuts import get_object_or_404
@login_required
def user_delete_prediction(request,id):
    prediction = get_object_or_404(Prediction, id=id, user=request.user)
    prediction.delete()
    messages.success(request,"Record removed from history")
    return redirect("user_history")

@login_required
def profile_view(request):
    profile = UserProfile.objects.get(user=request.user)
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        if name:
            parts = name.split(" ",1)
            request.user.first_name = parts[0]
            request.user.last_name = parts[1] if len(parts) > 1 else ""
        profile.phone = phone
        request.user.save()
        profile.save()
        messages.success(request,"Profile updated succesfully")
    full_name = request.user.get_full_name()
    return render(request,"profile.html",locals())

@login_required
def change_password_view(request):
    
    if request.method == "POST":
        current = request.POST.get("current_password")
        new = request.POST.get("new_password")
        confirm = request.POST.get("confirm_password")
        if not request.user.check_password(current):
            messages.error(request,"Current password is invalid")
            return redirect("change_password")
        if len(new) < 6:
            messages.error(request,"New password must be atleast 6 characters")
            return redirect("change_password")
        if new != confirm:
            messages.error(request,"New passwords does not match")
            return redirect("change_password")
        if new == current:
            messages.error(request,"New password cannot be same as current password")
            return redirect("change_password")
        request.user.set_password(new)
        request.user.save()
        user = authenticate(request,username=request.user.username,password=new)
        if user:
            login(request,user)
            messages.success(request,"Password Changed Successfully")
            return redirect("change_password")
    return render(request,"change_password.html",locals())

def admin_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request,username=username,password=password)
        if not user:
            messages.error(request,"Invalid login credentials")
            return redirect("admin_login")
        if not user.is_staff:
            messages.error(request,"You do not have admin privileges")
            return redirect("admin_login")
        login(request,user)
        messages.success(request,"Succesfully Logged In")
        return redirect("admin_dashboard")
    return render(request,"admin_login.html")



def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        new_password = request.POST.get("new_password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        # Email validation
        if not email:
            messages.error(request, "Email is required")
            return redirect("forgot_password")

        # Password validation
        if not new_password or not confirm_password:
            messages.error(request, "All password fields are required")
            return redirect("forgot_password")

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("forgot_password")

        if len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters")
            return redirect("forgot_password")

        # Check user
        user = User.objects.filter(username=email).first()
        if not user:
            messages.error(request, "Email not registered")
            return redirect("forgot_password")

        # Update password
        user.set_password(new_password)
        user.save()

        messages.success(request, "Password reset successful. Please login.")
        return redirect("login")

    return render(request, "forgot_password.html")


def is_staff(user):
    return user.is_authenticated and user.is_staff

from django.db.models import Count
from django.utils import timezone
import json
from datetime import timedelta
@user_passes_test(is_staff, login_url='admin_login')
def admin_dashboard_view(request):
   total_users = User.objects.filter(is_staff=False).count()
   total_predictions = Prediction.objects.count()

   crop_qs = (
       Prediction.objects.values('predicted_crop')
       .annotate(c = Count('id'))
       .order_by('-c')[:10]
   )
   crop_labels = [i['predicted_crop'].title() for i in crop_qs]
   crop_counts = [i['c'] for i in crop_qs]

   today = timezone.localdate() #6,5,4,3,2,1,0
   days = [today - timedelta(days=i) for i in range(6,-1,-1)]

   day_labels = [d.strftime("%d %b") for d in days ] #29 3 2026 -> 29 Mar
   day_counts = [Prediction.objects.filter(created_at__date=d).count() for d in days ]

   context = {
       "total_users" : total_users,
       "total_predictions" : total_predictions,
       "crop_labels_json" : json.dumps(crop_labels),
       "crop_counts_json" : json.dumps(crop_counts),
       "day_labels_json" : json.dumps(day_labels),
       "day_counts_json" : json.dumps(day_counts),

   } 
   return render(request,"admin_dashboard.html",context)

def admin_users_view(request):
   users = User.objects.filter(is_staff=False)
   return render(request,"admin_view_users.html",{"users":users})

@user_passes_test(is_staff, login_url='admin_login')
def admin_user_delete(request,id):
    user = get_object_or_404(User, id=id)
    user.delete()
    messages.success(request,"User deleted")
    return redirect("admin_users_view")

from django.utils.dateparse import parse_date
@user_passes_test(is_staff, login_url='admin_login')
def admin_view_predictions(request):
    qs = Prediction.objects.select_related('user')

    crop = request.GET.get('crop')
    start = request.GET.get('start')
    end = request.GET.get('end')

    if crop:
        qs = qs.filter(predicted_crop__iexact=crop)

    d_start = parse_date(start) if start else None
    d_end = parse_date(end) if end else None

    if d_start:
        qs = qs.filter(created_at__date__gte=d_start)

    if d_end:
        qs = qs.filter(created_at__date__lte=d_end)

    crops = (Prediction.objects
             .order_by('predicted_crop')
             .values_list('predicted_crop',flat=True)
             .distinct())
    context = {
       "qs" : qs,
       "crops" : crops,
       "current_crop" : crop,
       "start" : start,
       "end" : end,

   } 
    return render(request,"admin_view_predictions.html",context)

@user_passes_test(is_staff, login_url='admin_login')
def admin_delete_prediction(request,id):
    prediction = get_object_or_404(Prediction, id=id)
    prediction.delete()
    messages.success(request,"Prediction deleted")
    return redirect("admin_view_predictions")


def admin_logout_view(request):
    logout(request)
    messages.success(request,"Successfully Logged Out")
    return redirect("admin_login")

@user_passes_test(is_staff, login_url='admin_login')
def admin_change_password_view(request):
    
    if request.method == "POST":
        current = request.POST.get("current_password")
        new = request.POST.get("new_password")
        confirm = request.POST.get("confirm_password")
        if not request.user.check_password(current):
            messages.error(request,"Current password is invalid")
            return redirect("change_password")
        if len(new) < 6:
            messages.error(request,"New password must be atleast 6 characters")
            return redirect("change_password")
        if new != confirm:
            messages.error(request,"New passwords does not match")
            return redirect("change_password")
        if new == current:
            messages.error(request,"New password cannot be same as current password")
            return redirect("change_password")
        request.user.set_password(new)
        request.user.save()
        user = authenticate(request,username=request.user.username,password=new)
        if user:
            login(request,user)
            messages.success(request,"Password Changed Successfully")
            return redirect("change_password")
    return render(request,"change_password.html",locals())