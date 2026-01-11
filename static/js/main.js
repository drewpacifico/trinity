/* ============================================================================
   Trinity Training Guide - Main JavaScript
   ============================================================================ */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize quiz functionality
    initQuiz();

    // Initialize keyboard navigation
    initKeyboardNav();
});

/* --------------------------------------------------------------------------
   Quiz Functionality
   -------------------------------------------------------------------------- */
function initQuiz() {
    const quizForm = document.querySelector('.quiz-form');
    if (!quizForm) return;

    const options = quizForm.querySelectorAll('.quiz-option');
    const submitBtn = quizForm.querySelector('.quiz-submit-btn');

    // Handle option selection
    options.forEach(option => {
        option.addEventListener('click', function() {
            // Clear previous selection
            options.forEach(opt => opt.classList.remove('selected'));
            // Select this option
            this.classList.add('selected');
            // Check the radio button
            const radio = this.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;
            // Enable submit button
            if (submitBtn) submitBtn.disabled = false;
        });
    });
}

/* --------------------------------------------------------------------------
   Keyboard Navigation
   -------------------------------------------------------------------------- */
function initKeyboardNav() {
    document.addEventListener('keydown', function(e) {
        // Don't navigate if user is typing in an input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        const prevBtn = document.querySelector('.nav-btn.prev:not(.disabled)');
        const nextBtn = document.querySelector('.nav-btn.next:not(.disabled)');

        // Left arrow or A key - go to previous
        if (e.key === 'ArrowLeft' || e.key === 'a' || e.key === 'A') {
            if (prevBtn) {
                e.preventDefault();
                prevBtn.click();
            }
        }

        // Right arrow or D key - go to next
        if (e.key === 'ArrowRight' || e.key === 'd' || e.key === 'D') {
            if (nextBtn) {
                e.preventDefault();
                nextBtn.click();
            }
        }
    });
}

/* --------------------------------------------------------------------------
   Quiz Answer Submission (AJAX)
   -------------------------------------------------------------------------- */
function submitQuizAnswer(moduleId, questionId, selectedIndex, answerOrder) {
    const form = document.querySelector('.quiz-form');
    const csrfToken = form.querySelector('input[name="csrf_token"]')?.value;

    fetch('/submit-quiz-answer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            module_id: moduleId,
            question_id: questionId,
            selected_index: selectedIndex,
            answer_order: answerOrder
        })
    })
    .then(response => response.json())
    .then(data => {
        showQuizFeedback(data.is_correct, data.explanation, selectedIndex);
    })
    .catch(error => {
        console.error('Error submitting quiz answer:', error);
    });
}

function showQuizFeedback(isCorrect, explanation, selectedIndex) {
    const options = document.querySelectorAll('.quiz-option');
    const feedbackEl = document.querySelector('.quiz-feedback');

    // Mark selected option as correct/incorrect
    options.forEach((opt, index) => {
        if (index === selectedIndex) {
            opt.classList.add(isCorrect ? 'correct' : 'incorrect');
        }
    });

    // Show feedback
    if (feedbackEl) {
        feedbackEl.classList.remove('hidden');
        feedbackEl.classList.add(isCorrect ? 'correct' : 'incorrect');

        const titleEl = feedbackEl.querySelector('.quiz-feedback-title');
        const contentEl = feedbackEl.querySelector('.quiz-feedback-content');

        if (titleEl) {
            titleEl.innerHTML = isCorrect
                ? '<span>✓</span> Correct!'
                : '<span>✗</span> Incorrect';
        }

        if (contentEl && explanation) {
            contentEl.textContent = explanation;
        }
    }

    // Disable further interaction
    options.forEach(opt => {
        opt.style.pointerEvents = 'none';
    });

    const submitBtn = document.querySelector('.quiz-submit-btn');
    if (submitBtn) {
        submitBtn.style.display = 'none';
    }
}

/* --------------------------------------------------------------------------
   Utility Functions
   -------------------------------------------------------------------------- */
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
