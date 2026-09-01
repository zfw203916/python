// ============================================================
// 配置
// ============================================================
const API_BASE = 'http://127.0.0.1:8000';

// ============================================================
// DOM 引用
// ============================================================
const messageList = document.getElementById('messageList');
const msgInput = document.getElementById('msgInput');
const sendBtn = document.getElementById('sendBtn');
const newGameBtn = document.getElementById('newGameBtn');
const sessionDisplay = document.getElementById('sessionDisplay');
const statusBadge = document.getElementById('statusBadge');
const recordList = document.getElementById('recordList');
const recordCount = document.getElementById('recordCount');

// 规则相关DOM
const rulesInput = document.getElementById('rulesInput');
const updateRulesBtn = document.getElementById('updateRulesBtn');
const rulesDisplay = document.getElementById('rulesDisplay');
const rulesText = document.getElementById('rulesText');

// 设置相关DOM
const aiName = document.getElementById('aiName');
const aiPersonality = document.getElementById('aiPersonality');

// 默认规则
const defaultRules = `1、每次只回1条消息
2、禁止任何场景或状态描述性文字
3、匹配用户的语言
4、回复简短，像微信聊天一样
5、有需要的话可以用🩷 💞等emoji表情
6、用符合伴侣性格的方式对话
7、回复的内容，要充分体现伴侣的性格特征`;

// 状态管理
let currentSessionId = null;
let messageHistory = [];
let sessionRecords = [];

// ============================================================
// 工具函数
// ============================================================
function getTime() {
    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `${pad(now.getHours())}:${pad(now.getMinutes())}`;
}

function getFullTime() {
    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}

function addMessage(role, content, extra = '') {
    const isUser = role === 'user';
    const avatar = isUser ? '👤' : '🤖';
    const time = getTime();
    const timeFull = getFullTime();

    const div = document.createElement('div');
    div.className = `message ${role}`;

    div.innerHTML = `
        <div class="avatar">${avatar}</div>
        <div>
            <div class="bubble">${content}</div>
            <span class="time-tag">${timeFull}</span>
            ${extra ? `<span class="time-tag" style="color:#667eea;">${extra}</span>` : ''}
        </div>
    `;

    messageList.appendChild(div);
    messageList.scrollTop = messageList.scrollHeight;

    messageHistory.push({ role, content, time: timeFull });
}

function setStatus(text, type = 'online') {
    const colors = {
        online: '#00b894',
        offline: '#ff6b6b',
        loading: '#fdcb6e'
    };
    statusBadge.textContent = `● ${text}`;
    statusBadge.style.color = colors[type] || '#00b894';
}

function updateSessionUI(sessionId) {
    currentSessionId = sessionId;
    if (sessionId) {
        sessionDisplay.textContent = `会话: ${sessionId.slice(0, 12)}...`;
        setStatus('在线', 'online');
        msgInput.disabled = false;
        sendBtn.disabled = false;
        msgInput.focus();
    } else {
        sessionDisplay.textContent = '会话: 未创建';
        setStatus('离线', 'offline');
        msgInput.disabled = true;
        sendBtn.disabled = true;
    }
}

// ============================================================
// 通知函数
// ============================================================
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = 'notification';
    
    const colors = {
        success: '#52c41a',
        error: '#ff4d4f',
        info: '#1890ff'
    };
    
    notification.style.background = colors[type] || colors.success;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// ============================================================
// 规则相关函数
// ============================================================
function displayRules(rules) {
    if (rules) {
        rulesDisplay.style.display = 'block';
        rulesText.textContent = rules;
    } else {
        rulesDisplay.style.display = 'none';
        rulesText.textContent = '';
    }
}

