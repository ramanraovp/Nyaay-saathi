// Create a file called targeted-scroll-fix.js

(function() {
    // Run when page is interactive
    if (document.readyState === 'interactive' || document.readyState === 'complete') {
        applyFix();
    } else {
        document.addEventListener('DOMContentLoaded', applyFix);
    }
    
    function applyFix() {
        console.log("Applying targeted scroll fix");
        
        // Get key elements
        const chatBody = document.getElementById('chat-body');
        if (!chatBody) {
            console.error('Chat body not found');
            return;
        }
        
        // Track if user is viewing history
        let isViewingHistory = false;
        
        // Threshold for detecting if user has scrolled up (in pixels)
        const SCROLL_THRESHOLD = 150;
        
        // Check if user is viewing history
        function checkViewingHistory() {
            if (!chatBody) return false;
            
            const maxScroll = chatBody.scrollHeight - chatBody.clientHeight;
            const currentPosition = chatBody.scrollTop;
            const distanceFromBottom = maxScroll - currentPosition;
            
            return distanceFromBottom > SCROLL_THRESHOLD;
        }
        
        // Update viewing state when user scrolls
        function onScroll() {
            isViewingHistory = checkViewingHistory();
        }
        
        // Add our scroll listener with high priority
        chatBody.addEventListener('scroll', onScroll, { capture: true });
        
        // Function to check if we should allow auto-scrolling
        function shouldAutoScroll() {
            return !isViewingHistory;
        }
        
        // Function to safely scroll to bottom if appropriate
        function safeScrollToBottom() {
            if (shouldAutoScroll()) {
                if (chatBody) {
                    chatBody.scrollTop = chatBody.scrollHeight;
                }
            }
        }
        
        // DIRECT FIX: Find all places in the code that call scrollTop = scrollHeight
        // and intercept them with our logic
        
        // 1. Create a proxy for chatBody's scrollTop property
        Object.defineProperty(chatBody, '_actualScrollTop', {
            set: function(v) { 
                this._scrollTopVal = v; 
            },
            get: function() { 
                return this._scrollTopVal || 0; 
            }
        });
        
        // 2. Override the scrollTop property to intercept auto-scrolling attempts
        let originalScrollTop = chatBody.scrollTop;
        Object.defineProperty(chatBody, 'scrollTop', {
            set: function(value) {
                // Only allow scroll to bottom if not viewing history or explicitly requested
                if (value === this.scrollHeight) {
                    if (shouldAutoScroll()) {
                        originalScrollTop = value;
                        this._actualScrollTop = value;
                    }
                } else {
                    // Always allow manual scrolling to other positions
                    originalScrollTop = value;
                    this._actualScrollTop = value;
                }
            },
            get: function() {
                return originalScrollTop;
            }
        });
        
        // 3. Force reset when user sends a message
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');
        
        function resetScrollState() {
            isViewingHistory = false;
            chatBody.scrollTop = chatBody.scrollHeight;
        }
        
        if (sendBtn) {
            // We use capture to ensure our handler runs first
            sendBtn.addEventListener('click', resetScrollState, { capture: true });
        }
        
        if (userInput) {
            userInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    resetScrollState();
                }
            }, { capture: true });
        }
        
        // 4. Monitor for changes and apply our scroll logic
        const observer = new MutationObserver(function(mutations) {
            safeScrollToBottom();
        });
        
        observer.observe(chatBody, { 
            childList: true, 
            subtree: true 
        });
        
        console.log("Targeted scroll fix applied successfully");
    }
})();