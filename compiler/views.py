from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

from .runner import execute
from .compare import compare_codes
from .models import SavedCode

import json
import traceback
import shutil


# ============================================================
# HOME
# ============================================================

def home(request):
    return render(request, "home.html")


# ============================================================
# COMPILER PAGE
# ============================================================

@login_required
def compiler(request):
    return render(request, "compiler.html")

@login_required
def compare_page(request):

    saved_code = None

    code_id = request.GET.get("code_id")

    if code_id:

        saved_code = SavedCode.objects.get(
            id=code_id,
            user=request.user,
            code_type="compare"
        )

    return render(
        request,
        "compiler.html",
        {
            "saved_code": saved_code,
        }
    )
# ============================================================
# RUN CODE API
# ============================================================

@login_required
def run_code(request):

    try:

        if request.method != "POST":
            return JsonResponse(
                {"error": "POST request required."},
                status=400
            )

        data = json.loads(request.body)

        language = data.get("language")
        code = data.get("code")
        user_input = data.get("input", "")

        print("=" * 50)
        print("Language:", language)
        print("Code:")
        print(code)
        print("=" * 50)

        print("G++ =", shutil.which("g++"))
        print("GCC =", shutil.which("gcc"))

        output, error, execution_time, memory_usage = execute(
            language,
            code,
            user_input
        )

        return JsonResponse({
            "output": output,
            "error": error,
            "execution_time": execution_time,
            "memory_usage": memory_usage,
        })

    except Exception:

        traceback.print_exc()

        return JsonResponse(
            {
                "error": traceback.format_exc()
            },
            status=500
        )


# ============================================================
# COMPARE CODE API
# ============================================================

@login_required
def compare_view(request):

    try:

        if request.method != "POST":
            return JsonResponse(
                {
                    "error": "POST request required."
                },
                status=400
            )

        data = json.loads(request.body)

        language_a = data.get("language_a")
        code_a = data.get("code_a", "")

        language_b = data.get("language_b")
        code_b = data.get("code_b", "")

        user_input = data.get("user_input", "")

        print("=" * 60)
        print("COMPARE REQUEST")
        print("=" * 60)

        print("Language A:", language_a)
        print("Language B:", language_b)

        print("\nCode A:")
        print(code_a)

        print("\nCode B:")
        print(code_b)

        print("\nInput:")
        print(user_input)

        print("=" * 60)

        if not language_a:
            return JsonResponse(
                {"error": "Language A is required."},
                status=400
            )

        if not language_b:
            return JsonResponse(
                {"error": "Language B is required."},
                status=400
            )

        if not code_a.strip():
            return JsonResponse(
                {"error": "Code A is empty."},
                status=400
            )

        if not code_b.strip():
            return JsonResponse(
                {"error": "Code B is empty."},
                status=400
            )

        result = compare_codes(
            language_a,
            code_a,
            language_b,
            code_b,
            user_input
        )

        print("\nCOMPARE RESULT:")
        print(result)

        return JsonResponse(result)

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "error": "Invalid JSON request."
            },
            status=400
        )

    except Exception:

        traceback.print_exc()

        return JsonResponse(
            {
                "error": traceback.format_exc()
            },
            status=500
        )

# ============================================================
# HISTORY CODE METHODES STARTS
# ============================================================
@login_required
def save_code(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "POST request required."},
            status=400
        )

    try:
        data = json.loads(request.body)

        # -----------------------------------------
        # Basic data
        # -----------------------------------------

        code_id = data.get("code_id")
        title = data.get("title", "").strip()

        code_type = data.get("code_type", "single")

        language = data.get("language", "").strip()
        code = data.get("code", "")

        language_b = data.get("language_b", "").strip()
        code_b = data.get("code_b", "")

        # -----------------------------------------
        # Validation
        # -----------------------------------------

        if not code.strip():
            return JsonResponse(
                {"error": "Code cannot be empty."},
                status=400
            )

        if code_type == "compare" and not code_b.strip():
            return JsonResponse(
                {"error": "Code B cannot be empty."},
                status=400
            )

        # =================================================
        # UPDATE EXISTING SAVED CODE
        # =================================================

        if code_id:

            try:
                saved_code = SavedCode.objects.get(
                    id=code_id,
                    user=request.user
                )

            except SavedCode.DoesNotExist:
                return JsonResponse(
                    {"error": "Saved code not found."},
                    status=404
                )

            saved_code.code_type = code_type
            saved_code.language = language
            saved_code.code = code
            saved_code.language_b = language_b
            saved_code.code_b = code_b

            saved_code.save()

            return JsonResponse({
                "success": True,
                "updated": True,
                "message": "Your saved code was updated.",
                "id": saved_code.id
            })

        # =================================================
        # CREATE NEW SAVED CODE
        # =================================================

        if not title:
            return JsonResponse(
                {"error": "Title is required."},
                status=400
            )

        saved_code = SavedCode.objects.create(
            user=request.user,
            title=title,
            code_type=code_type,
            language=language,
            code=code,
            language_b=language_b,
            code_b=code_b
        )

        return JsonResponse({
            "success": True,
            "updated": False,
            "message": "Code saved successfully.",
            "id": saved_code.id
        })

    except json.JSONDecodeError:

        return JsonResponse(
            {"error": "Invalid JSON."},
            status=400
        )

    except Exception as e:

        return JsonResponse(
            {"error": str(e)},
            status=500
        )
                     
@login_required
def code_history(request):

    codes = SavedCode.objects.filter(
        user=request.user
    ).order_by("-created_at")

    return render(
        request,
        "history.html",
        {
            "codes": codes
        }
    )

@login_required
def open_code(request, code_id):

    code = SavedCode.objects.get(
        id=code_id,
        user=request.user
    )

    if code.code_type == "compare":

        return redirect(
            f"/compare/?code_id={code.id}"
        )

    return render(
        request,
        "compiler.html",
        {
            "saved_code": code,
        }
    )
       
@login_required
def delete_code(request, code_id):

    if request.method == "POST":

        code = SavedCode.objects.get(
            id=code_id,
            user=request.user
        )

        code.delete()

    return redirect("code_history")

# ============================================================
# HISTORY CODE METHODES ENDS
# ============================================================