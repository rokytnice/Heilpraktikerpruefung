import json

def count(path):
    try:
        with open(path) as f:
            data = json.load(f)
            total = sum(len(e.get('questions', [])) for e in data)
            print(f"{path}: {len(data)} exams, {total} questions")
            return total
    except FileNotFoundError:
        print(f"{path}: Not found")
        return 0

print("Comparing question counts:")
c1 = count("app/src/main/assets/exams.json")
c2 = count("app/src/main/assets/exams_v2.json")

print(f"Difference: {c2 - c1} more questions in v2")