async function updateRules() {
    if (!currentSessionId) {
        showNotification('请先创建或选择一个会话', 'error');
        return;
    }
    
    const newRules = rulesInput.value.trim();
    
    try {
        const response = await fetch(`${API_BASE}/api/sessions/${currentSessionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                extra_rules: newRules
            })
        });
        
        if (response.ok) {
            showNotification('✅ 行为规则已更新！', 'success');
            displayRules(newRules);
        } else {
            showNotification('❌ 更新失败，请重试', 'error');
        }
    } catch (error) {
        console.error('更新规则失败:', error);
        showNotification('❌ 网络错误：' + error.message, 'error');
    }
}

// ============================================================
// API 调用
// ============================================================

// 创建会话
async function createSession() {
    setStatus('连接中…', 'loading');
    
    try {
        const response = await fetch(`${API_BASE}/api/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nick_name: aiName.value || '小甜甜',
                nature: aiPersonality.value || '活泼开朗的台湾姑娘',
                extra_rules: rulesInput.value || defaultRules
            })
        });
        
        const data = await response.json();
        
        if (data.session_id) {
            updateSessionUI(data.session_id);
            addMessage('assistant', '✅ 新会话已创建！<br>开始你的对话吧 🚀');
            
            // 设置规则
            rulesInput.value = defaultRules;
            displayRules(defaultRules);
            
            return data.session_id;
        } else {
            addMessage('assistant', `❌ 创建会话失败`);
            updateSessionUI(null);
            return null;
        }
    } catch (error) {
        console.error('创建会话失败:', error);
        addMessage('assistant', `❌ 网络错误: ${error.message}`);
        updateSessionUI(null);
        return null;
    }
}

// 获取所有会话
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

// 获取单个会话
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

// 删除会话
async function deleteSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete session');
        return await response.json();
    } catch (error) {
        console.error('Error deleting session:', error);
        return null;
    }
}

