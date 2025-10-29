# Chapter Implementation Checklist

Use this checklist when implementing each new chapter to avoid common mistakes.

## 1. Quiz Questions (main.py)

### Create Quiz Array
```python
chapterX_quizzes = [
    {
        "id": "qX_Y_Z",  # X=chapter, Y=module, Z=question number
        "question": "...",
        "choices": ["A", "B", "C", "D"],
        "correct_index": 0-3,  # RANDOMIZE! Mix of 0,1,2,3 across all quizzes
        "explanation": "..."
    }
]
```

### Critical: Use Underscore in ID Filtering
```python
# ✅ CORRECT - prevents qX_1 from matching qX_10
"X.Y": [q for q in chapterX_quizzes if q["id"].startswith("qX_Y_")]
                                                                  # ↑ underscore

# ❌ WRONG - qX_1 will match qX_10, qX_11, etc.
"X.Y": [q for q in chapterX_quizzes if q["id"].startswith("qX_Y")]
```

### Checklist
- [ ] Quiz array created with correct naming pattern
- [ ] All quiz IDs use underscore separator: `qX_Y_Z`
- [ ] `correct_index` randomized (mix of 0, 1, 2, 3)
- [ ] Questions match their module content
- [ ] Explanations are detailed and educational

---

## 2. Module Completion Tracking (main.py)

### Add to THREE locations:

#### Location 1: `get_module_completion_status()` function
```python
quiz_map = {
    # ... existing chapters ...
    "X.1": [q for q in chapterX_quizzes if q["id"].startswith("qX_1_")],
    "X.2": [q for q in chapterX_quizzes if q["id"].startswith("qX_2_")],
    # ... all modules with underscore in filter
}
```

#### Location 2: `get_chapter_completion_status()` function
```python
chapter_modules = {
    # ... existing chapters ...
    X: ["X.1", "X.2", "X.3", ...],  # All module IDs for chapter X
}
```

#### Location 3: `build_pages()` function - quiz_map_chX
```python
quiz_map_chX = {
    "X.1": [q for q in chapterX_quizzes if q["id"].startswith("qX_1_")],
    "X.2": [q for q in chapterX_quizzes if q["id"].startswith("qX_2_")],
    # ... all modules with underscore in filter
}
```

### Checklist
- [ ] Added to `get_module_completion_status()` quiz_map
- [ ] Added to `get_chapter_completion_status()` chapter_modules
- [ ] Added to `build_pages()` quiz_map_chX
- [ ] All filters use underscore: `startswith("qX_Y_")`

---

## 3. Content Formatting (project.md)

### Bold Headers
```markdown
**Module Title**
**Section Header**
**Key Terms**
```

### Strategic Callouts (15-25 per chapter)
```markdown
[KEY TAKEAWAY] Main concepts and critical information

[COMMON MISTAKE] Pitfalls to avoid, typical errors

[PRO TIP] Expert advice, insider knowledge

[IMPORTANT] Critical information that must be remembered

[REAL EXAMPLE] Concrete scenarios that illustrate concepts
```

### Distribution Guidelines
- Spread callouts across ALL modules (not just first few)
- Each module should have 1-3 callouts
- Use variety - don't use same type repeatedly
- Place strategically at key learning points

### Checklist
- [ ] All headers bolded with `**text**`
- [ ] 15-25 callouts added across all modules
- [ ] Callouts distributed evenly (all modules have some)
- [ ] Variety of callout types used
- [ ] Callouts placed at strategic learning points

---

## 4. Backend Integration (main.py - build_pages())

### Extract Chapter Content
```python
chX = extract_chapter_content(text, X)
```

### Add to Cover and TOC Pages
```python
pages.append({
    "type": "cover", 
    "content": cover_content, 
    "ch1_modules": ch1["modules"], 
    # ... existing chapters ...
    "chX_modules": chX["modules"]
})

pages.append({
    "type": "toc", 
    "chapters": chapters, 
    "ch1_modules": ch1["modules"],
    # ... existing chapters ...
    "chX_modules": chX["modules"]
})
```

