from .runner import execute


def compare_codes(
    language_a,
    code_a,
    language_b,
    code_b,
    user_input=""
):

    # ==========================================
    # Run Code A
    # ==========================================

    output_a, error_a, time_a, memory_a = execute(
        language_a,
        code_a,
        user_input
    )

    # ==========================================
    # Run Code B
    # ==========================================

    output_b, error_b, time_b, memory_b = execute(
        language_b,
        code_b,
        user_input
    )

    # ==========================================
    # Status
    # ==========================================

    status_a = "Success" if not error_a else "Error"
    status_b = "Success" if not error_b else "Error"

    # ==========================================
    # Compare Output
    # ==========================================

    same_output = (
        output_a.strip() == output_b.strip()
    )

    # ==========================================
    # Compare Execution Time
    # ==========================================

    faster = "Same"

    if time_a < time_b:
        faster = "A"

    elif time_b < time_a:
        faster = "B"

    # ==========================================
    # Compare Memory
    # ==========================================

    memory_winner = "Same"

    try:

        mem_a = float(memory_a)
        mem_b = float(memory_b)

        if mem_a < mem_b:
            memory_winner = "A"

        elif mem_b < mem_a:
            memory_winner = "B"

    except (ValueError, TypeError):

        memory_winner = "Same"

    # ==========================================
    # Return Result
    # ==========================================

    return {

        "code_a": {
            "language": language_a,
            "status": status_a,
            "output": output_a,
            "error": error_a,
            "execution_time": time_a,
            "memory_usage": memory_a,
        },

        "code_b": {
            "language": language_b,
            "status": status_b,
            "output": output_b,
            "error": error_b,
            "execution_time": time_b,
            "memory_usage": memory_b,
        },

        "comparison": {
            "same_output": same_output,
            "faster": faster,
            "memory_winner": memory_winner,
        },

    }