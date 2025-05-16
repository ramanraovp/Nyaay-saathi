document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const chatBody = document.getElementById('chat-body');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const loader = document.querySelector('.loader');
    
    // Global variables
    let currentLanguage = 'English';
    let simplifyEnabled = false;
    
    // Simple send function
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;
        
        // Add user message to chat
        const userMessageDiv = document.createElement('div');
        userMessageDiv.classList.add('message', 'user-message');
        userMessageDiv.innerHTML = `<p>${message}</p>`;
        chatBody.appendChild(userMessageDiv);
        
        // Store in message history if needed
        if (typeof allMessages !== 'undefined') {
            allMessages.push({
                role: 'user',
                content: message
            });
        }
        
        // Clear input
        userInput.value = '';
        
        // Show loader
        loader.style.display = 'block';
        chatBody.scrollTop = chatBody.scrollHeight;
        
        // Send to API
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: message,
                simplify: simplifyEnabled,
                language: currentLanguage
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loader
            loader.style.display = 'none';
            
            // Add bot response to chat
            const botMessageDiv = document.createElement('div');
            botMessageDiv.classList.add('message', 'bot-message');
            
            if (data.error) {
                botMessageDiv.innerHTML = `
                    <p>Sorry, I encountered an error. Please try again.</p>
                    <p class="disclaimer">I am an AI assistant and not a licensed legal advisor. Please consult a lawyer for serious or urgent matters.</p>
                `;
            } else {
                const botMessage = data.response;
                
                // Check if message contains disclaimer
                if (botMessage.includes("I am an AI assistant and not a licensed legal advisor")) {
                    // Split the message and disclaimer
                    const parts = botMessage.split("I am an AI assistant and not a licensed legal advisor");
                    const mainMessage = parts[0];
                    
                    botMessageDiv.innerHTML = `
                        <p>${mainMessage}</p>
                        <p class="disclaimer">I am an AI assistant and not a licensed legal advisor${parts[1] || ". Please consult a lawyer for serious or urgent matters."}</p>
                    `;
                } else {
                    botMessageDiv.innerHTML = `
                        <p>${botMessage}</p>
                        <p class="disclaimer">I am an AI assistant and not a licensed legal advisor. Please consult a lawyer for serious or urgent matters.</p>
                    `;
                }
                
                // Store in message history if needed
                if (typeof allMessages !== 'undefined') {
                    allMessages.push({
                        role: 'assistant',
                        content: botMessage
                    });
                }
            }
            
            chatBody.appendChild(botMessageDiv);
            chatBody.scrollTop = chatBody.scrollHeight;
        })
        .catch(error => {
            // Hide loader
            loader.style.display = 'none';
            
            // Show error message
            const errorDiv = document.createElement('div');
            errorDiv.classList.add('message', 'bot-message');
            errorDiv.innerHTML = `
                <p>Sorry, I encountered a network error. Please try again.</p>
                <p class="disclaimer">I am an AI assistant and not a licensed legal advisor. Please consult a lawyer for serious or urgent matters.</p>
            `;
            chatBody.appendChild(errorDiv);
            console.error('Error:', error);
        });
    }
    
    // Add event listeners, but only if they don't already exist
    // For the send button
    if (sendBtn && !sendBtn._hasClickListener) {
        sendBtn.addEventListener('click', sendMessage);
        sendBtn._hasClickListener = true;
    }
    
    // For the input field
    if (userInput && !userInput._hasEnterListener) {
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        userInput._hasEnterListener = true;
    }
    
    // For question chips - IMPORTANT FIX FOR DOUBLE-CLICK ISSUE
    const questionChips = document.querySelectorAll('.question-chip');
    if (questionChips && questionChips.length > 0) {
        // First, remove any existing click listeners by cloning all chips
        questionChips.forEach(chip => {
            // Create a clone of the chip to remove all event listeners
            const newChip = chip.cloneNode(true);
            
            // Add a single click handler to the clone
            newChip.addEventListener('click', function(e) {
                e.stopPropagation(); // Prevent event bubbling
                
                // Add a flag to prevent double execution
                if (this._isProcessing) return;
                this._isProcessing = true;
                
                // Process the click
                console.log('Question chip clicked: ' + this.textContent);
                userInput.value = this.textContent;
                sendMessage();
                
                // Reset the flag after a delay
                setTimeout(() => {
                    this._isProcessing = false;
                }, 500);
            });
            
            // Replace the original chip with the clone
            if (chip.parentNode) {
                chip.parentNode.replaceChild(newChip, chip);
            }
        });
        
        console.log('Fixed question chips click handlers');
    }
    
    // Make these functions globally available
    window.sendMessage = sendMessage;
    
    console.log("Fix.js has been loaded and applied to fix send functionality");
    
    // Debugging helper - add this only if you're still having issues
    window.debugDoubleClick = function() {
        console.log('Current question chips:');
        document.querySelectorAll('.question-chip').forEach((chip, index) => {
            console.log(`Chip #${index}: ${chip.textContent}`);
            
            // List all event listeners (this is a simplified approach)
            const events = getEventListeners(chip);
            console.log(`Event listeners:`, events);
        });
    };
});
