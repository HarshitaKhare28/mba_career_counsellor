/**
 * MBA Student Counselor - Chat Interface JavaScript
 * Handles all client-side chat functionality and UI interactions
 */

class MBAChatInterface {
    constructor() {
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.resetButton = document.getElementById('reset-button');
        this.exportButton = document.getElementById('export-button');
        this.chatMessages = document.getElementById('chat-messages');
        this.welcomeSection = document.getElementById('welcome-section');
        this.preferencesPanel = document.getElementById('preferences-panel');
        this.loadingOverlay = document.getElementById('loading-overlay');
        this.statusIndicator = document.getElementById('status-indicator');

        this.chatHistory = [];
        this.isLoading = false;

        this.initializeEventListeners();
        this.checkHealth();

        // Send initial greeting
        setTimeout(() => {
            this.addBotMessage(
                "Hello! 👋 I'm Alex, your MBA counselor. I'm here to help you find the perfect MBA program that matches your goals and budget. What brings you here today?"
            );
        }, 1000);
    }

    initializeEventListeners() {
        // Message input events
        this.messageInput.addEventListener('input', () => this.handleInputChange());
        this.messageInput.addEventListener('keypress', (e) => this.handleKeyPress(e));

        // Button events
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.resetButton.addEventListener('click', () => this.resetChat());
        this.exportButton.addEventListener('click', () => this.exportChat());

        // Auto-resize input
        this.messageInput.addEventListener('input', () => this.autoResizeInput());

        // Prevent form submission
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.target === this.messageInput) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    handleInputChange() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || this.isLoading;