// 发送消息（流式）
async function sendMessageStream(content) {
    if (!currentSessionId) {
        addMessage('assistant', '⚠️ 请先点击「新建会话」创建会话');
        return;
    }

    // 添加用户消息
    addMessage('user', content);
    msgInput.value = '';
    msgInput.style.height = 'auto';
    sendBtn.disabled = true;

    // 创建助手消息占位
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="avatar">🤖</div>
        <div>
            <div class="bubble" id="ai-response">思考中...</div>
            <span class="time-tag"></span>
        </div>
    `;
    messageList.appendChild(messageDiv);
    messageList.scrollTop = messageList.scrollHeight;

    let fullResponse = '';
    let thinkingContent = '';

    try {
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: content,
                session_id: currentSessionId
            })
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
                            document.getElementById('ai-response').textContent = fullResponse;
                            messageList.scrollTop = messageList.scrollHeight;
                        } else if (chunk.type === 'complete') {
                            fullResponse = chunk.full_response;
                            thinkingContent = chunk.thinking || '';
                            document.getElementById('ai-response').textContent = fullResponse;
                            
                            if (thinkingContent) {
                                const thinkingDiv = document.createElement('div');
                                thinkingDiv.style.cssText = 'font-size: 12px; color: #999; margin-top: 8px;';
                                thinkingDiv.innerHTML = `<strong>💭 思考过程:</strong> ${thinkingContent}`;
                                messageDiv.querySelector('div:last-child').appendChild(thinkingDiv);
                            }
                            
                            // 更新会话状态
                            if (chunk.session_id) {
                                currentSessionId = chunk.session_id;
                            }
                            
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
        document.getElementById('ai-response').textContent = '❌ 发生错误: ' + error.message;
    }

    sendBtn.disabled = false;
    msgInput.focus();
}

// ============================================================
// 会话列表相关
// ============================================================
async function loadSessions() {
    const sessions = await fetchSessions();
    renderSessionList(sessions);
}

function renderSessionList(sessions) {
    recordList.innerHTML = '';
    recordCount.textContent = sessions.length;
    
    if (sessions.length === 0) {
        recordList.innerHTML = '<div style="text-align:center;color:#bbb;font-size:13px;padding:40px 0;">暂无会话<br><span style="font-size:12px;">开始你的第一次对话吧</span></div>';
        return;
    }
    
    for (const session of sessions) {
        const item = document.createElement('div');
        item.className = 'record-item';
        if (session.id === currentSessionId) {
            item.classList.add('active');
        }
        
        const nameSpan = document.createElement('span');
        nameSpan.className = 'preview';
        nameSpan.textContent = session.session_name || session.id.slice(0, 8);
        nameSpan.title = `创建: ${new Date(session.created_at).toLocaleString()}`;
        
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = '×';
        deleteBtn.style.cssText = 'background:none;border:none;color:#999;cursor:pointer;font-size:14px;margin-left:8px;';
        deleteBtn.title = '删除会话';
        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (confirm('确定要删除这个会话吗？')) {
                await deleteSession(session.id);
                if (currentSessionId === session.id) {
                    currentSessionId = null;
                    messageList.innerHTML = '';
                    updateSessionUI(null);
                }
                loadSessions();
            }
        });
        
        const itemContent = document.createElement('div');
        itemContent.style.cssText = 'display:flex;justify-content:space-between;align-items:center;';
        itemContent.appendChild(nameSpan);
        itemContent.appendChild(deleteBtn);
        
        item.appendChild(itemContent);
        
        item.addEventListener('click', async () => {
            const data = await getSession(session.id);
            if (data) {
                currentSessionId// ============================================================
// 配置
// ============================================================
const API_BASE = 'http://127.0.0.1:8000';

// ============================================================
// DOM 引用
// ============================================================
const messageList = document.getElementById('messageList');
const msgInput = document.getElementById('msgInput');
const sendBtn = document.getElementById('sendBtn');
const newGameBtn = document.getElementById('newGameBtn');
const sessionDisplay = document.getElementById('sessionDisplay');
const statusBadge = document.getElementById('statusBadge');
const recordList = document.getElementById('recordList');
const recordCount = document.getElementById('recordCount');

// 规则相关DOM
const rulesInput = document.getElementById('rulesInput');
const updateRulesBtn = document.getElementById('updateRulesBtn');
const rulesDisplay = document.getElementById('rulesDisplay');
const rulesText = document.getElementById('rulesText');

// 设置相关DOM
const aiName = document.getElementById('aiName');
const aiPersonality = document.getElementById('aiPersonality');

// 默认规则
const defaultRules = `1、每次只回1条消息
2、禁止任何场景或状态描述性文字
3、匹配用户的语言
4、回复简短，像微信聊天一样
5、有需要的话可以用🩷 💞等emoji表情
6、用符合伴侣性格的方式对话
7、回复的内容，要充分体现伴侣的性格特征`;

// 状态管理
let currentSessionId = null;
let messageHistory = [];
let sessionRecords = [];

// ============================================================
// 工具函数
// ============================================================
function getTime() {
    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `${pad(now.getHours())}:${pad(now.getMinutes())}`;
}

function getFullTime() {
    const now = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
}

function addMessage(role, content, extra = '') {
    const isUser = role === 'user';
    const avatar = isUser ? '👤' : '🤖';
    const time = getTime();
    const timeFull = getFullTime();

    const div = document.createElement('div');
    div.className = `message ${role}`;

    div.innerHTML = `
        <div class="avatar">${avatar}</div>
        <div>
            <div class="bubble">${content}</div>
            <span class="time-tag">${timeFull}</span>
            ${extra ? `<span class="time-tag" style="color:#667eea;">${extra}</span>` : ''}
        </div>
    `;

    messageList.appendChild(div);
    messageList.scrollTop = messageList.scrollHeight;

    messageHistory.push({ role, content, time: timeFull });
}

function setStatus(text, type = 'online') {
    const colors = {
        online: '#00b894',
        offline: '#ff6b6b',
        loading: '#fdcb6e'
    };
    statusBadge.textContent = `● ${text}`;
    statusBadge.style.color = colors[type] || '#00b894';
}

function updateSessionUI(sessionId) {
    currentSessionId = sessionId;
    if (sessionId) {
        sessionDisplay.textContent = `会话: ${sessionId.slice(0, 12)}...`;
        setStatus('在线', 'online');
        msgInput.disabled = false;
        sendBtn.disabled = false;
        msgInput.focus();
    } else {
        sessionDisplay.textContent = '会话: 未创建';
        setStatus('离线', 'offline');
        msgInput.disabled = true;
        sendBtn.disabled = true;
    }
}

// ============================================================
// 通知函数
// ============================================================
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = 'notification';
    
    const colors = {
        success: '#52c41a',
        error: '#ff4d4f',
        info: '#1890ff'
    };
    
    notification.style.background = colors[type] || colors.success;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// ============================================================
// 规则相关函数
// ============================================================
function displayRules(rules) {
    if (rules) {
        rulesDisplay.style.display = 'block';
        rulesText.textContent = rules;
    } else {
        rulesDisplay.style.display = 'none';
        rulesText.textContent = '';
    }
}

async function updateRules() {
    if (!currentSessionId) {
        showNotification('请先创建或选择一个会话', 'error');
        return;
    }
    
    const newRules = rulesInput.value.trim();
    
    try {
        const response = await fetch(`${API_BASE}/api/sessions/${currentSessionId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                extra_rules: newRules
            })
        });
        
        if (response.ok) {
            showNotification('✅ 行为规则已更新！', 'success');
            displayRules(newRules);
        } else {
            showNotification('❌ 更新失败，请重试', 'error');
        }
    } catch (error) {
        console.error('更新规则失败:', error);
        showNotification('❌ 网络错误：' + error.message, 'error');
    }
}

