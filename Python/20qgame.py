import pandas as pd
import random
import os
import time

# -------- CONFIG ----------
FILE_NAME = "countries.xlsx"
MAX_QUESTIONS = 20
MIN_QUESTIONS_BEFORE_GUESS = 10
NARROW_TOL = 0.45
TOP_RANDOM_K = 3

# thresholds for logical inference (user answer >= this implies "yes")
IMPLY_YES_THRESHOLD = 0.5
IMPLY_NO_THRESHOLD = 0.2

# -------- Load dataset ----------
if not os.path.exists(FILE_NAME):
    raise SystemExit(f"ERROR: {FILE_NAME} not found in current folder. Put it in the same folder as this script.")

df = pd.read_excel(FILE_NAME)

# sanity: first column must be Country
all_cols = list(df.columns)
if len(all_cols) < 2 or all_cols[0].lower() != "country":
    raise SystemExit("ERROR: First column header must be 'Country' and subsequent columns are question headers.")

# question columns (all columns except the first)
question_columns = list(df.columns[1:])
# coerce to numeric (fill missing with 0.0)
for c in question_columns:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

# -------- Intro (print once) ----------
print("Welcome — category: COUNTRIES")
print("Think of a country and I will try to guess it by asking up to 20 questions.")
print("Answer each question with a number between 0 and 1 where 1 means YES and 0 means NO.")
print("You may use decimals (for example 0.6) if you're unsure or partially true.")
print("Let's begin!\n")
time.sleep(0.3)

# -------- Helpers ----------
def read_float(prompt):
    s = input(prompt).strip()
    while True:
        try:
            v = float(s)
            if 0.0 <= v <= 1.0:
                return v
        except:
            pass
        s = input("Please enter a number between 0 and 1 (0 = No, 1 = Yes): ").strip()

def choose_question(candidates_df, asked_set):
    """
    Score questions by (stddev * balance) among candidate rows.
    Return a question. Add slight randomness by selecting among top-k.
    """
    scored = []
    for q in question_columns:
        if q in asked_set:
            continue
        col = candidates_df[q].astype(float)
        if len(col) <= 1:
            # low info but keep as fallback
            scored.append((q, 0.0))
            continue
        std = float(col.std(ddof=0))
        mean = float(col.mean())
        balance = 1.0 - abs(mean - 0.5)
        score = std * balance
        scored.append((q, score))
    if not scored:
        return None
    # sort descending by score
    scored.sort(key=lambda x: x[1], reverse=True)
    topk = scored[:TOP_RANDOM_K]
    # if top score is 0 (no info), just pick any unasked question deterministically
    if topk[0][1] <= 0:
        for q in question_columns:
            if q not in asked_set:
                return q
        return None
    # random choice among topk weighted by score (so best more likely)
    qs, scores = zip(*topk)
    total = sum(scores)
    if total <= 0:
        return random.choice(qs)
    probs = [s / total for s in scores]
    return random.choices(qs, weights=probs, k=1)[0]

def compute_scores(dataset, answers):
    rows = []
    for _, row in dataset.iterrows():
        s = 0.0
        for q, val in answers.items():
            rq = float(row.get(q, 0.0))
            s += abs(rq - val)
        rows.append((row["Country"], s))
    rows.sort(key=lambda x: x[1])
    return rows

def apply_logical_inference(answers):
    """
    Given answered Q->value, infer obvious contradictions and add implied answers:
    - continents are exclusive: if one continent > IMPLY_YES_THRESHOLD then other continent flags -> 0
    This function returns a dict of newly implied answers (q->value) which should be merged into asked.
    """
    implied = {}

    # Detect continent-like columns robustly (loose heuristics)
    continents = {}
    continent_names = ["africa", "asia", "europe", "north america", "south america", "oceania"]
    for cont in continent_names:
        for col in question_columns:
            low = col.lower()
            # match typical patterns: "in africa", "africa?", "africa"
            if cont in low and ("in " in low or low.startswith(cont) or low.endswith(cont) or cont in low.split()):
                continents[cont] = col
                break
    # If any continent column answered > threshold, exclude other continent columns (set implied = 0.0)
    for cont, col in continents.items():
        if col in answers and answers[col] > IMPLY_YES_THRESHOLD:
            for other_cont, other_col in continents.items():
                if other_col != col and other_col not in answers:
                    implied[other_col] = 0.0
            break

    # Ensure only valid columns returned
    implied = {k: v for k, v in implied.items() if k in question_columns}
    return implied