### Add Chapter Content (follow pattern from previous chapters)
```python
# Chapter X intro
if chX["intro"]:
    pages.append({
        "type": "intro",
        "chapter_id": X,
        "chapter_title": chX["chapter_title"],
        "content": chX["intro"],
        "content_html": convert_to_html(chX["intro"])
    })

# Chapter X modules
for mod in chX["modules"]:
    module_page_map[mod["id"]] = len(pages)
    content_text = "\n".join(mod["content"])
    content_pages = split_content_into_pages(content_text)
    
    for page_idx, page_content in enumerate(content_pages):
        pages.append({
            "type": "module",
            "chapter_id": X,
            "chapter_title": chX["chapter_title"],
            "module_id": mod["id"],
            "module_title": mod["title"],
            "content": page_content,
            "content_html": convert_to_html(page_content),
            "module_page_num": page_idx + 1,
            "module_total_pages": len(content_pages)
        })
    
    # Add quiz questions
    if mod["id"] in quiz_map_chX:
        quiz_questions = quiz_map_chX[mod["id"]]
        for idx, quiz_question in enumerate(quiz_questions):
            quiz_page_map[quiz_question["id"]] = len(pages)
            pages.append({
                "type": "quiz",
                "chapter_id": X,
                "module_id": mod["id"],
                "module_title": mod["title"],
                "quiz_question": quiz_question,
                "question_number": idx + 1,
                "total_questions": len(quiz_questions)
            })

# Chapter X summary
if chX["summary"]:
    pages.append({
        "type": "summary",
        "chapter_id": X,
        "chapter_title": chX["chapter_title"],
        "content": chX["summary"],
        "content_html": convert_to_html(chX["summary"])
    })

# Chapter X action items
if chX["action_items"]:
    pages.append({
        "type": "action_items",
        "chapter_id": X,
        "chapter_title": chX["chapter_title"],
        "content": chX["action_items"],
        "content_html": convert_to_html(chX["action_items"])
    })
```

### Checklist
- [ ] `chX = extract_chapter_content(text, X)` added
- [ ] `chX_modules` added to cover page
- [ ] `chX_modules` added to TOC page
- [ ] Chapter intro added (if exists)
- [ ] All modules added with content splitting
- [ ] Quiz questions added after each module
- [ ] Chapter summary added (if exists)
- [ ] Chapter action items added (if exists)

---

## 5. Frontend Display (templates/page.html)

### Add Chapter Section in TOC

**CRITICAL: Check `preview_mode` FIRST, then `is_complete`**

