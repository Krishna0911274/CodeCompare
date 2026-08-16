from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect


# ============================================================
# REGISTER
# ============================================================

def register(request):

    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # -----------------------------
        # Validation
        # -----------------------------

        if not username or not email or not password:
            messages.error(
                request,
                "All fields are required."
            )

            return redirect("register")

        if password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )

            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(
                request,
                "Username already exists."
            )

            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(
                request,
                "Email already exists."
            )

            return redirect("register")

        # -----------------------------
        # Create User
        # -----------------------------

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # -----------------------------
        # Login after registration
        # -----------------------------

        login(request, user)

        return redirect("compiler")

    return render(
        request,
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("compiler")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("compiler")

        messages.error(
            request,
            "Invalid username or password."
        )

    return render(
        request,
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):

    logout(request)

    return redirect("login")