def safe_save(df_to_save):
    """Try saving to FILE_NAME. If permission error, ask user to close excel or save to alternate."""
    try:
        df_to_save.to_excel(FILE_NAME, index=False)
        print(f"Saved updates to {FILE_NAME}")
        return True
    except PermissionError:
        print(f"PermissionError: could not save to {FILE_NAME}. Is it open in Excel? Close it and press Enter to retry, or type 'skip' to save to countries_updated.xlsx")
        resp = input().strip().lower()
        if resp == "skip":
            alt = os.path.splitext(FILE_NAME)[0] + "_updated.xlsx"
            try:
                df_to_save.to_excel(alt, index=False)
                print(f"Saved updates to {alt}")
                return True
            except Exception as e:
                print("Save failed:", e)
                return False
        else:
            try:
                df_to_save.to_excel(FILE_NAME, index=False)
                print(f"Saved updates to {FILE_NAME}")
                return True
            except Exception as e:
                print("Retry failed:", e)
                return False

# -------- MAIN GAME LOOP (play again) ----------
while True:
    asked = {} 			 # q -> float answer
    asked_order = []
    candidates = df.copy()
    rejected_guesses = set() # Set to track countries rejected by the user during the game
    
    # Use q_index to track the actual number of questions asked and loop termination
    q_index = 0
    
    # Flag to control the question asking phase
    continue_asking = True
    correct = False

    while continue_asking and q_index < MAX_QUESTIONS:

        # update implied answers
        implied = apply_logical_inference(asked)
        for k, v in implied.items():
            if k not in asked:
                asked[k] = v
                asked_order.append(k)
                low = max(0.0, v - NARROW_TOL)
                high = min(1.0, v + NARROW_TOL)
                narrowed = candidates[candidates[k].between(low, high)]
                if len(narrowed) >= 1:
                    candidates = narrowed

        # pick next question dynamically
        q = choose_question(candidates, set(asked.keys()))
        
        if q is None:
            # No more information-rich questions to ask
            continue_asking = False
            break

        if q in asked:
            continue 

        # ask user
        ans = read_float(f"{q}: ")
        asked[q] = ans
        asked_order.append(q)

        # narrow candidates loosely
        low = max(0.0, ans - NARROW_TOL)
        high = min(1.0, ans + NARROW_TOL)
        narrowed = candidates[candidates[q].between(low, high)]
        if len(narrowed) >= 1:
            candidates = narrowed
            
        q_index += 1 # Increment question count after a valid question is asked and answered

        # DECISION POINT: Should we check for a guess?
        if len(asked) >= MIN_QUESTIONS_BEFORE_GUESS or len(candidates) == 1 or q_index == MAX_QUESTIONS:
            
            # Compute score and get the best guess
            scored = compute_scores(candidates, asked)
            guess = scored[0][0] if scored else None
            
            if guess:
                
                # Filter out previously rejected guesses from the current candidate list
                scored = [country_score for country_score in scored if country_score[0] not in rejected_guesses]
                guess = scored[0][0] if scored else None
                
                if not guess:
                    # If all remaining candidates were already rejected, continue asking questions
                    continue
                    
                # Simplified prompt: just ask the question.
                prompt = f"\nIs it {guess}? (1 = Yes, 0 = No): "
                
                ansg = input(prompt).strip()
                while ansg not in {"0", "1"}:
                    ansg = input("Type 1 for YES or 0 for NO: ").strip()

                if ansg == "1":
                    correct = True
                    continue_asking = False # End question asking
                    break
                else:
                    # Wrong guess (or user chose not to guess yet).
                    rejected_guesses.add(guess) # Store the rejected guess
                    
                    if len(candidates) == 1:
                         # If they say NO when there is only one candidate, that candidate is wrong.
                         # Remove it from consideration to force a search for the second best match on the next guess.
                         candidates = candidates[candidates['Country'] != guess]
                         print(f"I will eliminate {guess} and continue asking questions.")
                    
                    if q_index >= MAX_QUESTIONS:
                        # If we used the last question, end the loop.
                        continue_asking = False
                        break
                    
                    # Otherwise, continue to the next iteration of the while loop to ask the next question.


    # ----------------------------------------------------------------------
    # POST-QUESTION PHASE (Final Guess/Learning)
    # ----------------------------------------------------------------------

    # If the question loop ended without a correct guess, make a final check.
    if not correct:
        # Score against the full dataset to find the mathematically closest match
        scored = compute_scores(df, asked)
        
        # Filter out previously rejected guesses
        scored = [country_score for country_score in scored if country_score[0] not in rejected_guesses]
        
        final_guess = scored[0][0] if scored else None

        if final_guess is None:
            print("\nI couldn't produce a guess.")
            
        else:
            # Final, forced guess attempt using the best match from the full dataset
            ansg = input(f"\nIs it {final_guess}? (1 = Yes, 0 = No): ").strip()
            while ansg not in {"0", "1"}:
                ansg = input("Type 1 for YES or 0 for NO: ").strip()

            if ansg == "1":
                correct = True
            else:
                pass # Proceed to learning/giving up


    if correct:
        print("\nI guessed it! 🎉")
        again = input("That was fun! Wanna play again? (1 = Yes, 0 = No): ").strip()
        if again == "1":
            continue
        else:
            print("Goodbye — run me again to play another round.")
            break

    # if guess wrong -> learn
    print("\nI give up.")
    new_country = input("Which country were you thinking of? ").strip()

    # Check if the country already exists (case-insensitive)
    country_exists = new_country.lower() in df["Country"].str.lower().tolist()

    if country_exists:
        # Get the correctly cased name from the DataFrame for feedback
        correct_name = df[df["Country"].str.lower() == new_country.lower()]["Country"].iloc[0]
        print(f"\nI see you were thinking of {correct_name}!")
        print("This country already exists in my database, so I won't overwrite its values.")
    else:
        # Proceed with learning the new country
        print("\nPlease help me fill values for ALL question columns so I can learn this country for next time.")
        new_row = {col: 0.0 for col in df.columns}
        new_row["Country"] = new_country

        for q, v in asked.items():
            if q in question_columns:
                new_row[q] = float(v)

        remaining = [c for c in question_columns if c not in asked]
        if remaining:
            print("Answer the remaining questions with 0–1 values:")
        for q in remaining:
            new_row[q] = read_float(f"{q}: ")

        # optional new question
        new_col = input("\n(Optional) Type a new distinguishing question (exact column name) to add, or press Enter to skip: ").strip()
        if new_col:
            if new_col not in df.columns:
                df[new_col] = 0.0
                question_columns.append(new_col)
            new_row[new_col] = read_float(f"For '{new_col}', what is the value for {new_country}? ")

        # append and save
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        # Re-coercing columns to numeric in case a new column was added
        for c in question_columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

        if safe_save(df):
            print(f"Thanks — I learned {new_country} and saved it to {FILE_NAME}.")
        else:
            print("I couldn't save the dataset. Close Excel if it's open and run again to save.")

    again = input("\nThat was fun! Wanna play again? (1 = Yes, 0 = No): ").strip()
    if again != "1":
        print("Goodbye — run me again to play another round.")
        break
