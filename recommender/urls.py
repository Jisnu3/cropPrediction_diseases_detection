
from django.urls import path
from .views import *  # * -> all
from . import views


urlpatterns = [
    path('',home,name='home'),
    path('signup/',signup_view,name='signup'),
    path('predict/',predict_view,name='predict'),
    path('logout/',logout_view,name='logout'),
    path('login/',login_view,name='login'),
    path('user_history/',user_history_view,name='user_history'),
    path('history_delete/<int:id>/',user_delete_prediction,name='user_delete_prediction'),
    path('profile/',profile_view,name='profile'),
    path('change_password/',change_password_view,name='change_password'),
    path('admin_login/',admin_login_view,name='admin_login'),
    path('admin_dashboard/',admin_dashboard_view,name='admin_dashboard'),
    path('admin_profile/',admin_profile_view,name='admin_profile'),
    path('admin_users_view/',admin_users_view,name='admin_users_view'),
    path('admin_user_delete/<int:id>/',admin_user_delete,name='admin_user_delete'),
    path('admin_user_toggle_block/<int:id>/',admin_user_toggle_block,name='admin_user_toggle_block'),
    path('admin_delete_prediction/<int:id>/',admin_delete_prediction,name='admin_delete_prediction'),
    path('admin_logout/',admin_logout_view,name='admin_logout'),
    path('admin_change_password/',admin_change_password_view,name='admin_change_password'),
    path('admin_view_predictions/',admin_view_predictions,name='admin_view_predictions'),
    path('admin_disease_history/',admin_disease_history,name='admin_disease_history'),
    path('admin_analytics/',admin_analytics_view,name='admin_analytics'),
    path('admin_reports/',admin_reports_view,name='admin_reports'),
    path('admin_notifications_api/', admin_notifications_api, name='admin_notifications_api'),
    path('admin_reports/export_users/',export_users_csv,name='export_users_csv'),
    path('admin_reports/export_predictions/',export_predictions_csv,name='export_predictions_csv'),
    path('admin_reports/export_detections/',export_detections_csv,name='export_detections_csv'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('disease_detection/',disease_detection_view,name='disease_detection'),
    path('detection-history/',views.user_disease_history,name='user_disease_history'),
    path("delete-selected-predictions/",views.delete_selected_predictions,name="delete_selected_predictions"),
    path("delete-selected-detections/",views.delete_selected_detections,name="delete_selected_detections"),
    path("verify-otp/",views.verify_otp_view,name="verify_otp"),
    path("verify-forgot-password-otp/",views.verify_forgot_password_otp_view,name="verify_forgot_password_otp"),
    path("resend-otp/", views.resend_otp_view, name="resend_otp"),
    path("api/chat/", agri_ai_chat_api, name="agri_ai_chat_api"),
]