```jinja
{% elif ch.id == X %}
  <li style="cursor: pointer;">
    <a href="{{ url_for('page', page_num=total_pages - 2) }}" style="...">Chapter {{ ch.id }}: {{ ch.title }}</a>
    {% if page.chX_modules %}
    <div style="margin-left: 30px; margin-top: 12px; font-size: 14px; line-height: 2.0;">
      {% for mod in page.chX_modules %}
        {% set is_complete = module_completion.get(mod.id, False) %}
        {% set prev_index = loop.index0 - 1 %}
        {% set is_locked = False %}
        {% if loop.index0 > 0 and not preview_mode %}
          {% set prev_mod_id = page.chX_modules[prev_index].id %}
          {% set is_locked = not module_completion.get(prev_mod_id, False) %}
        {% elif loop.index0 == 0 and not preview_mode %}
          {# First module requires previous chapter completion #}
          {% set is_locked = not all_ch[X-1]_modules_complete %}
        {% endif %}
        
        <div style="margin: 6px 0; display: flex; align-items: center;">
          {# CRITICAL: Check preview_mode FIRST #}
          {% if preview_mode %}
            <span style="color: var(--highlight); margin-right: 8px; font-size: 16px;">🔓</span>
          {% elif is_complete %}
            <span style="color: #10b981; margin-right: 8px; font-size: 16px;">✓</span>
          {% else %}
            <span style="color: var(--muted); margin-right: 8px; font-size: 16px;">☐</span>
          {% endif %}
          
          {% if is_locked %}
            <span style="color: var(--muted); opacity: 0.5; cursor: not-allowed;">
              🔒 Module {{ mod.id }}: {{ mod.title }}
            </span>
          {% else %}
            <a href="{{ url_for('page', page_num=page.module_page_map[mod.id]) }}" 
               style="color: {% if preview_mode %}var(--highlight){% elif is_complete %}#10b981{% else %}var(--muted){% endif %}; ...">
              Module {{ mod.id }}: {{ mod.title }}
            </a>
          {% endif %}
        </div>
        
        {# Quiz dropdown - ONLY when complete, NOT in preview_mode #}
        {% if is_complete and quiz_map.get(mod.id) %}
          <div class="quiz-toggle" onclick="toggleQuizDropdown('{{ mod.id }}')">
            <span class="quiz-toggle-icon" id="toggle-icon-{{ mod.id }}">▶</span>
            Quiz Questions ({{ quiz_map[mod.id]|length }})
          </div>
          <div class="quiz-dropdown" id="quiz-dropdown-{{ mod.id }}">
            {% for quiz_q in quiz_map[mod.id] %}
              {% set is_answered = quiz_answers.get(quiz_q.id, False) %}
              {% set quiz_page_num = page.quiz_page_map.get(quiz_q.id) %}
              <a href="{{ url_for('page', page_num=quiz_page_num) }}" 
                 class="quiz-question-item {% if is_answered %}answered{% endif %}"
                 style="text-decoration: none; display: flex; align-items: center; gap: 8px;">
                <span class="quiz-question-checkmark">{% if is_answered %}✓{% else %}○{% endif %}</span>
                <span>Question {{ loop.index }}</span>
              </a>
            {% endfor %}
          </div>
        {% endif %}
      {% endfor %}
      
      <!-- Chapter X Key Concepts -->
      <div style="margin: 12px 0 6px; display: flex; align-items: center;">
        {# CRITICAL: Check preview_mode FIRST #}
        {% if preview_mode %}
          <span style="color: var(--highlight); margin-right: 8px; font-size: 16px;">🔓</span>
          <a href="{{ url_for('page', page_num=total_pages - 2) }}" style="...">
            📋 Chapter X Key Concepts
          </a>
        {% elif all_chX_modules_complete %}
          <span style="color: #10b981; margin-right: 8px; font-size: 16px;">✓</span>
          <a href="{{ url_for('page', page_num=total_pages - 2) }}" style="...">
            📋 Chapter X Key Concepts
          </a>
        {% else %}
          <span style="color: var(--muted); margin-right: 8px; font-size: 16px;">☐</span>
          <span style="color: var(--muted); opacity: 0.5; cursor: not-allowed;">
            🔒 Chapter X Key Concepts
          </span>
        {% endif %}
      </div>
      
      <!-- Chapter X Action Items -->
      <div style="margin: 6px 0; display: flex; align-items: center;">
        {# CRITICAL: Check preview_mode FIRST #}
        {% if preview_mode %}
          <span style="color: var(--highlight); margin-right: 8px; font-size: 16px;">🔓</span>
          <a href="{{ url_for('page', page_num=total_pages - 1) }}" style="...">
            ✅ Chapter X Action Items
          </a>
        {% elif all_chX_modules_complete %}
          <span style="color: #10b981; margin-right: 8px; font-size: 16px;">✓</span>
          <a href="{{ url_for('page', page_num=total_pages - 1) }}" style="...">
            ✅ Chapter X Action Items
          </a>
        {% else %}
          <span style="color: var(--muted); margin-right: 8px; font-size: 16px;">☐</span>
          <span style="color: var(--muted); opacity: 0.5; cursor: not-allowed;">
            🔒 Chapter X Action Items
          </span>
        {% endif %}
      </div>
    </div>
    {% endif %}
  </li>
```

### Checklist
- [ ] New `{% elif ch.id == X %}` section added
- [ ] All conditionals check `preview_mode` FIRST
- [ ] Module icons: `preview_mode` → 🔓, `is_complete` → ✓, else → ☐
- [ ] Quiz dropdown condition: `is_complete and quiz_map.get(mod.id)` (NOT preview_mode)
- [ ] Quiz format: "Question {{ loop.index }}" (not truncated question text)
- [ ] Key Concepts section checks preview_mode first
- [ ] Action Items section checks preview_mode first