        // Change button color based on state
        if (hasText && !this.isLoading) {
            this.sendButton.style.background = 'var(--primary-color)';
        } else {
            this.sendButton.style.background = 'var(--secondary-color)';
        }
    }

    handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!this.isLoading && this.messageInput.value.trim()) {
                this.sendMessage();
            }
        }
    }

    autoResizeInput() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;

        // Add user message to chat
        this.addUserMessage(message);
        this.messageInput.value = '';
        this.handleInputChange();

        // Show inline thinking message
        this.setLoading(true);
        const thinkingMessage = this.addThinkingMessage();

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            const data = await response.json();

            if (response.ok) {
                // Remove thinking message and add bot response
                this.removeThinkingMessage(thinkingMessage);
                this.addBotMessage(data.response, data.university_cards);

                // Update preferences if available
                if (data.preferences && Object.keys(data.preferences).length > 0) {
                    this.updatePreferences(data.preferences);
                }

                this.setOnlineStatus(true);
            } else {
                throw new Error(data.error || 'Failed to send message');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.removeThinkingMessage(thinkingMessage);
            this.showToast('Sorry, I encountered an issue. Please try again.', 'error');
            this.setOnlineStatus(false);
        } finally {
            this.setLoading(false);
        }
    }

    addUserMessage(message) {
        const messageElement = this.createMessageElement(message, 'user');
        this.appendMessage(messageElement);

        // Add to history
        this.chatHistory.push({
            type: 'user',
            message: message,
            timestamp: new Date().toISOString()
        });
    }

    addBotMessage(message, universityCards = null) {
        // Create the bot message element
        const messageElement = this.createMessageElement(message, 'bot');
        this.appendMessage(messageElement);

        // Add university cards as separate elements if provided
        if (universityCards && universityCards.length > 0) {
            // Add a small gap before cards
            setTimeout(() => {
                const cardsContainer = this.createUniversityCards(universityCards);
                const cardsWrapper = document.createElement('div');
                cardsWrapper.className = 'message bot cards-message';
                cardsWrapper.appendChild(cardsContainer);

                this.appendMessage(cardsWrapper);
            }, 500); // Small delay for better UX
        }

        // Add to history
        this.chatHistory.push({
            type: 'bot',
            message: message,
            universityCards: universityCards,
            timestamp: new Date().toISOString()
        });
    } createUniversityCards(universityCards) {
        const cardsContainer = document.createElement('div');
        cardsContainer.className = 'university-cards-container';

        universityCards.forEach(card => {
            const cardElement = document.createElement('div');
            cardElement.className = 'university-card';

            cardElement.innerHTML = `
                <div class="card-header">
                    <div class="card-title">
                        <h3>${card.name}</h3>
                        <div class="card-badges">
                            <span class="specialization-badge">${card.specialization}</span>
                            ${card.alumni_status !== undefined && card.alumni_status ?
                    '<span class="alumni-badge"><i class="fas fa-graduation-cap"></i> Alumni Status</span>' :
                    '<span class="no-alumni-badge"><i class="fas fa-times-circle"></i> No Alumni Status</span>'
                }
                        </div>
                    </div>
                    <div class="card-fees">${card.fees}</div>
                </div>
                
                <div class="card-body">
                    ${card.review_rating && card.review_rating > 0 ? `
                    <div class="card-section reviews-section">
                        <div class="section-label">
                            <i class="fas fa-star"></i>
                            Student Reviews
                        </div>
                        <div class="section-content">
                            <div class="star-rating">
                                ${(() => {
                        if (!card.review_rating || card.review_rating === 0) return '<span class="no-reviews">No reviews yet</span>';

                        const rating = card.review_rating;
                        const count = card.review_count || 0;
                        const fullStars = Math.floor(rating);
                        const hasHalfStar = rating % 1 >= 0.5;
                        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

                        let stars = '';
                        // Full stars
                        for (let i = 0; i < fullStars; i++) {
                            stars += '<i class="fas fa-star"></i>';
                        }
                        // Half star
                        if (hasHalfStar) {
                            stars += '<i class="fas fa-star-half-alt"></i>';
                        }
                        // Empty stars
                        for (let i = 0; i < emptyStars; i++) {
                            stars += '<i class="far fa-star"></i>';
                        }

                        return stars + `<span class="rating-text">${rating.toFixed(1)} (${count} reviews)</span>`;
                    })()}
                            </div>
                            <div class="review-sentiments">
                                ${card.review_sentiment && card.review_sentiment.length > 0 ?
                        card.review_sentiment.slice(0, 2).map(sentiment =>
                            `<span class="sentiment-badge">${sentiment}</span>`
                        ).join('') : ''
                    }
                            </div>
                            ${card.review_source && card.review_source !== 'Not Available' ?
                        `<div class="review-source">Source: ${card.review_source}</div>` : ''
                    }
                        </div>
                    </div>
                    ` : ''}
                    
                    <div class="card-section">
                        <div class="section-label">
                            <i class="fas fa-certificate"></i>
                            Accreditations
                        </div>
                        <div class="section-content">${card.accreditations}</div>
                    </div>
                    
                    <div class="card-section">
                        <div class="section-label">
                            <i class="fas fa-thumbs-up"></i>
                            Pros
                        </div>
                        <div class="section-content">
                            ${card.pros.map(pro => `<span class="pro-tag">${pro}</span>`).join('')}
                        </div>
                    </div>
                    
                    <!-- <div class="card-section">
                        <div class="section-label">
                            <i class="fas fa-exclamation-triangle"></i>
                            Considerations
                        </div>
                        <div class="section-content">
                            ${card.cons.map(con => `<span class="con-tag">${con}</span>`).join('')}
                        </div>
                    </div> -->
                    
                    <div class="card-section">
                        <div class="section-label">
                            <i class="fas fa-lightbulb"></i>
                            Why This Matches
                        </div>
                        <div class="section-content">
                            ${card.reasons.map(reason => `<span class="reason-tag">${reason}</span>`).join('')}
                        </div>
                    </div>
                </div>
                
                <div class="card-actions">
                    <a href="${card.website}" target="_blank" class="card-button primary">
                        <i class="fas fa-external-link-alt"></i>
                        Visit Website
                    </a>
                    <a href="${card.brochure}" target="_blank" class="card-button secondary">
                        <i class="fas fa-download"></i>
                        Download Brochure
                    </a>
                </div>
            `;

            cardsContainer.appendChild(cardElement);
        });

        return cardsContainer;
    }

    createMessageElement(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = type === 'bot' ? '<i class="fas fa-user-graduate"></i>' : '<i class="fas fa-user"></i>';

        const content = document.createElement('div');
        content.className = 'message-content';

        // Process message for better formatting
        const formattedMessage = this.formatMessage(message);
        content.innerHTML = formattedMessage;

        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = this.formatTimestamp(new Date());

        if (type === 'bot') {
            messageDiv.appendChild(avatar);
            messageDiv.appendChild(content);
            content.appendChild(timestamp);
        } else {
            messageDiv.appendChild(content);
            content.appendChild(timestamp);
            messageDiv.appendChild(avatar);
        }

        return messageDiv;
    }

    formatMessage(message) {
        // Convert markdown-like formatting to HTML
        let formatted = message
            // Bold text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic text
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Line breaks
            .replace(/\n/g, '<br>')
            // Links (basic)
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>')
            // Emojis (preserve as-is)
            .replace(/:\)/g, '😊')
            .replace(/:\(/g, '😞')
            .replace(/:D/g, '😄');

        // Format lists (simple)
        if (formatted.includes('1.') || formatted.includes('-')) {
            formatted = formatted
                .replace(/^\d+\.\s+(.+)$/gm, '<li>$1</li>')
                .replace(/^-\s+(.+)$/gm, '<li>$1</li>');

            if (formatted.includes('<li>')) {
                formatted = '<ul>' + formatted + '</ul>';
            }
        }

        return formatted;
    }

    formatTimestamp(date) {
        return date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    appendMessage(messageElement) {
        // Show chat area if first message
        if (!this.chatMessages.classList.contains('active')) {
            this.chatMessages.classList.add('active');
            this.welcomeSection.style.display = 'none';
        }

        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    updatePreferences(preferences) {
        if (!preferences || Object.keys(preferences).length === 0) {
            return;
        }

        this.preferencesPanel.classList.add('active');
        const content = this.preferencesPanel.querySelector('#preferences-content');

        // Clear existing content
        content.innerHTML = '';

        // Add preference items
        Object.entries(preferences).forEach(([key, value]) => {
            const item = document.createElement('div');
            item.className = 'preference-item';

            const icon = this.getPreferenceIcon(key);
            const label = this.formatPreferenceLabel(key);
            const displayValue = Array.isArray(value) ? value.join(', ') : value;

            item.innerHTML = `
                <i class="fas fa-${icon}"></i>
                <span><strong>${label}:</strong> ${displayValue}</span>
            `;

            content.appendChild(item);
        });
    }

    getPreferenceIcon(key) {
        const icons = {
            specialization: 'graduation-cap',
            budget: 'dollar-sign',
            career_goal: 'bullseye',
            priorities: 'star',
            location_preference: 'map-marker-alt',
            experience_level: 'user-clock'
        };
        return icons[key] || 'cog';
    }

    formatPreferenceLabel(key) {
        const labels = {
            specialization: 'Specialization',
            budget: 'Budget',
            career_goal: 'Career Goal',
            priorities: 'Priorities',
            location_preference: 'Location',
            experience_level: 'Experience'
        };
        return labels[key] || key.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    setLoading(loading) {
        this.isLoading = loading;
        this.sendButton.disabled = loading || !this.messageInput.value.trim();
        this.messageInput.disabled = loading;

        if (loading) {
            this.sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        } else {
            this.sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
        }
    }

    addThinkingMessage() {
        const messageElement = this.createMessageElement('', 'bot');
        messageElement.classList.add('thinking-message');

        const content = messageElement.querySelector('.message-content');
        content.innerHTML = `
            <div class="thinking-indicator">
                <div class="thinking-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span class="thinking-text">Alex is thinking...</span>
            </div>
        `;

        this.chatMessages.appendChild(messageElement);
        this.scrollToBottom();

        return messageElement;
    }

    removeThinkingMessage(thinkingElement) {
        if (thinkingElement && thinkingElement.parentNode) {
            thinkingElement.parentNode.removeChild(thinkingElement);
        }
    }

    setOnlineStatus(online) {
        this.statusIndicator.className = `status-indicator ${online ? 'online' : 'offline'}`;
        this.statusIndicator.style.background = online ? 'var(--success-color)' : 'var(--error-color)';
    }

    async resetChat() {
        if (this.isLoading) return;

        if (this.chatHistory.length > 0) {
            if (!confirm('Are you sure you want to start a new conversation? This will clear your current chat.')) {
                return;
            }
        }

        this.setLoading(true);

        try {
            const response = await fetch('/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                // Clear UI
                this.chatMessages.innerHTML = '';
                this.chatMessages.classList.remove('active');
                this.preferencesPanel.classList.remove('active');
                this.welcomeSection.style.display = 'block';
                this.chatHistory = [];

                this.showToast('New conversation started!', 'success');

                // Send welcome message after reset
                setTimeout(() => {
                    this.addBotMessage(
                        "Hello again! 👋 I'm ready to help you with a fresh conversation about MBA programs. What would you like to explore today?"
                    );
                }, 1000);
            } else {
                throw new Error('Failed to reset chat');
            }
        } catch (error) {
            console.error('Reset error:', error);
            this.showToast('Failed to reset chat. Please refresh the page.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    exportChat() {
        if (this.chatHistory.length === 0) {
            this.showToast('No conversation to export!', 'error');
            return;
        }

        const chatData = {
            title: 'MBA Counselor Conversation',
            timestamp: new Date().toISOString(),
            messages: this.chatHistory
        };

        const blob = new Blob([JSON.stringify(chatData, null, 2)], {
            type: 'application/json'
        });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `mba-chat-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        this.showToast('Chat exported successfully!', 'success');
    }

    async checkHealth() {
        try {
            const response = await fetch('/health');
            const data = await response.json();

            if (response.ok && data.status === 'healthy') {
                this.setOnlineStatus(true);
            } else {
                throw new Error(data.error || 'Health check failed');
            }
        } catch (error) {
            console.error('Health check failed:', error);
            this.setOnlineStatus(false);
            this.showToast('Connection issues detected. Some features may not work properly.', 'error');
        }
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById(`${type}-toast`);
        const messageElement = document.getElementById(`${type}-message`);

        if (toast && messageElement) {
            messageElement.textContent = message;
            toast.classList.add('active');

            // Auto-hide after 5 seconds
            setTimeout(() => {
                toast.classList.remove('active');
            }, 5000);
        }
    }
}

// Global functions for suggestion buttons and toast management
function sendSuggestion(message) {
    if (window.chatInterface) {
        window.chatInterface.messageInput.value = message;
        window.chatInterface.handleInputChange();
        window.chatInterface.sendMessage();
    }
}

function closeToast() {
    document.querySelectorAll('.toast').forEach(toast => {
        toast.classList.remove('active');
    });
}

// Initialize the chat interface when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.chatInterface = new MBAChatInterface();

    // Add smooth scrolling for better UX
    document.documentElement.style.scrollBehavior = 'smooth';

    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible' && window.chatInterface) {
            // Check health when page becomes visible
            window.chatInterface.checkHealth();
        }
    });

    // Handle online/offline events
    window.addEventListener('online', () => {
        if (window.chatInterface) {
            window.chatInterface.setOnlineStatus(true);
            window.chatInterface.showToast('Connection restored!', 'success');
        }
    });

    window.addEventListener('offline', () => {
        if (window.chatInterface) {
            window.chatInterface.setOnlineStatus(false);
            window.chatInterface.showToast('Connection lost. Please check your internet.', 'error');
        }
    });
});

// Prevent zoom on iOS
document.addEventListener('touchstart', (event) => {
    if (event.touches.length > 1) {
        event.preventDefault();
    }
});

let lastTouchEnd = 0;
document.addEventListener('touchend', (event) => {
    const now = (new Date()).getTime();
    if (now - lastTouchEnd <= 300) {
        event.preventDefault();
    }
    lastTouchEnd = now;
}, false);