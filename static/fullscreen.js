// Fullscreen and responsive behavior for Nyaay Saathi

// Function to handle fullscreen for desktop 
function toggleFullScreen() {
    const elem = document.documentElement;
    
    if (!document.fullscreenElement && !document.mozFullScreenElement &&
        !document.webkitFullscreenElement && !document.msFullscreenElement) {
        // Enter fullscreen
        if (elem.requestFullscreen) {
            elem.requestFullscreen();
        } else if (elem.msRequestFullscreen) {
            elem.msRequestFullscreen();
        } else if (elem.mozRequestFullScreen) {
            elem.mozRequestFullScreen();
        } else if (elem.webkitRequestFullscreen) {
            elem.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
        }
    } else {
        // Exit fullscreen
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        } else if (document.mozCancelFullScreen) {
            document.mozCancelFullScreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        }
    }
}

// Add fullscreen button to desktop view
function addFullscreenButton() {
    // Only add on desktop
    if (window.innerWidth >= 992) {
        const header = document.querySelector('.chat-header');
        
        // Check if button already exists
        if (!document.getElementById('fullscreen-btn') && header) {
            const fullscreenBtn = document.createElement('button');
            fullscreenBtn.id = 'fullscreen-btn';
            fullscreenBtn.className = 'reset-btn ms-2';
            fullscreenBtn.innerHTML = '<i class="fas fa-expand"></i>';
            fullscreenBtn.title = 'Toggle Fullscreen';
            fullscreenBtn.addEventListener('click', toggleFullScreen);
            
            // Add to header next to other control buttons
            const controlsDiv = header.querySelector('div.d-flex.align-items-center');
            if (controlsDiv) {
                controlsDiv.appendChild(fullscreenBtn);
            }
            
            // Update icon when fullscreen state changes
            document.addEventListener('fullscreenchange', updateFullscreenIcon);
            document.addEventListener('webkitfullscreenchange', updateFullscreenIcon);
            document.addEventListener('mozfullscreenchange', updateFullscreenIcon);
            document.addEventListener('MSFullscreenChange', updateFullscreenIcon);
        }
    }
}

// Update fullscreen button icon based on state
function updateFullscreenIcon() {
    const button = document.getElementById('fullscreen-btn');
    if (button) {
        if (document.fullscreenElement || document.webkitFullscreenElement || 
            document.mozFullScreenElement || document.msFullscreenElement) {
            button.innerHTML = '<i class="fas fa-compress"></i>';
        } else {
            button.innerHTML = '<i class="fas fa-expand"></i>';
        }
    }
}

// Fix height issues on mobile devices
function adjustHeight() {
    // Get actual viewport height
    const vh = window.innerHeight * 0.01;
    // Set the --vh custom property to the root of the document
    document.documentElement.style.setProperty('--vh', `${vh}px`);
    
    // Also adjust the chat body height for better display
    const chatBody = document.getElementById('chat-body');
    const chatContainer = document.querySelector('.chat-container');
    
    if (chatBody && chatContainer) {
        const headerHeight = document.querySelector('.chat-header')?.offsetHeight || 0;
        const featuresHeight = document.querySelector('.features-row')?.offsetHeight || 0;
        const inputHeight = document.querySelector('.chat-input')?.offsetHeight || 0;
        
        const availableHeight = window.innerHeight - headerHeight - featuresHeight - inputHeight;
        chatBody.style.height = `${availableHeight}px`;
        
        // Scroll to bottom to show latest messages
        chatBody.scrollTop = chatBody.scrollHeight;
    }
}

// Handle resize events for responsive behavior
function handleResize() {
    addFullscreenButton();
    adjustHeight();
}

// Handle message display optimization for mobile
function optimizeMessagesForMobile() {
    // Limit message width on small screens
    const isMobile = window.innerWidth < 768;
    const messages = document.querySelectorAll('.message');
    
    messages.forEach(message => {
        if (isMobile) {
            message.style.maxWidth = '85%';
        } else {
            message.style.maxWidth = '80%';
        }
    });
}

// Fix modals position on mobile
function fixModalsOnMobile() {
    const modals = document.querySelectorAll('.modal-content');
    
    modals.forEach(modal => {
        // Make sure modals are properly positioned and sized on mobile
        if (window.innerWidth < 768) {
            modal.style.width = '95%';
            modal.style.maxHeight = '90vh';
            modal.style.overflow = 'auto';
        }
    });
}

// Detect if device is touch capable and add specific class
function detectTouchDevice() {
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
        document.body.classList.add('touch-device');
    }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Apply all responsive enhancements
    addFullscreenButton();
    adjustHeight();
    optimizeMessagesForMobile();
    fixModalsOnMobile();
    detectTouchDevice();
    
    // Set up event listeners
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', adjustHeight);
    
    // Set interval to check and adjust height occasionally
    // (helps with mobile browsers where address bar may hide/show)
    setInterval(adjustHeight, 1000);
});