---

## 6. Completion Tracking (main.py - page route)

### Add Module Completion Variables
```python
all_chX_modules_complete = False

if pages:
    chX_modules = pages[0].get("chX_modules", [])
    
    for mod in chX_modules:
        module_completion[mod["id"]] = get_module_completion_status(session.get('quiz_answers', {}), mod["id"])
    all_chX_modules_complete = get_chapter_completion_status(session.get('quiz_answers', {}), X)
```

### Add to Template Render
```python
return render_template(
    "page.html",
    # ... existing variables ...
    all_chX_modules_complete=all_chX_modules_complete,
    # ...
)
```

### Add Unlocking Logic
```python
elif current_module_id.startswith("X."):
    # For Chapter X, first check if all Chapter [X-1] is complete
    if not get_chapter_completion_status(session.get('quiz_answers', {}), X-1):
        return redirect(url_for("page", page_num=1))
    # Then check previous Chapter X modules
    chapter_X_modules = ["X.1", "X.2", "X.3", ...]
    module_index = chapter_X_modules.index(current_module_id) if current_module_id in chapter_X_modules else 0
    if module_index > 0:
        for i in range(module_index):
            if not get_module_completion_status(session.get('quiz_answers', {}), chapter_X_modules[i]):
                return redirect(url_for("page", page_num=1))
```

### Checklist
- [ ] `all_chX_modules_complete` variable initialized
- [ ] `chX_modules` extracted from pages
- [ ] Module completion loop added
- [ ] Chapter completion status calculated
- [ ] Variable passed to template render
- [ ] Unlocking logic added (requires previous chapter)
- [ ] Sequential module unlocking within chapter

---

## 7. Content Splitting Parameters

### Current Settings (main.py)
```python
def split_content_into_pages(content_text: str, max_height_score: float = 28.0) -> list:
    # ...
    safety_threshold = max_height_score * 0.85  # 85% for callouts
```

### Adjustment Guidelines
- **If callouts still cut off:** Reduce `max_height_score` (try 25.0 or 22.0)
- **If pages too short:** Increase slightly (try 30.0 or 32.0)
- **Safety threshold:** Keep at 85% for callouts
- **Test with longest module** to verify

### Visual Testing
Navigate through EVERY module and check:
- [ ] All callouts fully visible (title + content + bottom border)
- [ ] No text cut off mid-sentence
- [ ] Headers not orphaned at bottom of page
- [ ] Page breaks feel natural
- [ ] Next button visible below all content

---

## 8. Quiz Questions Quality Checklist

### Per Question
- [ ] Question is clear and unambiguous
- [ ] All 4 choices are plausible
- [ ] Only ONE clearly correct answer
- [ ] Explanation teaches WHY answer is correct
- [ ] Content matches the module topic

### Per Module
- [ ] Number of questions appropriate (1-3 per module)
- [ ] Questions cover key concepts from module
- [ ] Difficulty appropriate for learning stage

### Per Chapter
- [ ] Correct answers distributed: ~25% each of A/B/C/D
- [ ] No pattern (e.g., not all B or C)
- [ ] Total questions: 15-25 for full chapter

---

## 9. Testing Protocol

### Phase 1: Preview Mode Test
1. Visit `http://127.0.0.1:5000/preview`
2. Check TOC:
   - [ ] All modules show 🔓 (unlock icon, orange)
   - [ ] No ✓ checkmarks visible
   - [ ] No quiz dropdowns visible
3. Navigate through each module:
   - [ ] Can access all content
   - [ ] All callouts fully visible
   - [ ] Page breaks reasonable

### Phase 2: Student Mode Test
1. Clear cookies or use incognito: `http://127.0.0.1:5000/`
2. Check TOC:
   - [ ] Only Module X.1 unlocked (if previous chapter complete)
   - [ ] All other modules show 🔒
   - [ ] No quiz dropdowns visible
