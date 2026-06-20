from tensorflow.keras.preprocessing.image import img_to_array
from django.shortcuts import render, redirect
from .models import *
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from PIL import ImageFile
import random
import re

from django.core.mail import send_mail


ImageFile.LOAD_TRUNCATED_IMAGES = True


# Create your views here.

from .models import Prediction, DiseasePrediction

def home(request):

    total_users = User.objects.filter(is_staff=False).count()

    total_predictions = Prediction.objects.count()

    total_detections = DiseasePrediction.objects.count()

    return render(
    request,
    "homepage.html",
    {
        "total_users": total_users,
        "total_predictions": total_predictions,
        "total_detections": total_detections,
    }
)

def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        email = request.POST.get("email").strip().lower()
        if not re.match(r'^[6-9]\d{9}$', phone):
            messages.error(
                request,
                "Enter a valid 10-digit mobile number"
            )
            return redirect("signup")
        password = request.POST.get("password")
        #basic validations
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")
        
        if not name or not email or not phone or not password:
            messages.error(request,"Please fill all required fields")
            return redirect("signup")
        
        if len(password) < 6:
            messages.error(request,"Password should be atleast 6 characters")
            return redirect("signup")
        
        if User.objects.filter(username__iexact=email).exists():
            messages.error(request,"Account already exists with this email")
            return redirect("signup")


        otp = random.randint(100000, 999999)
        request.session["signup_otp"] = str(otp)

        request.session["signup_name"] = name

        request.session["signup_phone"] = phone

        request.session["signup_email"] = email

        request.session["signup_password"] = password


        try:
            send_mail(
                subject="CropAI Email Verification",
                message=f"Your OTP is: {otp}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(
                request,
                "OTP sent to your email."
            )
            return redirect("verify_otp")
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending OTP email: {str(e)}\n{traceback.format_exc()}")
            messages.error(
                request,
                f"Failed to send verification email. Please check your SMTP settings. Error: {str(e)}"
            )
            return redirect("signup")

        #return redirect("home")
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



def verify_otp_view(request):

    if request.method == "POST":

        entered_otp = request.POST.get("otp", "").strip()

        saved_otp = request.session.get("signup_otp")

        if entered_otp == saved_otp:

            name = request.session.get("signup_name")
            phone = request.session.get("signup_phone")
            email = request.session.get("signup_email")
            password = request.session.get("signup_password")

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

            parts = name.split(" ", 1)

            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""

            user.save()

            UserProfile.objects.create(
                user=user,
                phone=phone
            )

            request.session.pop("signup_otp", None)
            request.session.pop("signup_name", None)
            request.session.pop("signup_phone", None)
            request.session.pop("signup_email", None)
            request.session.pop("signup_password", None)
            

            login(request, user)

            messages.success(
                request,
                "Account created successfully"
            )

            return redirect("home")

        else:

            messages.error(
                request,
                "Invalid OTP"
            )

    return render(
        request,
        "verify_otp.html"
    )
