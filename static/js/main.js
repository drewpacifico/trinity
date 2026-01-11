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
   Utility Functions
   -------------------------------------------------------------------------- */
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