3. Complete Module X.1 quizzes:
   - [ ] Quiz dropdown appears after completion
   - [ ] Shows "Question 1", "Question 2", etc.
   - [ ] Correct answers work
   - [ ] Module X.2 unlocks
4. Test progressive unlocking:
   - [ ] Each module unlocks after previous complete
   - [ ] Can't skip ahead
   - [ ] Summary/Action items locked until all modules complete

### Phase 3: Callout Visibility Test
For EVERY module in the chapter:
- [ ] Navigate to module
- [ ] Check EVERY callout box:
  - [ ] Title visible (with icon)
  - [ ] All content visible
  - [ ] Bottom border complete
  - [ ] No cutoff at page bottom
- [ ] If cutoff found: adjust `max_height_score` and retest

### Phase 4: Quiz Functionality Test
- [ ] Each module has correct number of questions
- [ ] Questions appear AFTER module content
- [ ] Correct answers work (green feedback)
- [ ] Wrong answers give "try again" (red feedback)
- [ ] Explanations display correctly
- [ ] Module completion updates after all quizzes correct
- [ ] Next module unlocks

---

## 10. Common Mistakes to Avoid

### ❌ Quiz ID Filtering Without Underscore
```python
# WRONG - will match q4_1, q4_10, q4_11
"4.1": [q for q in chapter4_quizzes if q["id"].startswith("q4_1")]

# CORRECT - only matches q4_1_1, q4_1_2, etc.
"4.1": [q for q in chapter4_quizzes if q["id"].startswith("q4_1_")]
```

### ❌ Preview Mode Check Order
```jinja
<!-- WRONG - shows checkmarks in preview mode -->
{% if is_complete %}
  ✓
{% elif preview_mode %}
  🔓
{% endif %}

<!-- CORRECT - preview mode takes priority -->
{% if preview_mode %}
  🔓
{% elif is_complete %}
  ✓
{% endif %}
```

### ❌ Quiz Dropdown in Preview Mode
```jinja
<!-- WRONG - shows quizzes in preview mode -->
{% if (preview_mode or is_complete) and quiz_map.get(mod.id) %}

<!-- CORRECT - only when complete -->
{% if is_complete and quiz_map.get(mod.id) %}
```

### ❌ All Correct Answers Same Index
```python
# WRONG - all correct answers are B
{"correct_index": 1}  # repeated for all questions

# CORRECT - randomized mix
{"correct_index": 0}  # A
{"correct_index": 2}  # C
{"correct_index": 1}  # B
{"correct_index": 3}  # D
```

### ❌ Forgetting to Add Chapter to All 3 Tracking Functions
- Must add to `get_module_completion_status()`
- Must add to `get_chapter_completion_status()`
- Must add to `build_pages()` quiz_map_chX

### ❌ Not Testing Callout Visibility
- Must navigate through EVERY module
- Must check EVERY callout
- Don't assume—verify visually

---

## Quick Reference: Files to Modify

1. **main.py**
   - Add `chapterX_quizzes` array
   - Update `get_module_completion_status()`
   - Update `get_chapter_completion_status()`
   - Update `build_pages()`
   - Update `page()` route completion tracking
   - Update `page()` route unlocking logic

2. **project.md**
   - Format content with bold headers
   - Add 15-25 strategic callouts

3. **templates/page.html**
   - Add new `{% elif ch.id == X %}` section
   - Ensure preview_mode checked first
   - Quiz dropdown only on is_complete

---

## Success Criteria

Chapter is complete when:
- ✅ All quizzes created with randomized answers
- ✅ All 3 tracking functions updated
- ✅ Content formatted with headers and callouts
- ✅ Backend integration complete
- ✅ Frontend TOC display working
- ✅ Preview mode shows 🔓 for all
- ✅ Student mode shows proper locking
- ✅ All callouts fully visible
- ✅ Quiz questions work correctly
- ✅ Progressive unlocking functional

---

**Last Updated:** Based on Chapter 4 implementation and fixes
**Current Project State:** Chapters 1-4 complete, ready for Chapter 5+

