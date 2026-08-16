import subprocess
import uuid
import os
import shutil
import time

TEMP_DIR = "temp"

os.makedirs(TEMP_DIR, exist_ok=True)

def docker_security_options():
    return [
        "--rm",
        "--network", "none",
        "--memory", "128m",
        "--cpus", "1",
        "--pids-limit", "50",
        "--cgroupns", "private",
    ]
    
def get_docker_peak_memory(container_name):
    try:
        result = subprocess.run(
            [
                "docker",
                "exec",
                container_name,
                "cat",
                "/sys/fs/cgroup/memory.peak",
            ],
            capture_output=True,
            text=True,
            timeout=2,
        )

        if result.returncode != 0:
            return "N/A"

        # memory.peak is returned in bytes
        memory_bytes = int(result.stdout.strip())

        memory_mb = memory_bytes / (1024 * 1024)

        return f"{memory_mb:.2f} MB"

    except Exception as e:
        print("Memory error:", e)
        return "N/A"
    
# Function to run Python code in a temporary file
def run_python(code, user_input=""):
    filename = f"{uuid.uuid4().hex}.py"
    filepath = os.path.abspath(os.path.join(TEMP_DIR, filename))

    memory_file = os.path.abspath(
        os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}_memory.txt")
    )

    time_file = os.path.abspath(
        os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}_time.txt")
    )

    container_name = f"codecompare-python-{uuid.uuid4().hex[:8]}"

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        security_options = docker_security_options()
        security_options = [o for o in security_options if o != "--rm"]

        memory_filename = os.path.basename(memory_file)
        time_filename = os.path.basename(time_file)

        command = [
            "docker",
            "run",
            "--name",
            container_name,
            "-i",
            *security_options,

            "-v",
            f"{os.path.abspath(TEMP_DIR)}:/code",

            "codecompare-python",

            "sh",
            "-c",

            (
                f"START=$(date +%s%N); "
                f"python /code/{filename}; "
                f"STATUS=$?; "
                f"END=$(date +%s%N); "
                f"echo $(( (END-START)/1000000 )) > /code/{time_filename}; "
                f"cat /sys/fs/cgroup/memory.peak > /code/{memory_filename}; "
                f"exit $STATUS"
            ),
        ]

        result = subprocess.run(
            command,
            input=user_input,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # --------------------------------
        # Read execution time (in-container)
        # --------------------------------

        execution_time = 0

        if os.path.exists(time_file):
            try:
                with open(time_file, "r") as f:
                    execution_time = int(f.read().strip())
            except Exception as e:
                print("Time read error:", e)

        # --------------------------------
        # Read peak memory
        # --------------------------------

        memory_usage = "N/A"

        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r") as f:
                    memory_bytes = int(f.read().strip())

                memory_mb = memory_bytes / (1024 * 1024)
                memory_usage = f"{memory_mb:.2f} MB"

            except Exception as e:
                print("Memory read error:", e)

        return (result.stdout, result.stderr, execution_time, memory_usage)

    except subprocess.TimeoutExpired:
        return ("", "Execution timed out.", 0, "N/A")

    except Exception as e:
        return ("", str(e), 0, "N/A")

    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            text=True,
        )

        if os.path.exists(filepath):
            os.remove(filepath)

        if os.path.exists(memory_file):
            os.remove(memory_file)

        if os.path.exists(time_file):
            os.remove(time_file)
            
