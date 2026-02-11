import json
import os

def verify_exams(json_path):
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return

    with open(json_path, 'r') as f:
        try:
            exams = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

    print(f"Found {len(exams)} exams in {json_path}")
    print("-" * 60)
    print(f"{'ID':<20} | {'Year':<6} | {'Month':<10} | {'Questions':<10}")
    print("-" * 60)

    total_issues = 0

    for exam in exams:
        exam_id = exam.get('id', 'N/A')
        year = exam.get('year', 'N/A')
        month = exam.get('month', 'N/A')
        questions = exam.get('questions', [])
        
        print(f"{exam_id:<20} | {year:<6} | {month:<10} | {len(questions):<10}")

        # Check for issues in questions
        for q in questions:
            q_id = q.get('id', 'N/A')
            text = q.get('text', '')
            options = q.get('options', [])
            correct = q.get('correctIndices', [])
            
            issues = []
            if not text or len(text.strip()) < 5:
                issues.append("Text empty or too short")
            if len(options) < 2:
                issues.append(f"Too few options ({len(options)})")
            if not correct:
                issues.append("No correct answers")
            
            if issues:
                total_issues += 1
                # Only print first few issues to avoid spamming
                if total_issues <= 20: 
                    print(f"  [Warn] Exam {exam_id}, Q {q_id}: {', '.join(issues)}")

    print("-" * 60)
    if total_issues > 0:
        print(f"Total issues found: {total_issues}")
    else:
        print("No obvious structural issues found in exams.json")

if __name__ == "__main__":
    verify_exams("app/src/main/assets/exams.json")
