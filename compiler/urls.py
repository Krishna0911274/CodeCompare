from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", views.home, name="home"),
    path("compiler/", views.compiler, name="compiler"),
    path("compare/", views.compare_page, name="compare"),
    path("run/", views.run_code, name="run_code"),
    path("compare-code/", views.compare_view, name="compare_code"),
    path("save-code/", views.save_code, name="save_code"),
    path("history/",views.code_history,name="code_history"),
    path("open-code/<int:code_id>/",views.open_code,name="open_code"),
    path("delete-code/<int:code_id>/",views.delete_code,name="delete_code"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]