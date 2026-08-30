// my-test-framework/src/framework/ai/aicompanion_v2/static/script.js

const API_BASE = '';

// 状态管理
const state = {
    currentSessionId: null,
    messages: [],
    isStreaming: false,
};

// DOM元素
const elements = {
    chatMessages: document.getElementById('chatMessages'),
    messageInput: document.getElementById('messageInput'),
    sendButton: document.getElementById('sendButton'),
    sessionList: document.getElementById('sessionList'),
    newSessionBtn: document.getElementById('newSession'),
    updateSettingsBtn: document.getElementById('updateSettings'),
    aiName: document.getElementById('aiName'),
    aiPersonality: document.getElementById('aiPersonality'),
    aiRules: document.getElementById('aiRules'),
    currentSessionName: document.getElementById('currentSessionName'),
};

// ========== API调用 ==========

async function fetchSessions() {
    try {
        const response = await fetch(`${API_BASE}/api/sessions`);
        if (!response.ok) throw new Error('Failed to fetch sessions');
        return await response.json();
    } catch (error) {
        console.error('Error fetching sessions:', error);
        return [];
    }
}

async function createSession(data) {
    try {
        const response = await fetch(`${API_BASE}/api/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error('Failed to create session');
        return await response.json();
    } catch (error) {
        console.error('Error creating session:', error);
        return null;
    }
}

async function updateSession(sessionId, data) {
    try {
        const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error('Failed to update session');
        return await response.json();
    } catch (error) {
        console.error('Error updating session:', error);
        return null;
    }
}

async function deleteSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
            method: 'DELETE',
        });
        if (!response.ok) throw new Error('Failed to delete session');
        return await response.json();
    } catch (error) {
        console.error('Error deleting session:', error);
        return null;
    }
}

async function getSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
        if (!response.ok) throw new Error('Failed to get session');
        return await response.json();
    } catch (error) {
        console.error('Error getting session:', error);
        return null;
    }
}

// ========== 流式聊天 ==========

async function sendMessageStream(content) {
    if (state.isStreaming) return;
    state.isStreaming = true;

    // 添加用户消息
    addMessage('user', content);
    elements.messageInput.value = '';

    // 创建助手消息占位
    const messageDiv = createMessageElement('assistant');
    const contentDiv = messageDiv.querySelector('.message-content');
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();

    let fullResponse = '';
    let thinkingContent = '';
    let hasThinking = false;

    try {
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: content,
                session_id: state.currentSessionId,
            }),
        });

        if (!response.ok) throw new Error('Stream request failed');

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    if (data === '[DONE]') continue;

                    try {
                        const chunk = JSON.parse(data);
                        
                        if (chunk.type === 'chunk') {
                            fullResponse += chunk.content || '';
                            contentDiv.textContent = fullResponse;
                            scrollToBottom();
                        } else if (chunk.type === 'complete') {
                            state.currentSessionId = chunk.session_id;
                            fullResponse = chunk.full_response;
                            thinkingContent = chunk.thinking || '';
                            contentDiv.textContent = fullResponse;
                            
                            // 如果有思考内容，添加思考折叠
                            if (thinkingContent) {
                                const thinkingDiv = document.createElement('div');
                                thinkingDiv.className = 'message-thinking';
                                const details = document.createElement('details');
                                const summary = document.createElement('summary');
                                summary.textContent = '💭 思考过程';
                                const content = document.createElement('p');
                                content.textContent = thinkingContent;
                                details.appendChild(summary);
                                details.appendChild(content);
                                thinkingDiv.appendChild(details);
                                messageDiv.appendChild(thinkingDiv);
                            }
                            
                            // 更新会话名称显示
                            updateSessionInfo();
                            // 刷新会话列表
                            loadSessions();
                        }
                    } catch (e) {
                        console.error('Error parsing chunk:', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error in stream:', error);
        contentDiv.textContent = '❌ 发生错误: ' + error.message;
    }

    state.isStreaming = false;
    scrollToBottom();
}

// ========== UI更新 ==========

function addMessage(role, content) {
    const messageDiv = createMessageElement(role);
    messageDiv.querySelector('.message-content').textContent = content;
    elements.chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function createMessageElement(role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.innerHTML = `<div class="message-content"></div>`;
    return div;
}

function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function clearMessages() {
    elements.chatMessages.innerHTML = '';
    state.messages = [];
}

function loadMessages(sessionData) {
    clearMessages();
    if (sessionData && sessionData.messages) {
        for (const msg of sessionData.messages) {
            addMessage(msg.role, msg.content);
        }
    }
    updateSessionInfo();
}

function updateSessionInfo() {
    if (state.currentSessionId) {
        elements.currentSessionName.textContent = `会话: ${state.currentSessionId.slice(0, 8)}...`;
    } else {
        elements.currentSessionName.textContent = '会话: 无';
    }
}

// ========== 会话列表 ==========

async function loadSessions() {
    const sessions = await fetchSessions();
    renderSessionList(sessions);
}

function renderSessionList(sessions) {
    elements.sessionList.innerHTML = '';
    if (sessions.length === 0) {
        elements.sessionList.innerHTML = '<p style="color: #999; font-size: 13px;">暂无会话</p>';
        return;
    }
    
    for (const session of sessions) {
        const item = document.createElement('div');
        item.className = 'session-item';
        if (session.id === state.currentSessionId) {
            item.classList.add('active');
        }
        
        const nameSpan = document.createElement('span');
        nameSpan.className = 'session-name';
        nameSpan.textContent = session.session_name || session.id.slice(0, 8);
        nameSpan.title = `创建: ${new Date(session.created_at).toLocaleString()}`;
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'delete-btn';
        deleteBtn.textContent = '×';
        deleteBtn.title = '删除会话';
        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (confirm('确定要删除这个会话吗？')) {
                await deleteSession(session.id);
                if (state.currentSessionId === session.id) {
                    state.currentSessionId = null;
                    clearMessages();
                }
                loadSessions();
            }
        });
        
        item.appendChild(nameSpan);
        item.appendChild(deleteBtn);
        
        item.addEventListener('click', async () => {
            const data = await getSession(session.id);
            if (data) {
                state.currentSessionId = session.id;
                loadMessages(data);
                // 更新设置表单
                elements.aiName.value = data.nick_name;
                elements.aiPersonality.value = data.nature;
                // 更新会话列表高亮
                loadSessions();
            }
        });
        
        elements.sessionList.appendChild(item);
    }
}

// ========== 事件处理 ==========

// 发送消息
async function handleSend() {
    const content = elements.messageInput.value.trim();
    if (!content || state.isStreaming) return;
    await sendMessageStream(content);
}

// 新建会话
async function handleNewSession() {
    const result = await createSession({
        nick_name: elements.aiName.value,
        nature: elements.aiPersonality.value,
        extra_rules: elements.aiRules.value,
    });
    if (result) {
        state.currentSessionId = result.session_id;
        clearMessages();
        loadSessions();
        updateSessionInfo();
        elements.messageInput.focus();
    }
}

// 更新设置
async function handleUpdateSettings() {
    if (!state.currentSessionId) {
        alert('请先创建或选择一个会话');
        return;
    }
    
    const result = await updateSession(state.currentSessionId, {
        nick_name: elements.aiName.value,
        nature: elements.aiPersonality.value,
        extra_rules: elements.aiRules.value,
    });
    if (result) {
        alert('设置已更新！');
    }
}

// ========== 键盘事件 ==========

elements.messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
    }
});

// ========== 按钮事件 ==========

elements.sendButton.addEventListener('click', handleSend);
elements.newSessionBtn.addEventListener('click', handleNewSession);
elements.updateSettingsBtn.addEventListener('click', handleUpdateSettings);

// ========== 初始化 ==========

async function init() {
    await loadSessions();
    
    // 如果有会话，加载第一个
    const sessions = await fetchSessions();
    if (sessions.length > 0) {
        state.currentSessionId = sessions[0].id;
        const data = await getSession(sessions[0].id);
        if (data) {
            loadMessages(data);
            elements.aiName.value = data.nick_name;
            elements.aiPersonality.value = data.nature;
        }
        loadSessions();
    }
}

init();

// 检测流式传输状态
console.log('AI智能伴侣已启动！');