# Function to run Java code in a temporary directory
def run_java(code, user_input=""):
    java_dir = os.path.join(TEMP_DIR, "java")
    os.makedirs(java_dir, exist_ok=True)

    filepath = os.path.join(java_dir, "Main.java")

    memory_file = os.path.join(
        java_dir,
        f"{uuid.uuid4().hex}_memory.txt"
    )

    time_file = os.path.join(
        java_dir,
        f"{uuid.uuid4().hex}_time.txt"
    )

    container_name = f"codecompare-java-{uuid.uuid4().hex[:8]}"

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        # =========================
        # Compile Java inside Docker (not timed as execution)
        # =========================

        compile_command = [
            "docker",
            "run",
        ]

        compile_command.extend(docker_security_options())

        compile_command.extend([
            "-v",
            f"{os.path.abspath(java_dir)}:/code",
            "codecompare-java",
            "javac",
            "/code/Main.java",
        ])

        compile_result = subprocess.run(
            compile_command,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if compile_result.returncode != 0:
            return (
                "",
                compile_result.stderr,
                0,
                "N/A",
            )

        # =========================
        # Run Java inside Docker
        # =========================

        security_options = docker_security_options()
        security_options = [
            option
            for option in security_options
            if option != "--rm"
        ]

        memory_filename = os.path.basename(memory_file)
        time_filename = os.path.basename(time_file)

        run_command = [
            "docker",
            "run",
            "--name",
            container_name,
            "-i",
            *security_options,

            "-v",
            f"{os.path.abspath(java_dir)}:/code",

            "codecompare-java",

            "sh",
            "-c",

            (
                f"START=$(date +%s%N); "
                f"java -cp /code Main; "
                f"STATUS=$?; "
                f"END=$(date +%s%N); "
                f"echo $(( (END-START)/1000000 )) > /code/{time_filename}; "
                f"cat /sys/fs/cgroup/memory.peak > /code/{memory_filename}; "
                f"exit $STATUS"
            ),
        ]

        run_result = subprocess.run(
            run_command,
            input=user_input,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # =========================
        # Read execution time (in-container)
        # =========================

        execution_time = 0

        if os.path.exists(time_file):
            try:
                with open(time_file, "r") as f:
                    execution_time = int(f.read().strip())
            except Exception as e:
                print("Java time read error:", e)

        # =========================
        # Read peak memory
        # =========================

        memory_usage = "N/A"

        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r") as f:
                    memory_bytes = int(f.read().strip())

                memory_mb = memory_bytes / (1024 * 1024)
                memory_usage = f"{memory_mb:.2f} MB"

            except Exception as e:
                print("Java memory read error:", e)

        return (
            run_result.stdout,
            run_result.stderr,
            execution_time,
            memory_usage,
        )

    except subprocess.TimeoutExpired:
        return ("", "Execution timed out.", 0, "N/A")

    except Exception as e:
        return ("", str(e), 0, "N/A")

    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            text=True,
        )

        if os.path.exists(filepath):
            os.remove(filepath)

        if os.path.exists(memory_file):
            os.remove(memory_file)

        if os.path.exists(time_file):
            os.remove(time_file)

        class_file = os.path.join(java_dir, "Main.class")
        if os.path.exists(class_file):
            os.remove(class_file)
# Function to run C code in a temporary file
def run_c(code, user_input=""):
    filename = uuid.uuid4().hex

    c_file = os.path.join(TEMP_DIR, filename + ".c")
    exe_file = os.path.join(TEMP_DIR, filename)
    memory_file = os.path.join(TEMP_DIR, filename + "_memory.txt")
    time_file = os.path.join(TEMP_DIR, filename + "_time.txt")

    container_name = f"codecompare-c-{uuid.uuid4().hex[:8]}"

    try:
        with open(c_file, "w", encoding="utf-8") as f:
            f.write(code)

        # -------------------------
        # Compile inside Docker (not timed as execution)
        # -------------------------
        compile_command = [
            "docker",
            "run",
        ]

        compile_command.extend(docker_security_options())

        compile_command.extend([
            "-v",
            f"{os.path.abspath(TEMP_DIR)}:/code",
            "codecompare-c",
            "gcc",
            f"/code/{filename}.c",
            "-o",
            f"/code/{filename}",
        ])

        compile_result = subprocess.run(
            compile_command,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if compile_result.returncode != 0:
            return (
                "",
                compile_result.stderr,
                0,
                "N/A",
            )

        # -------------------------
        # Run C program inside Docker
        # -------------------------

        security_options = docker_security_options()
        security_options = [
            option
            for option in security_options
            if option != "--rm"
        ]

        memory_filename = os.path.basename(memory_file)
        time_filename = os.path.basename(time_file)

        run_command = [
            "docker",
            "run",
            "--name",
            container_name,
            "-i",
            *security_options,

            "-v",
            f"{os.path.abspath(TEMP_DIR)}:/code",

            "codecompare-c",

            "sh",
            "-c",

            (
                f"START=$(date +%s%N); "
                f"/code/{filename}; "
                f"STATUS=$?; "
                f"END=$(date +%s%N); "
                f"echo $(( (END-START)/1000000 )) > /code/{time_filename}; "
                f"cat /sys/fs/cgroup/memory.peak > /code/{memory_filename}; "
                f"exit $STATUS"
            ),
        ]

        run_result = subprocess.run(
            run_command,
            input=user_input,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # -------------------------
        # Read execution time (in-container)
        # -------------------------

        execution_time = 0

        if os.path.exists(time_file):
            try:
                with open(time_file, "r") as f:
                    execution_time = int(f.read().strip())
            except Exception as e:
                print("C time read error:", e)

        # -------------------------
        # Read peak memory
        # -------------------------

        memory_usage = "N/A"

        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r") as f:
                    memory_bytes = int(f.read().strip())

                memory_mb = memory_bytes / (1024 * 1024)
                memory_usage = f"{memory_mb:.2f} MB"

            except Exception as e:
                print("C memory read error:", e)

        return (
            run_result.stdout,
            run_result.stderr,
            execution_time,
            memory_usage,
        )

    except subprocess.TimeoutExpired:
        return ("", "Execution timed out.", 0, "N/A")

    except Exception as e:
        return ("", str(e), 0, "N/A")

    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            text=True,
        )

        if os.path.exists(c_file):
            os.remove(c_file)

        if os.path.exists(exe_file):
            os.remove(exe_file)

        if os.path.exists(memory_file):
            os.remove(memory_file)

        if os.path.exists(time_file):
            os.remove(time_file)

def run_cpp(code, user_input=""):
    filename = uuid.uuid4().hex

    cpp_file = os.path.join(TEMP_DIR, filename + ".cpp")
    exe_file = os.path.join(TEMP_DIR, filename)
    memory_file = os.path.join(TEMP_DIR, filename + "_memory.txt")
    time_file = os.path.join(TEMP_DIR, filename + "_time.txt")

    container_name = f"codecompare-cpp-{uuid.uuid4().hex[:8]}"

    try:
        with open(cpp_file, "w", encoding="utf-8") as f:
            f.write(code)

        # =========================
        # Compile C++ inside Docker (not timed as execution)
        # =========================

        compile_command = [
            "docker",
            "run",
        ]

        compile_command.extend(docker_security_options())

        compile_command.extend([
            "-v",
            f"{os.path.abspath(TEMP_DIR)}:/code",
            "codecompare-cpp",
            "g++",
            f"/code/{filename}.cpp",
            "-o",
            f"/code/{filename}",
        ])

        compile_result = subprocess.run(
            compile_command,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if compile_result.returncode != 0:
            return (
                "",
                compile_result.stderr,
                0,
                "N/A",
            )

        # =========================
        # Run C++ inside Docker
        # =========================

        security_options = docker_security_options()
        security_options = [
            option
            for option in security_options
            if option != "--rm"
        ]

        memory_filename = os.path.basename(memory_file)
        time_filename = os.path.basename(time_file)

        run_command = [
            "docker",
            "run",
            "--name",
            container_name,
            "-i",
            *security_options,

            "-v",
            f"{os.path.abspath(TEMP_DIR)}:/code",

            "codecompare-cpp",

            "sh",
            "-c",
            (
                f"START=$(date +%s%N); "
                f"/code/{filename}; "
                f"STATUS=$?; "
                f"END=$(date +%s%N); "
                f"echo $(( (END-START)/1000000 )) > /code/{time_filename}; "
                f"cat /sys/fs/cgroup/memory.peak > /code/{memory_filename}; "
                f"exit $STATUS"
            ),
        ]

        run_result = subprocess.run(
            run_command,
            input=user_input,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # =========================
        # Read execution time (in-container)
        # =========================

        execution_time = 0

        if os.path.exists(time_file):
            try:
                with open(time_file, "r") as f:
                    execution_time = int(f.read().strip())
            except Exception as e:
                print("C++ time read error:", e)

        # =========================
        # Read peak memory
        # =========================

        memory_usage = "N/A"

        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r") as f:
                    memory_bytes = int(f.read().strip())

                memory_mb = memory_bytes / (1024 * 1024)
                memory_usage = f"{memory_mb:.2f} MB"

            except Exception as e:
                print("C++ memory read error:", e)

        return (
            run_result.stdout,
            run_result.stderr,
            execution_time,
            memory_usage,
        )

    except subprocess.TimeoutExpired:
        return ("", "Execution timed out.", 0, "N/A")

    except Exception as e:
        return ("", str(e), 0, "N/A")

    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            text=True,
        )

        if os.path.exists(cpp_file):
            os.remove(cpp_file)

        if os.path.exists(exe_file):
            os.remove(exe_file)

        if os.path.exists(memory_file):
            os.remove(memory_file)

        if os.path.exists(time_file):
            os.remove(time_file)
            
                        
# Function to run JavaScript code using Node.js
def run_javascript(code, user_input=""):
    filename = f"{uuid.uuid4().hex}.js"
    filepath = os.path.join(TEMP_DIR, filename)

    memory_file = os.path.join(
        TEMP_DIR,
        f"{uuid.uuid4().hex}_memory.txt"
    )

    time_file = os.path.join(
        TEMP_DIR,
        f"{uuid.uuid4().hex}_time.txt"
    )

    container_name = f"codecompare-javascript-{uuid.uuid4().hex[:8]}"

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)

        # =========================
        # Run JavaScript in Docker
        # =========================

        security_options = docker_security_options()
        security_options = [
            option
            for option in security_options
            if option != "--rm"
        ]

        memory_filename = os.path.basename(memory_file)
        time_filename = os.path.basename(time_file)

        docker_command = [
            "docker",
            "run",
            "--name",
            container_name,
            "-i",
            *security_options,

            "-v",
            f"{os.path.abspath(TEMP_DIR)}:/code",

            "codecompare-javascript",

            "sh",
            "-c",

            (
                f"START=$(date +%s%N); "
                f"node /code/{filename}; "
                f"STATUS=$?; "
                f"END=$(date +%s%N); "
                f"echo $(( (END-START)/1000000 )) > /code/{time_filename}; "
                f"cat /sys/fs/cgroup/memory.peak > /code/{memory_filename}; "
                f"exit $STATUS"
            ),
        ]

        result = subprocess.run(
            docker_command,
            input=user_input,
            capture_output=True,
            text=True,
            timeout=5,
        )

        # =========================
        # Read execution time (in-container)
        # =========================

        execution_time = 0

        if os.path.exists(time_file):
            try:
                with open(time_file, "r") as f:
                    execution_time = int(f.read().strip())
            except Exception as e:
                print("JavaScript time read error:", e)

        # =========================
        # Read peak memory
        # =========================

        memory_usage = "N/A"

        if os.path.exists(memory_file):
            try:
                with open(memory_file, "r") as f:
                    memory_bytes = int(f.read().strip())

                memory_mb = memory_bytes / (1024 * 1024)
                memory_usage = f"{memory_mb:.2f} MB"

            except Exception as e:
                print("JavaScript memory read error:", e)

        return (
            result.stdout,
            result.stderr,
            execution_time,
            memory_usage,
        )

    except subprocess.TimeoutExpired:
        return ("", "Execution timed out.", 0, "N/A")

    except Exception as e:
        return ("", str(e), 0, "N/A")

    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            text=True,
        )

        if os.path.exists(filepath):
            os.remove(filepath)

        if os.path.exists(memory_file):
            os.remove(memory_file)

        if os.path.exists(time_file):
            os.remove(time_file)   
# Dispatcher function to call the appropriate language runner
def execute(language, code, user_input=""):
    
    if language == "python":
        result = run_python(code, user_input)

    elif language == "java":
        result = run_java(code, user_input)

    elif language == "cpp":
        result = run_cpp(code, user_input)

    elif language == "c":
        result = run_c(code, user_input)

    elif language == "javascript":
        result = run_javascript(code, user_input)

    else:
        return "", "Language not supported.", 0, "N/A"

    if len(result) == 4:
        return result

    if len(result) == 3:
        output, error, execution_time = result

        return (
            output,
            error,
            execution_time,
            "N/A",
        )

    if len(result) == 2:
        output, error = result

        return (
            output,
            error,
            0,
            "N/A",
        )

    return "", "Unexpected execution result.", 0, "N/A"