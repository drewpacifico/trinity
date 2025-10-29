# Chapter 2 Integration Code for main.py
# This file contains the code changes needed to add Chapter 2 to your website

# STEP 1: Add this line after line 689 in build_pages()
# ch2 = extract_chapter_content(text, 2)

# STEP 2: Replace the comment at line 686-687 with:
# """Build a flat list of pages: Cover, TOC, chapters 1-2 with modules, summaries, action items."""

# STEP 3: After Chapter 1 action items section (around line 777), add Chapter 2:

CHAPTER_2_PAGE_CODE = '''
    # ===== CHAPTER 2 CONTENT =====
    
    # Chapter 2 intro
    if ch2["intro"]:
        pages.append({
            "type": "intro",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["intro"],
            "content_html": convert_to_html(ch2["intro"])
        })
    
    # Chapter 2 modules
    for mod in ch2["modules"]:
        module_page_map[mod["id"]] = len(pages)
        content_text = "\\n".join(mod["content"])
        content_pages = split_content_into_pages(content_text, max_chars_per_page=2000)
        
        for page_idx, page_content in enumerate(content_pages):
            pages.append({
                "type": "module",
                "chapter_id": 2,
                "chapter_title": ch2["chapter_title"],
                "module_id": mod["id"],
                "module_title": mod["title"],
                "content": page_content,
                "content_html": convert_to_html(page_content),
                "module_page_num": page_idx + 1,
                "module_total_pages": len(content_pages)
            })
        
        # Add quiz questions after each module
        ch2_quiz_map = {
            "2.1": MODULE_2_1_QUIZ,
            "2.2": MODULE_2_2_QUIZ,
            "2.3": MODULE_2_3_QUIZ,
            "2.4": MODULE_2_4_QUIZ,
            "2.5": MODULE_2_5_QUIZ,
            "2.6": MODULE_2_6_QUIZ,
            "2.7": MODULE_2_7_QUIZ,
            "2.8": MODULE_2_8_QUIZ,
            "2.9": MODULE_2_9_QUIZ,
        }
        
        if mod["id"] in ch2_quiz_map:
            quiz_questions = ch2_quiz_map[mod["id"]]
            for idx, quiz_question in enumerate(quiz_questions):
                quiz_page_map[quiz_question["id"]] = len(pages)
                pages.append({
                    "type": "quiz",
                    "chapter_id": 2,
                    "module_id": mod["id"],
                    "module_title": mod["title"],
                    "quiz_question": quiz_question,
                    "question_number": idx + 1,
                    "total_questions": len(quiz_questions)
                })
    
    # Chapter 2 summary
    if ch2["summary"]:
        pages.append({
            "type": "summary",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["summary"],
            "content_html": convert_to_html(ch2["summary"])
        })
    
    # Chapter 2 action items
    if ch2["action_items"]:
        pages.append({
            "type": "action_items",
            "chapter_id": 2,
            "chapter_title": ch2["chapter_title"],
            "content": ch2["action_items"],
            "content_html": convert_to_html(ch2["action_items"])
        })
'''

# STEP 4: Update page() function around line 803 to also extract ch2:
# ch2 = extract_chapter_content(text, 2) if text else {"modules": []}

# STEP 5: Update module locking logic around line 860 to include Chapter 2 modules
MODULE_INDEX_MAP_UPDATE = '''
# Replace the module_index dict at line 860 with this expanded version:
module_index = {
    "1.1": 0, "1.2": 1, "1.3": 2, "1.4": 3, "1.5": 4, "1.6": 5,
    "2.1": 0, "2.2": 1, "2.3": 2, "2.4": 3, "2.5": 4, "2.6": 5, "2.7": 6, "2.8": 7, "2.9": 8
}.get(current_module_id, 0)

# Also update the module_ids check to be dynamic based on chapter:
current_chapter = current_page.get("chapter_id")
if current_chapter == 1:
    module_ids = ["1.1", "1.2", "1.3", "1.4", "1.5", "1.6"]
elif current_chapter == 2:
    module_ids = ["2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9"]
'''

# STEP 6: Update quiz_map in page() function around line 899 to include Chapter 2:
QUIZ_MAP_UPDATE = '''
quiz_map = {
    "1.1": MODULE_1_1_QUIZ,
    "1.2": MODULE_1_2_QUIZ,
    "1.3": MODULE_1_3_QUIZ,
    "1.4": MODULE_1_4_QUIZ,
    "1.5": MODULE_1_5_QUIZ,
    "1.6": MODULE_1_6_QUIZ,
    "2.1": MODULE_2_1_QUIZ,
    "2.2": MODULE_2_2_QUIZ,
    "2.3": MODULE_2_3_QUIZ,
    "2.4": MODULE_2_4_QUIZ,
    "2.5": MODULE_2_5_QUIZ,
    "2.6": MODULE_2_6_QUIZ,
    "2.7": MODULE_2_7_QUIZ,
    "2.8": MODULE_2_8_QUIZ,
    "2.9": MODULE_2_9_QUIZ,
}
'''

print("Chapter 2 integration code ready!")
print("\nFollow the 6 steps above to integrate Chapter 2 into main.py")

