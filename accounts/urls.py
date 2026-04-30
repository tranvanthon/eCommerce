from django.urls import path, include
from accounts import views
from accounts import views as accounts_view
from django.contrib.auth import views as auth_views

urlpatterns = [
    path(
        "password/reset/",
        accounts_view.CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "password/reset/done/",
        auth_views.PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path(
        "password/change/done/",
        auth_views.PasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path("login/", accounts_view.LoginCustomView.as_view(), name="account_login"),
    path("signup/", accounts_view.SignupView.as_view(), name="account_signup"),
    path("logout/", accounts_view.logout_view, name="account_logout"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"),
    path("profile/upload-avatar/", views.upload_avatar, name="upload_avatar"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("staff-dashboard/", views.staff_dashboard, name="staff_dashboard"),
    path("customer-dashboard/", views.customer_dashboard, name="customer_dashboard"),
    path("", include("allauth.urls")),
]