// ============================================================
// API 调用
// ============================================================

// 创建会话
async function createSession() {
    setStatus('连接中…', 'loading');
    
    try {
        const response = await fetch(`${API_BASE}/api/sessions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nick_name: aiName.value || '小甜甜',
                nature: aiPersonality.value || '活泼开朗的台湾姑娘',
                extra_rules: rulesInput.value || defaultRules
            })
        });
        
        const data = await response.json();
        
        if (data.session_id) {
            updateSessionUI(data.session_id);
            addMessage('assistant', '✅ 新会话已创建！<br>开始你的对话吧 🚀');
            
            // 设置规则
            rulesInput.value = defaultRules;
            displayRules(defaultRules);
            
            return data.session_id;
        } else {
            addMessage('assistant', `❌ 创建会话失败`);
            updateSessionUI(null);
            return null;
        }
    } catch (error) {
        console.error('创建会话失败:', error);
        addMessage('assistant', `❌ 网络错误: ${error.message}`);
        updateSessionUI(null);
        return null;
    }
}

// 获取所有会话
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

// 获取单个会话
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

// 删除会话
async function deleteSession(sessionId) {
    try {
        const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete session');
        return await response.json();
    } catch (error) {
        console.error('Error deleting session:', error);
        return null;
    }
}

// 发送消息（流式）
async function sendMessageStream(content) {
    if (!currentSessionId) {
        addMessage('assistant', '⚠️ 请先点击「新建会话」创建会话');
        return;
    }

    // 添加用户消息
    addMessage('user', content);
    msgInput.value = '';
    msgInput.style.height = 'auto';
    sendBtn.disabled = true;

    // 创建助手消息占位
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.innerHTML = `
        <div class="avatar">🤖</div>
        <div>
            <div class="bubble" id="ai-response">思考中...</div>
            <span class="time-tag"></span>
        </div>
    `;
    messageList.appendChild(messageDiv);
    messageList.scrollTop = messageList.scrollHeight;

    let fullResponse = '';
    let thinkingContent = '';

    try {
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: content,
                session_id: currentSessionId
            })
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
                            document.getElementById('ai-response').textContent = fullResponse;
                            messageList.scrollTop = messageList.scrollHeight;
                        } else if (chunk.type === 'complete') {
                            fullResponse = chunk.full_response;
                            thinkingContent = chunk.thinking || '';
                            document.getElementById('ai-response').textContent = fullResponse;
                            
                            if (thinkingContent) {
                                const thinkingDiv = document.createElement('div');
                                thinkingDiv.style.cssText = 'font-size: 12px; color: #999; margin-top: 8px;';
                                thinkingDiv.innerHTML = `<strong>💭 思考过程:</strong> ${thinkingContent}`;
                                messageDiv.querySelector('div:last-child').appendChild(thinkingDiv);
                            }
                            
                            // 更新会话状态
                            if (chunk.session_id) {
                                currentSessionId = chunk.session_id;
                            }
                            
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
        document.getElementById('ai-response').textContent = '❌ 发生错误: ' + error.message;
    }

    sendBtn.disabled = false;
    msgInput.focus();
}

// ============================================================
// 会话列表相关
// ============================================================
async function loadSessions() {
    const sessions = await fetchSessions();
    renderSessionList(sessions);
}

function renderSessionList(sessions) {
    recordList.innerHTML = '';
    recordCount.textContent = sessions.length;
    
    if (sessions.length === 0) {
        recordList.innerHTML = '<div style="text-align:center;color:#bbb;font-size:13px;padding:40px 0;">暂无会话<br><span style="font-size:12px;">开始你的第一次对话吧</span></div>';
        return;
    }
    
    for (const session of sessions) {
        const item = document.createElement('div');
        item.className = 'record-item';
        if (session.id === currentSessionId) {
            item.classList.add('active');
        }
        
        const nameSpan = document.createElement('span');
        nameSpan.className = 'preview';
        nameSpan.textContent = session.session_name || session.id.slice(0, 8);
        nameSpan.title = `创建: ${new Date(session.created_at).toLocaleString()}`;
        
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = '×';
        deleteBtn.style.cssText = 'background:none;border:none;color:#999;cursor:pointer;font-size:14px;margin-left:8px;';
        deleteBtn.title = '删除会话';
        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (confirm('确定要删除这个会话吗？')) {
                await deleteSession(session.id);
                if (currentSessionId === session.id) {
                    currentSessionId = null;
                    messageList.innerHTML = '';
                    updateSessionUI(null);
                }
                loadSessions();
            }
        });
        
        const itemContent = document.createElement('div');
        itemContent.style.cssText = 'display:flex;justify-content:space-between;align-items:center;';
        itemContent.appendChild(nameSpan);
        itemContent.appendChild(deleteBtn);
        
        item.appendChild(itemContent);
        
        item.addEventListener('click', async () => {
            const data = await getSession(session.id);
            if (data) {
                currentSessionId = session.id;
                messageList.innerHTML = '';
                
                // 加载历史消息
                if (data.messages && data.messages.length > 0) {
                    for (const msg of data.messages) {
                        addMessage(msg.role, msg.content);
                    }
                } else {
                    addMessage('assistant', '这个会话还没有消息，开始对话吧！');
                }
                
                // 加载设置
                aiName.value = data.nick_name;
                aiPersonality.value = data.nature;
                
                // 加载规则
                rulesInput.value = data.extra_rules || defaultRules;
                displayRules(data.extra_rules || defaultRules);
                
                updateSessionUI(session.id);
                loadSessions();
            }
        });
        
        recordList.appendChild(item);
    }
}

// ============================================================
// 事件绑定
// ============================================================

// 新建会话
newGameBtn.addEventListener('click', async () => {
    newGameBtn.disabled = true;
    newGameBtn.textContent = '⏳ 创建中…';
    await createSession();
    newGameBtn.textContent = '🎮 新建会话';
    newGameBtn.disabled = false;
});

// 发送消息
sendBtn.addEventListener('click', () => {
    const content = msgInput.value.trim();
    if (content) {
        sendMessageStream(content);
    }
});

// 更新规则
updateRulesBtn.addEventListener('click', updateRules);

// 键盘事件
msgInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
    }
});

// 自动调整高度
msgInput.addEventListener('input', () => {
    msgInput.style.height = 'auto';
    msgInput.style.height = Math.min(msgInput.scrollHeight, 120) + 'px';
});

// ============================================================
// 初始化
// ============================================================
async function init() {
    // 设置欢迎时间
    document.getElementById('welcomeTime').textContent = getFullTime();
    
    // 设置默认规则
    rulesInput.value = defaultRules;
    displayRules(defaultRules);
    
    // 加载会话列表
    await loadSessions();
    
    // 如果有会话，加载第一个
    const sessions = await fetchSessions();
    if (sessions.length > 0) {
        const data = await getSession(sessions[0].id);
        if (data) {
            currentSessionId = sessions[0].id;
            messageList.innerHTML = '';
            
            // 加载历史消息
            if (data.messages && data.messages.length > 0) {
                for (const msg of data.messages) {
                    addMessage(msg.role, msg.content);
                }
            }
            
            // 加载设置
            aiName.value = data.nick_name;
            aiPersonality.value = data.nature;
            
            // 加载规则
            rulesInput.value = data.extra_rules || defaultRules;
            displayRules(data.extra_rules || defaultRules);
            
            updateSessionUI(currentSessionId);
        }
    } else {
        // 没有会话，自动创建
        setTimeout(() => {
            createSession();
        }, 500);
    }
}

// 启动
init();

console.log('📦 AI智能伴侣已加载');
console.log('🔗 API: ', API_BASE);