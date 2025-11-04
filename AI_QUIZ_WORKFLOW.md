# AI-Assisted Quiz Creation Workflow

## 🤖 The Easiest Way to Add Quiz Questions

This workflow is designed for using AI (like Claude, ChatGPT, etc.) to generate quiz questions and import them directly into your database.

---

## Quick Start (3 Easy Steps)

### Step 1: Generate Quiz Content with AI

Give this prompt to your AI:

```
I need you to create quiz questions for Module [X.X] of my freight agent training guide.

The module covers: [brief description of module content]

Please generate 2-3 multiple choice questions in this EXACT format:

MODULE: [X.X]

Q: q[X]_[X]_[#]
Question: [Your question text here?]
A: [First choice]
B: [Second choice]
C: [Third choice]
D: [Fourth choice]
CORRECT: [A/B/C/D]
EXPLANATION: [Detailed explanation of why the correct answer is correct]

See quiz_example.txt for reference examples.
```

### Step 2: Save the AI Output

Copy the AI-generated quiz questions and save to a file (e.g., `new_quizzes.txt`)

Or just copy to your clipboard—you'll paste it in the next step.

### Step 3: Import to Database

Run the import script:

```bash
python import_quizzes.py
```

Choose option **2** (Simple text format)

Paste your quiz content

Press **Ctrl+Z then Enter** (Windows) or **Ctrl+D** (Mac/Linux)

Done! ✅

---

## Detailed Workflow

### For Local Development (SQLite)

```bash
# 1. Generate quizzes with AI (see prompt above)

# 2. Save to file: new_quizzes.txt

# 3. Import to local database
python import_quizzes.py

# 4. Choose option 3 (Load from file)
# Enter: new_quizzes.txt

# 5. Test locally
python main.py
# Visit http://localhost:5000 and test the new quizzes
```

### For Production Deployment (PostgreSQL)

After testing locally and confirming quizzes work:

```bash
# On your local machine
git add new_quizzes.txt
git commit -m "Add Module 7.1 quiz questions"
git push

# On production server
git pull

# Set environment variable for production database
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Import to production
python import_quizzes.py

# Choose option 3, enter: new_quizzes.txt
```

---

## Format Reference

### Simple Text Format (Recommended for AI)

```
MODULE: 7.1

Q: q7_1_1
Question: What is the primary benefit of XYZ?
A: First incorrect choice
B: Correct answer here
C: Another incorrect choice
D: Final incorrect choice
CORRECT: B
EXPLANATION: Detailed explanation of why B is correct and why others are wrong.

Q: q7_1_2
Question: Your next question?
A: Choice A
B: Choice B
C: Choice C
D: Choice D
CORRECT: C
EXPLANATION: Why C is the best answer...
```

### JSON Format (Advanced)

```json
{
    "module_id": "7.1",
    "questions": [
        {
            "id": "q7_1_1",
            "question": "What is the primary benefit of XYZ?",
            "choices": {
                "a": "First incorrect choice",
                "b": "Correct answer here",
                "c": "Another incorrect choice",
                "d": "Final incorrect choice"
            },
            "correct_choice": "b",
            "explanation": "Detailed explanation..."
        }
    ]
}
```

---

## Question ID Naming Convention

Format: `q[chapter]_[module]_[question#]`

Examples:
- `q7_1_1` = Chapter 7, Module 1, Question 1
- `q7_1_2` = Chapter 7, Module 1, Question 2
- `q7_2_1` = Chapter 7, Module 2, Question 1

**Important:** IDs must be unique across the entire system!

---

## AI Prompt Templates

### For Creating New Module Quizzes

```
Create 2-3 multiple choice quiz questions for Module [X.X]: [Module Title].

This module teaches freight agents about [topic description].

Key concepts covered:
- [Concept 1]
- [Concept 2]
- [Concept 3]

Requirements:
- Questions should be scenario-based and practical
- Test application of knowledge, not just memorization
- Provide detailed explanations
- Include realistic distractors (wrong answers that seem plausible)

Use this format:
[paste format from quiz_example.txt]
```

### For Expanding Existing Modules

```
The existing Module [X.X] has [N] quiz questions. I need [N] more questions covering different aspects of the same material.

Existing questions cover:
- [Topic 1]
- [Topic 2]

Please create new questions that cover:
- [Different aspect 1]
- [Different aspect 2]

Use format from quiz_example.txt
```

### For Updating/Improving Questions

```
Review this quiz question and improve it:

[paste existing question]

Issues to address:
- Make the question more scenario-based
- Ensure distractors are plausible but clearly wrong
- Strengthen the explanation

Provide the improved version in the same format.
```

---

## Troubleshooting

### "Cannot connect to database"
- Make sure you've run `python init_db.py` first
- Check that `training_guide.db` exists in your project folder

### "Skipping question: Missing fields"
- Check that every question has: Q, Question, A, B, C, D, CORRECT, EXPLANATION
- Make sure there are no typos in the field names

### "Error: MODULE not specified"
- The first line must be `MODULE: [module_id]`
- Example: `MODULE: 7.1`

### Questions import but don't show in app
- Restart Flask app: `python main.py`
- Clear your browser cache
- Check that module exists in database: `SELECT * FROM modules WHERE id = '7.1';`

---

## Tips for High-Quality AI-Generated Quizzes

1. **Be Specific in Your Prompt**
   - Give AI context about what the module teaches
   - Provide learning objectives
   - Share examples of good vs. bad questions

2. **Review AI Output**
   - AI might generate factually incorrect information
   - Check that correct answers are actually correct
   - Ensure explanations are accurate

3. **Test the Questions**
   - Import to local database first
   - Take the quiz yourself
   - Ask: "Would this confuse students?" or "Is this too easy/hard?"

4. **Iterate**
   - If questions aren't great, refine your prompt
   - Ask AI to revise specific questions
   - Mix AI-generated with human-written questions

---

## File Organization

Keep your quiz source files organized:

```
Trinity-Training-Guide/
├── quizzes/
│   ├── chapter1/
│   │   ├── module_1_1.txt
│   │   ├── module_1_2.txt
│   │   └── ...
│   ├── chapter2/
│   │   └── ...
│   └── chapter7/
│       ├── module_7_1.txt
│       └── module_7_2.txt
```

This makes it easy to:
- Track what's been created
- Update specific modules later
- Re-import if database needs to be rebuilt

---

## Advanced: Batch Import Multiple Modules

Create a script `import_all.sh` (Linux/Mac) or `import_all.bat` (Windows):

```bash
#!/bin/bash
echo "Importing all quizzes..."
python import_quizzes.py < quizzes/chapter7/module_7_1.txt
python import_quizzes.py < quizzes/chapter7/module_7_2.txt
python import_quizzes.py < quizzes/chapter7/module_7_3.txt
echo "All imports complete!"
```

---

## Next Steps

- See `quiz_example.txt` for real examples
- Run `python import_quizzes.py` to start importing
- Check `deployment.md` for production deployment details

Questions? Check the main README or deployment guide.