def logout_view(request):
    logout(request)
    messages.success(request,"Successfully Logged Out")
    return redirect("home")

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email").strip()
        password = request.POST.get("password")

        db_user = User.objects.filter(
            username__iexact=email
        ).first()

        if not db_user:
            messages.error(request, "Invalid login credentials")
            return redirect("login")

        user = authenticate(
            request,
            username=db_user.username,
            password=password
        )
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
        user = User.objects.filter(username__iexact=email).first()
        if not user:
            messages.error(request, "Email not registered")
            return redirect("forgot_password")

        # Generate OTP and store details in session
        otp = random.randint(100000, 999999)
        request.session["forgot_otp"] = str(otp)
        request.session["forgot_email"] = email
        request.session["forgot_password"] = new_password

        # Send OTP email
        try:
            send_mail(
                subject="CropAI Password Reset OTP",
                message=f"Your OTP for password reset is: {otp}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, "OTP sent to your email.")
            return redirect("verify_forgot_password_otp")
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error sending password reset OTP email: {str(e)}\n{traceback.format_exc()}")
            messages.error(
                request,
                f"Failed to send password reset email. Please check your settings. Error: {str(e)}"
            )
            return redirect("forgot_password")

    return render(request, "forgot_password.html")


def verify_forgot_password_otp_view(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()
        saved_otp = request.session.get("forgot_otp")
        email = request.session.get("forgot_email")
        new_password = request.session.get("forgot_password")

        if entered_otp == saved_otp and email and new_password:
            user = User.objects.filter(username__iexact=email).first()
            if user:
                user.set_password(new_password)
                user.save()
                
                # Clean up session
                request.session.pop("forgot_otp", None)
                request.session.pop("forgot_email", None)
                request.session.pop("forgot_password", None)
                
                messages.success(request, "Password reset successful. Please login.")
                return redirect("login")
            else:
                messages.error(request, "User not found")
                return redirect("forgot_password")
        else:
            messages.error(request, "Invalid OTP or session expired")
            return redirect("verify_forgot_password_otp")

    return render(request, "verify_otp.html")


def resend_otp_view(request):
    if "signup_email" in request.session:
        email = request.session.get("signup_email")
        otp = random.randint(100000, 999999)
        request.session["signup_otp"] = str(otp)
        try:
            send_mail(
                subject="CropAI Email Verification",
                message=f"Your OTP is: {otp}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, "OTP resent to your email.")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error resending OTP email: {str(e)}")
            messages.error(request, f"Failed to resend verification email: {str(e)}")
        return redirect("verify_otp")

    elif "forgot_email" in request.session:
        email = request.session.get("forgot_email")
        otp = random.randint(100000, 999999)
        request.session["forgot_otp"] = str(otp)
        try:
            send_mail(
                subject="CropAI Password Reset OTP",
                message=f"Your OTP for password reset is: {otp}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, "OTP resent to your email.")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error resending reset OTP email: {str(e)}")
            messages.error(request, f"Failed to resend verification email: {str(e)}")
        return redirect("verify_forgot_password_otp")

    else:
        messages.error(request, "Session expired or invalid request.")
        return redirect("signup")


def is_staff(user):
    return user.is_authenticated and user.is_staff

from django.db.models import Count
from django.utils import timezone
import json
from datetime import timedelta
def format_disease_name_helper(name):
    if "___" in name:
        parts = name.split("___")
        crop = parts[0].replace("_", " ").title()
        disease = parts[1].replace("_", " ").strip().title()
        return f"{crop} - {disease}"
    return name.replace("_", " ").title()

@user_passes_test(is_staff, login_url='admin_login')
def admin_dashboard_view(request):
   total_users = User.objects.filter(is_staff=False).count()
   total_predictions = Prediction.objects.count()
   total_detections = DiseasePrediction.objects.count()
   active_users = User.objects.filter(is_staff=False, is_active=True).count()
   blocked_users = User.objects.filter(is_staff=False, is_active=False).count()

   crop_qs = (
       Prediction.objects.values('predicted_crop')
       .annotate(c = Count('id'))
       .order_by('-c')[:5]
   )
   crop_labels = [i['predicted_crop'].title() for i in crop_qs]
   crop_counts = [i['c'] for i in crop_qs]

   # Disease detection distribution
   disease_qs = (
       DiseasePrediction.objects.values('disease_name')
       .annotate(c = Count('id'))
       .order_by('-c')[:5]
   )
   disease_labels = [format_disease_name_helper(i['disease_name']) for i in disease_qs]
   disease_counts = [i['c'] for i in disease_qs]

   today = timezone.localdate() #6,5,4,3,2,1,0
   days = [today - timedelta(days=i) for i in range(6,-1,-1)]

   day_labels = [d.strftime("%d %b") for d in days ] #29 3 2026 -> 29 Mar
   day_counts = [Prediction.objects.filter(created_at__date=d).count() for d in days ]

   context = {
       "total_users" : total_users,
       "total_predictions" : total_predictions,
       "total_detections" : total_detections,
       "active_users" : active_users,
       "blocked_users" : blocked_users,
       "crop_labels_json" : json.dumps(crop_labels),
       "crop_counts_json" : json.dumps(crop_counts),
       "disease_labels_json" : json.dumps(disease_labels),
       "disease_counts_json" : json.dumps(disease_counts),
       "day_labels_json" : json.dumps(day_labels),
       "day_counts_json" : json.dumps(day_counts),
   } 
   return render(request,"admin_dashboard.html",context)

@user_passes_test(is_staff, login_url='admin_login')
def admin_users_view(request):
    from django.utils import timezone
    from datetime import timedelta
    from recommender.models import Prediction
    
    one_month_ago = timezone.now() - timedelta(days=30)
    users = User.objects.filter(is_staff=False).select_related('userprofile')
    
    user_list = []
    for u in users:
        # Check if they have a prediction in the last month
        has_pred = Prediction.objects.filter(user=u, created_at__gte=one_month_ago).exists()
        u.is_active_last_month = has_pred
        user_list.append(u)
        
    return render(request,"admin_view_users.html",{"users": user_list})

@user_passes_test(is_staff, login_url='admin_login')
def admin_user_toggle_block(request, id):
    user = get_object_or_404(User, id=id)
    if user.is_active:
        user.is_active = False
        messages.success(request, f"User {user.get_full_name() or user.username} has been blocked.")
    else:
        user.is_active = True
        messages.success(request, f"User {user.get_full_name() or user.username} has been unblocked.")
    user.save()
    return redirect('admin_users_view')


@user_passes_test(is_staff, login_url='admin_login')
def admin_profile_view(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()

        # Phone validation
        if not re.match(r'^[6-9]\d{9}$', phone):
            messages.error(
                request,
                "Enter a valid 10-digit mobile number."
            )
            return redirect("admin_profile")

        parts = name.split(" ", 1)

        request.user.first_name = parts[0] if parts else ""
        request.user.last_name = parts[1] if len(parts) > 1 else ""

        profile.phone = phone

        request.user.save()
        profile.save()

        messages.success(
            request,
            "Profile updated successfully"
        )

        return redirect("admin_profile")

    return render(
        request,
        "admin_profile.html",
        {"profile": profile}
    )


from django.contrib.auth.decorators import login_required

@login_required
def user_disease_history(request):

    predictions = DiseasePrediction.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(
        request,
        'user_disease_history.html',
        {
            'predictions': predictions
        }
    )

@login_required
def delete_selected_detections(request):

    if request.method == "POST":

        ids = request.POST.getlist(
            "selected_detections"
        )

        DiseasePrediction.objects.filter(
            id__in=ids,
            user=request.user
        ).delete()

    return redirect("user_disease_history")


@login_required
def delete_selected_predictions(request):

    if request.method == "POST":

        ids = request.POST.getlist(
            "selected_predictions"
        )

        Prediction.objects.filter(
            id__in=ids,
            user=request.user
        ).delete()

        messages.success(
            request,
            f"{len(ids)} prediction(s) deleted successfully."
        )

    return redirect("user_history")



@user_passes_test(is_staff, login_url='admin_login')
def admin_user_delete(request,id):
    user = get_object_or_404(User, id=id)
    user.delete()
    messages.success(request,"User deleted")
    return redirect("admin_users_view")

from django.utils.dateparse import parse_date
from collections import defaultdict

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

    qs = qs.order_by('-created_at')

    grouped_predictions = defaultdict(list)

    for p in qs:
        grouped_predictions[p.user].append(p)

    crops = (
        Prediction.objects
        .order_by('predicted_crop')
        .values_list('predicted_crop', flat=True)
        .distinct()
    )

    context = {
        "qs": qs,
        "grouped_predictions": grouped_predictions.items(),
        "crops": crops,
        "current_crop": crop,
        "start": start,
        "end": end,
    }

    return render(
        request,
        "admin_view_predictions.html",
        context
    )

@user_passes_test(is_staff, login_url='admin_login')
def admin_delete_prediction(request,id):
    prediction = get_object_or_404(Prediction, id=id)
    prediction.delete()
    messages.success(request,"Prediction deleted")
    return redirect("admin_view_predictions")


def admin_logout_view(request):
    logout(request)
    messages.success(request,"Successfully Logged Out")
    return redirect("home")

@user_passes_test(is_staff, login_url='admin_login')
def admin_change_password_view(request):
    
    if request.method == "POST":
        current = request.POST.get("current_password")
        new = request.POST.get("new_password")
        confirm = request.POST.get("confirm_password")
        if not request.user.check_password(current):
            messages.error(request,"Current password is invalid")
            return redirect("admin_change_password")
        if len(new) < 6:
            messages.error(request,"New password must be atleast 6 characters")
            return redirect("admin_change_password")
        if new != confirm:
            messages.error(request,"New passwords does not match")
            return redirect("admin_change_password")
        if new == current:
            messages.error(request,"New password cannot be same as current password")
            return redirect("admin_change_password")
        request.user.set_password(new)
        request.user.save()
        user = authenticate(request,username=request.user.username,password=new)
        if user:
            login(request,user)
            messages.success(request,"Password Changed Successfully")
            return redirect("admin_change_password")
    return render(request,"admin_change_password.html",locals())


import tensorflow as tf
import numpy as np
from PIL import Image
import base64
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "MachineLearning" / "trained_model.keras"

MODEL = None

def get_model():
    global MODEL

    print("get_model() called")

    if MODEL is None:

        print("Loading model...")
        print("MODEL PATH:", MODEL_PATH)

        MODEL = tf.keras.models.load_model(
            MODEL_PATH,
            compile=False
        )

        print("Model loaded successfully")

    else:
        print("Using cached model")

    return MODEL

class_names = [

    "Apple___Apple_scab",
    "Apple___Black_rot",
    "Apple___Cedar_apple_rust",
    "Apple___healthy",

    "Blueberry___healthy",

    "Cherry_(including_sour)___Powdery_mildew",
    "Cherry_(including_sour)___healthy",

    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
    "Corn_(maize)___Common_rust_",
    "Corn_(maize)___Northern_Leaf_Blight",
    "Corn_(maize)___healthy",

    "Grape___Black_rot",
    "Grape___Esca_(Black_Measles)",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
    "Grape___healthy",

    "NonLeaf",

    "Orange___Haunglongbing_(Citrus_greening)",

    "Peach___Bacterial_spot",
    "Peach___healthy",

    "Pepper,_bell___Bacterial_spot",
    "Pepper,_bell___healthy",

    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy",

    "Raspberry___healthy",

    "Rice_Brown_Spot",
    "Rice_Hispa",
    "Rice_Leaf_Blast",
    "Rice_Healthy",

    "Soybean___healthy",

    "Squash___Powdery_mildew",

    "Strawberry___Leaf_scorch",
    "Strawberry___healthy",

    "Tomato___Bacterial_spot",
    "Tomato___Early_blight",
    "Tomato___Late_blight",
    "Tomato___Leaf_Mold",
    "Tomato___Septoria_leaf_spot",
    "Tomato___Spider_mites Two-spotted_spider_mite",
    "Tomato___Target_Spot",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato___Tomato_mosaic_virus",
    "Tomato___healthy"
]

advice_dict = {

    # Apple
    "Apple___Apple_scab": "Remove infected leaves and apply fungicide regularly.",
    "Apple___Black_rot": "Prune infected branches and destroy fallen leaves.",
    "Apple___Cedar_apple_rust": "Use resistant varieties and preventive fungicide sprays.",
    "Apple___healthy": "Plant is healthy. Maintain proper care.",

    # Blueberry
    "Blueberry___healthy": "Plant is healthy. Maintain proper soil conditions and watering.",

    # Cherry
    "Cherry_(including_sour)___Powdery_mildew": "Apply sulfur fungicide and improve airflow.",
    "Cherry_(including_sour)___healthy": "Plant is healthy. Continue monitoring.",

    # Corn
    "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot": "Use resistant hybrids and apply fungicide if needed.",
    "Corn_(maize)___Common_rust_": "Remove infected leaves and rotate crops.",
    "Corn_(maize)___Northern_Leaf_Blight": "Apply fungicide and maintain crop rotation.",
    "Corn_(maize)___healthy": "Corn plant is healthy. Maintain balanced nutrition.",

    # Grape
    "Grape___Black_rot": "Prune infected vines and apply fungicide regularly.",
    "Grape___Esca_(Black_Measles)": "Remove infected wood and avoid pruning wounds.",
    "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)": "Improve airflow and apply fungicide.",
    "Grape___healthy": "Grape plant is healthy. Maintain proper vineyard care.",

    # Non-leaf
    "NonLeaf": "Invalid input. Please upload a clear plant leaf image.",

    # Orange
    "Orange___Haunglongbing_(Citrus_greening)": "Control psyllids and remove infected trees.",

    # Peach
    "Peach___Bacterial_spot": "Use copper-based sprays and avoid overhead irrigation.",
    "Peach___healthy": "Peach plant is healthy. Maintain balanced fertilization.",

    # Pepper
    "Pepper,_bell___Bacterial_spot": "Use disease-free seeds and avoid leaf wetness.",
    "Pepper,_bell___healthy": "Pepper plant is healthy. Maintain proper irrigation.",

    # Potato
    "Potato___Early_blight": "Remove infected leaves and apply fungicide.",
    "Potato___Late_blight": "Destroy infected plants and improve drainage.",
    "Potato___healthy": "Potato plant is healthy. Maintain crop rotation.",

    # Raspberry
    "Raspberry___healthy": "Plant is healthy. Maintain proper care.",

    # Rice
    "Rice_Brown_Spot": "Use balanced fertilizer and remove infected leaves early.",
    "Rice_Hispa": "Use neem oil or recommended insecticides to control pests.",
    "Rice_Leaf_Blast": "Apply Tricyclazole fungicide and avoid excess nitrogen fertilizer.",
    "Rice_Healthy": "Rice crop is healthy. Maintain proper irrigation and field hygiene.",

    # Soybean
    "Soybean___healthy": "Soybean crop is healthy. Maintain proper soil nutrients.",

    # Squash
    "Squash___Powdery_mildew": "Apply sulfur-based fungicide and improve airflow.",

    # Strawberry
    "Strawberry___Leaf_scorch": "Remove infected leaves and avoid water stress.",
    "Strawberry___healthy": "Strawberry plant is healthy. Maintain proper care.",

    # Tomato
    "Tomato___Bacterial_spot": "Avoid overhead watering and use clean seeds.",
    "Tomato___Early_blight": "Remove infected leaves and apply fungicide.",
    "Tomato___Late_blight": "Destroy infected plants and improve spacing.",
    "Tomato___Leaf_Mold": "Reduce humidity and improve ventilation.",
    "Tomato___Septoria_leaf_spot": "Remove infected leaves and apply fungicide.",
    "Tomato___Spider_mites Two-spotted_spider_mite": "Use neem oil or insecticidal soap.",
    "Tomato___Target_Spot": "Maintain field hygiene and apply fungicides.",
    "Tomato___Tomato_Yellow_Leaf_Curl_Virus": "Control whiteflies and remove infected plants.",
    "Tomato___Tomato_mosaic_virus": "Disinfect tools and avoid contamination.",
    "Tomato___healthy": "Tomato plant is healthy. Continue regular monitoring.",

}



# detection history
from collections import defaultdict

@user_passes_test(is_staff, login_url='admin_login')
def admin_disease_history(request):

    predictions = DiseasePrediction.objects.select_related(
        'user'
    ).order_by('-created_at')

    grouped_predictions = defaultdict(list)

    for p in predictions:
        grouped_predictions[p.user].append(p)

    return render(
        request,
        'admin_disease_history.html',
        {
            'predictions': predictions,  # Desktop table
            'grouped_predictions': grouped_predictions.items()  # Mobile cards
        }
    )



# DETECTION VIEW
@login_required
def disease_detection_view(request):

    result = None
    display_result = None
    confidence = None
    advice = None
    image_data = None

    if request.method == "POST":

        image = request.FILES.get("image")

        if not image:
            messages.error(request, "Please select an image.")
            return redirect("disease_detection")

        if image.size > 5 * 1024 * 1024:
            messages.error(
                request,
                "Image too large. Please upload an image smaller than 5MB."
            )
            return redirect("disease_detection")
        print("Image Name:", image.name)
        print("Image Size:", round(image.size / 1024 / 1024, 2), "MB")

        if image:

            try:

                # preview
                image_data = base64.b64encode(image.read()).decode("utf-8")
                image.seek(0)

                img = Image.open(image)

                # Reduce huge camera photos first
                img.thumbnail((800, 800))

                img = img.convert("RGB")

                # Final model size
                img = img.resize((128, 128))

                # IMPORTANT: NO NORMALIZATION (matches training)
                img_array = img_to_array(img)
                img_array = img_array.astype("float32")
                img_array = np.expand_dims(img_array, axis=0)

                # predict
                print("=== DISEASE DETECTION STARTED ===")

                model = get_model()

                print("MODEL OBJECT:", model)

                if model is None:
                    raise Exception("Model failed to load")

                prediction = model.predict(img_array, verbose=0)[0]

                result_index = int(np.argmax(prediction))
                result = class_names[result_index]
                display_result = result.replace("___", " - ").replace("_", " ")

                confidence = float(prediction[result_index]) * 100

                print("PRED:", result)
                print("CONF:", confidence)

                # UNKNOWN DETECTION (FIXED)
                if confidence < 35:
                    result = "Unknown Image"
                    confidence = None
                    advice = None

                elif result == "NonLeaf":
                    result = "Non Leaf Image"
                    confidence = None
                    advice = "Please upload a plant leaf image only."
                    messages.error(
                            request,
                            "Non-leaf image detected. Upload a leaf image only."
                    )

                else:
                    confidence = round(confidence, 2)
                    advice = advice_dict.get(result, "No advice available")
                    print("========== SAVING ==========")
                    print("USER:", request.user.username)
                    print("DISEASE:", result)
                    print("CONFIDENCE:", confidence)
                    DiseasePrediction.objects.create(
                        user=request.user if request.user.is_authenticated else None,
                        disease_name=result,
                        confidence=confidence
                    )

            except Exception as e:
                import traceback

                print("=" * 80)
                traceback.print_exc()
                print("=" * 80)

                messages.error(request, str(e))

    return render(
        request,
        "disease_detection.html",
        {
            "result": result,
            "display_result": display_result,
            "confidence": confidence,
            "advice": advice,
            "image_data": image_data
        }
    )

# ==========================================
# ADMIN ANALYTICS & REPORTS
# ==========================================
@user_passes_test(is_staff, login_url='admin_login')
def admin_analytics_view(request):
   total_users = User.objects.filter(is_staff=False).count()
   total_predictions = Prediction.objects.count()
   total_detections = DiseasePrediction.objects.count()
   
   crop_qs = Prediction.objects.values('predicted_crop').annotate(c=Count('id')).order_by('-c')
   crop_labels = [i['predicted_crop'].title() for i in crop_qs]
   crop_counts = [i['c'] for i in crop_qs]
   
   disease_qs = DiseasePrediction.objects.values('disease_name').annotate(c=Count('id')).order_by('-c')
   disease_labels = [format_disease_name_helper(i['disease_name']) for i in disease_qs]
   disease_counts = [i['c'] for i in disease_qs]
   
   context = {
       "total_users": total_users,
       "total_predictions": total_predictions,
       "total_detections": total_detections,
       "crop_labels_json": json.dumps(crop_labels),
       "crop_counts_json": json.dumps(crop_counts),
       "disease_labels_json": json.dumps(disease_labels),
       "disease_counts_json": json.dumps(disease_counts),
   }
   return render(request, "admin_analytics.html", context)

from django.http import JsonResponse
from django.utils.timesince import timesince

@user_passes_test(is_staff, login_url='admin_login')
def admin_notifications_api(request):
    notifications = []
    
    recent_users = User.objects.filter(is_staff=False).order_by('-date_joined')[:3]
    recent_preds = Prediction.objects.select_related('user').order_by('-created_at')[:3]
    recent_detections = DiseasePrediction.objects.select_related('user').order_by('-created_at')[:3]
    
    for u in recent_users:
        notifications.append({
            'type': 'user',
            'title': 'New User Registered',
            'desc': f"{u.get_full_name() or u.username} joined.",
            'time': timesince(u.date_joined) + " ago",
            'timestamp': u.date_joined
        })
        
    for p in recent_preds:
        user_display = p.user.get_full_name() or p.user.username
        notifications.append({
            'type': 'prediction',
            'title': 'New Crop Prediction',
            'desc': f"{user_display} predicted crop: {p.predicted_crop.title()}.",
            'time': timesince(p.created_at) + " ago",
            'timestamp': p.created_at
        })
        
    for d in recent_detections:
        user_display = d.user.get_full_name() or d.user.username if d.user else 'Anonymous'
        notifications.append({
            'type': 'detection',
            'title': 'New Disease Detected',
            'desc': f"Pathology: {d.formatted_disease_name} ({d.confidence:.1f}%).",
            'time': timesince(d.created_at) + " ago",
            'timestamp': d.created_at
        })
        
    notifications.sort(key=lambda x: x['timestamp'], reverse=True)
    
    data = notifications[:5]
    return JsonResponse({
        'notifications': data,
        'count': len(data)
    })


@user_passes_test(is_staff, login_url='admin_login')
def admin_reports_view(request):
    recent_users = User.objects.filter(is_staff=False).order_by('-date_joined')[:5]
    recent_predictions = Prediction.objects.select_related('user').order_by('-created_at')[:5]
    recent_detections = DiseasePrediction.objects.select_related('user').order_by('-created_at')[:5]
    
    context = {
        'recent_users': recent_users,
        'recent_predictions': recent_predictions,
        'recent_detections': recent_detections,
    }
    return render(request, 'admin_reports.html', context)


import csv
from django.http import HttpResponse

@user_passes_test(is_staff, login_url='admin_login')
def export_users_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="users_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Username/Email', 'First Name', 'Last Name', 'Phone', 'Date Joined', 'Is Active'])
    
    users = User.objects.filter(is_staff=False).select_related('userprofile')
    for u in users:
        phone = u.userprofile.phone if hasattr(u, 'userprofile') else ''
        writer.writerow([u.id, u.username, u.first_name, u.last_name, phone, u.date_joined.strftime('%Y-%m-%d %H:%M'), u.is_active])
        
    return response


@user_passes_test(is_staff, login_url='admin_login')
def export_predictions_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="crop_predictions_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'User', 'N', 'P', 'K', 'Temp (C)', 'Humidity (%)', 'pH', 'Rainfall (mm)', 'Predicted Crop', 'Date'])
    
    predictions = Prediction.objects.select_related('user')
    for p in predictions:
        user_name = p.user.get_full_name() or p.user.username
        writer.writerow([p.id, user_name, p.N, p.P, p.K, p.temperature, p.humidity, p.ph, p.rainfall, p.predicted_crop, p.created_at.strftime('%Y-%m-%d %H:%M')])
        
    return response


@user_passes_test(is_staff, login_url='admin_login')
def export_detections_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="disease_detections_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'User', 'Disease Name', 'Confidence (%)', 'Date'])
    
    detections = DiseasePrediction.objects.select_related('user')
    for d in detections:
        user_name = d.user.get_full_name() or d.user.username if d.user else 'Anonymous'
        writer.writerow([d.id, user_name, d.disease_name, d.confidence, d.created_at.strftime('%Y-%m-%d %H:%M')])
        
    return response


import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def agri_ai_chat_api(request):
    query = request.GET.get("query", "").strip()
    if not query:
        return JsonResponse({"response": "Please enter a valid query."})

    # Call pollinations AI text API
    system_prompt = (
        "You are an expert agricultural AI assistant. Provide extremely helpful, accurate, and practical "
        "agricultural advice, crop recommendations, pest management tips, and soil improvement techniques. "
        "Use HTML tags (like <strong>, <br>, <ul>, <li>) for structured and beautiful formatting of your output."
    )
    
    try:
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            "model": "openai"
        }
        r = requests.post("https://text.pollinations.ai/", json=payload, timeout=8)
        if r.status_code == 200:
            ai_text = r.text
            import re
            # Simple markdown bold parser **text** -> <strong>text</strong>
            ai_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', ai_text)
            # If the response doesn't have HTML break tags, replace newlines with <br>
            if "<br>" not in ai_text and "<p>" not in ai_text:
                ai_text = ai_text.replace("\n", "<br>")
            return JsonResponse({"response": ai_text})
    except Exception:
        pass

    # Fallback keyword QA logic
    query_lower = query.lower()
    qa_db = [
        {
            "keys": ['npk', 'nitrogen', 'phosphorus', 'potassium', 'soil', 'fertility', 'ph level', 'ph'],
            "ans": "<strong>NPK</strong> stands for Nitrogen (N), Phosphorus (P), and Potassium (K) - the primary nutrients essential for plant growth:<br><br>"
                   "• <strong>Nitrogen (N)</strong>: Stimulates healthy vegetative growth and leaf greening. To boost naturally, apply composted manure, grow cover crops (like clover), or use blood meal.<br><br>"
                   "• <strong>Phosphorus (P)</strong>: Vital for strong root system development, flower blooming, and seed creation. To boost, apply bone meal, rock phosphate, or fish emulsion.<br><br>"
                   "• <strong>Potassium (K)</strong>: Regulates water balance, photosynthesis, and strengthens plant disease resistance. To boost, use potash, wood ash, or compost rich in banana peels.<br><br>"
                   "• <strong>Soil pH level</strong>: Most crops grow best in slightly acidic to neutral soils (pH 6.0 to 7.0). Use lime to raise pH (decrease acidity) and sulfur to lower pH (increase acidity)."
        },
        {
            "keys": ['crop', 'predict', 'recommend', 'ml', 'machine learning', 'predict crop', 'recommend crop'],
            "ans": "Our platform's <strong>Crop Recommendation tool</strong> uses a highly accurate Machine Learning model (Random Forest Classifier).<br><br>"
                   "It analyzes seven parameters: Nitrogen, Phosphorus, Potassium, Temperature, Relative Humidity, Soil pH, and Rainfall.<br><br>"
                   "Try it out from the <strong>Features > Crop Prediction</strong> menu!"
        },
        {
            "keys": ['disease', 'pathology', 'detect', 'leaf', 'scan', 'upload', 'trained_model', 'cnn', 'tensorflow'],
            "ans": "Our <strong>Plant Disease Detection tool</strong> uses a deep Convolutional Neural Network (CNN) trained on thousands of plant leaf images.<br><br>"
                   "1. Navigate to the <strong>Features > Disease Detection</strong> page.<br>"
                   "2. Upload a clear photograph of an infected leaf (up to 5MB, JPG/PNG format).<br>"
                   "3. The AI model evaluates spots and chlorosis, identifying the specific pathology with a confidence percentage, and recommends organic and chemical treatment advice."
        },
        {
            "keys": ['pest', 'pesticide', 'bug', 'insect', 'organic pesticide', 'neem oil', 'spider mite', 'aphid', 'beetle', 'caterpillar'],
            "ans": "Here are highly effective, organic recipes to manage common agricultural pests:<br><br>"
                   "• <strong>Neem Oil Spray</strong>: Mix 2 teaspoons of pure neem oil, 1 teaspoon of organic liquid dish soap, and 1 liter of warm water. Spray thoroughly on both sides of leaves in the evening.<br><br>"
                   "• <strong>Garlic-Chili Insecticide</strong>: Blend 2 heads of garlic and 3 hot peppers with 1 liter of water. Strain the mixture, add 1 teaspoon of liquid soap, and spray onto plants.<br><br>"
                   "• <strong>Cultural practices</strong>: Introduce beneficial insects (like ladybugs), practice companion planting (e.g. marigolds to deter nematodes), and maintain proper plant spacing."
        }
    ]

    matched_ans = ""
    max_matches = 0
    for item in qa_db:
        match_count = sum(1 for key in item["keys"] if key in query_lower)
        if match_count > max_matches:
            max_matches = match_count
            matched_ans = item["ans"]

    if not matched_ans:
        matched_ans = (
            "<strong>AgriAI Assistant (Offline Fallback)</strong><br><br>"
            "We could not reach our online AI models at this moment. Here is some general guidance:<br><br>"
            "• <strong>Soil Health</strong>: Maintain balanced N-P-K ratios and a soil pH of 6.0 to 7.0 for optimal crop growth.<br>"
            "• <strong>Pests and Disease</strong>: Spray neem oil for pest control and prune diseased leaves to halt infections.<br>"
            "• <strong>Crop Planning</strong>: Align crop choices with local climate seasons (Kharif for monsoon, Rabi for winter)."
        )

    return JsonResponse({"response": matched_ans})
