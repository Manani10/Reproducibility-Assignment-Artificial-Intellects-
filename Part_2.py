import subprocess
import re
import os

# =========================================
# FAST DOWNWARD PATH
# =========================================
FAST_DOWNWARD = "fast-downward.py"
DOMAIN = "domain_mod.pddl"
COMPLIANT = "problem_compliant.pddl"
NONCOMPLIANT = "problem_noncompliant.pddl"

# =========================================
# RUN PLANNER
# =========================================
def run_planner(domain_file, problem_file):
    command = [
        "python",
        FAST_DOWNWARD,
        domain_file,
        problem_file,
        "--search",
        "astar(lmcut())"
    ]
    print("\nRunning:")
    print(" ".join(command))

    result = subprocess.run(
        command,
        capture_output=True,
        text=True
    )

    if result.returncode not in (0, 10, 11, 12):
        print(f"[WARNING] Planner exited with code {result.returncode}")

    return result.stdout + result.stderr

# =========================================
# EXTRACT RESULTS
# =========================================
def extract_results(output):
    results = {
        "success": False,
        "plan_cost": None,
        "search_time": None,
        "expanded_states": None
    }

    if "Solution found" in output:
        results["success"] = True

    cost_match = re.search(r"Plan cost:\s*(\d+)", output)
    if cost_match:
        results["plan_cost"] = int(cost_match.group(1))

    time_match = re.search(r"Search time:\s*([\d.]+)s?", output)
    if time_match:
        results["search_time"] = float(time_match.group(1))

    expanded_match = re.search(r"Expanded (\d+) state", output)
    if expanded_match:
        results["expanded_states"] = int(expanded_match.group(1))

    return results

# =========================================
# DISPLAY RESULTS
# =========================================
def show_results(name, results):
    print("\n==============================")
    print(name)
    print("==============================")
    print(f"  Success:         {results['success']}")
    print(f"  Plan Cost:       {results['plan_cost']}")
    print(f"  Search Time:     {results['search_time']}s")
    print(f"  Expanded States: {results['expanded_states']}")

# =========================================
# CHECK FILES EXIST
# =========================================
def check_files(*files):
    all_present = True
    for f in files:
        if not os.path.exists(f):
            print(f"[ERROR] Missing file: {f}")
            all_present = False
    return all_present

# =========================================
# INTERPRET RESULTS
# =========================================
def interpret(compliant, noncompliant):
    print("\n===================================")
    print("FINAL INTERPRETATION")
    print("===================================")

    c_ok = compliant["success"]
    n_ok = noncompliant["success"]
    c_cost = compliant["plan_cost"]
    n_cost = noncompliant["plan_cost"]

    if c_ok and not n_ok:
        print("  >> Observations STRONGLY support the goal.")

    elif not c_ok and n_ok:
        print("  >> Observations STRONGLY contradict the goal.")

    elif c_ok and n_ok:
        if c_cost is not None and n_cost is not None:
            if c_cost < n_cost:
                print(f"  >> Goal is MORE likely compliant (cost {c_cost} vs {n_cost}).")
            elif c_cost > n_cost:
                print(f"  >> Goal is LESS likely compliant (cost {c_cost} vs {n_cost}).")
            else:
                print(f"  >> Both goals equally plausible (cost {c_cost}).")
        else:
            print("  >> Both succeeded but plan costs unavailable.")

    else:
        print("  >> No strong evidence for compliance (both failed).")

# =========================================
# MAIN
# =========================================
if __name__ == "__main__":

    if not check_files(DOMAIN, COMPLIANT, NONCOMPLIANT):
        exit(1)

    compliant_output    = run_planner(DOMAIN, COMPLIANT)
    compliant_results   = extract_results(compliant_output)
    show_results("COMPLIANT PROBLEM", compliant_results)

    noncompliant_output   = run_planner(DOMAIN, NONCOMPLIANT)
    noncompliant_results  = extract_results(noncompliant_output)
    show_results("NON-COMPLIANT PROBLEM", noncompliant_results)

    interpret(compliant_results, noncompliant_results)
