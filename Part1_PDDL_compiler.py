import re


# =========================
# HELPERS
# =========================

def ensure_and_block(effect_body):
    effect_body = effect_body.strip()
    if effect_body.startswith("(and"):
        return effect_body
    return f"(and {effect_body})"


def insert_into_and(effect_body, new_effect):
    effect_body = ensure_and_block(effect_body)
    inner = effect_body[len("(and"): -1].strip()
    return f"(and {inner} {new_effect})"


# =========================
# EXTRACT ACTION BLOCK 
# =========================

def extract_action_block(domain_str, action_name):
    start = domain_str.find(f"(:action {action_name}")
    if start == -1:
        return None

    count = 0
    for i in range(start, len(domain_str)):
        if domain_str[i] == "(":
            count += 1
        elif domain_str[i] == ")":
            count -= 1

        if count == 0:
            return domain_str[start:i+1]

    return None


# =========================
# EXTRACT EFFECT
# =========================

def extract_effect_block(action_block):
    start = action_block.find(":effect")
    if start == -1:
        return None

    start = action_block.find("(", start)

    count = 0
    for i in range(start, len(action_block)):
        if action_block[i] == "(":
            count += 1
        elif action_block[i] == ")":
            count -= 1

        if count == 0:
            return action_block[start:i+1]

    return None


# =========================
# PREDICATES
# =========================

def add_observation_predicates(domain_str, observations):
    new_preds = "\n    ".join(f"(p_{a})" for a in observations)

    pattern = r"\(:predicates\s*((?:\([^)]*\)\s*)+)\)"
    match = re.search(pattern, domain_str, re.DOTALL)

    if not match:
        raise ValueError("No :predicates found")

    old = match.group(1)

    
    new = old.strip() + "\n    " + new_preds + "\n"

    return domain_str.replace(old, new, 1)


# =========================
# MODIFY ACTIONS
# =========================

def modify_actions(domain_str, observations):
    new_domain = domain_str

    for i, action in enumerate(observations):
        action = action.lower()

        action_block = extract_action_block(new_domain, action)

        if not action_block:
            print(f"Warning: action '{action}' not found")
            continue

        
        if ":effect" not in action_block:
            raise ValueError(f"No :effect in {action}")

        before, after = action_block.split(":effect", 1)

        effect_block = extract_effect_block(":effect" + after)

        if not effect_block:
            raise ValueError(f"Effect parsing failed for {action}")

        
        if i == 0:
            obs = f"(p_{action})"
        else:
            prev = observations[i - 1]
            obs = f"(when (p_{prev}) (p_{action}))"

        
        clean_effect = effect_block.replace(":effect", "", 1).strip()

        updated_effect = ":effect " + insert_into_and(clean_effect, obs)

        
        new_action = before + updated_effect + "\n)"

        
        new_domain = new_domain.replace(action_block, new_action, 1)

    return new_domain


# =========================
# MODIFY GOAL
# =========================

def modify_goal(problem_str, last_obs, compliant=True):
    obs = f"(p_{last_obs})"

    pattern = r"\(:goal\s*(\(.*?\))\s*\)"
    match = re.search(pattern, problem_str, re.DOTALL)

    if not match:
        raise ValueError("No goal found")

    original = match.group(1)

    if compliant:
        new_goal = f"(and {original} {obs})"
    else:
        new_goal = f"(and {original} (not {obs}))"

    return problem_str.replace(original, new_goal, 1)


# =========================
# MAIN COMPILER
# =========================

def compile_pddl(domain_str, problem_str, observations):
    domain_new = add_observation_predicates(domain_str, observations)
    domain_new = modify_actions(domain_new, observations)

    last = observations[-1]

    compliant = modify_goal(problem_str, last, True)
    noncompliant = modify_goal(problem_str, last, False)

    return domain_new, compliant, noncompliant


# =========================
# RUNNER
# =========================

if __name__ == "__main__":
    observations = ["up", "right"]

    with open("domain.pddl") as f:
        domain = f.read()

    with open("problem.pddl") as f:
        problem = f.read()

    d, c, nc = compile_pddl(domain, problem, observations)

    with open("domain_mod.pddl", "w") as f:
        f.write(d)

    with open("problem_compliant.pddl", "w") as f:
        f.write(c)

    with open("problem_noncompliant.pddl", "w") as f:
        f.write(nc)

    print("Done. Files generated.")