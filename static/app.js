const chatViewport = document.getElementById('chatViewport');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sessionList = document.getElementById('sessionList');
const newChatBtn = document.getElementById('newChatBtn');
const micBtn = document.getElementById('micBtn');
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');

let currentSessionId = crypto.randomUUID().replaceAll('-', '_');
let lastUserPrompt = '';

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || 'Request failed');
  }
  return res.json();
}

function makeUtilityRow(text, audioUrl) {
  const row = document.createElement('div');
  row.className = 'utility-row';

  const copyBtn = document.createElement('button');
  copyBtn.className = 'icon-btn';
  copyBtn.textContent = 'Copy';
  copyBtn.onclick = async () => {
    await navigator.clipboard.writeText(text);
    copyBtn.textContent = '✓ Copied';
    setTimeout(() => (copyBtn.textContent = 'Copy'), 1400);
  };

  const audioBtn = document.createElement('button');
  audioBtn.className = 'icon-btn';
  audioBtn.textContent = 'Play Audio';
  audioBtn.onclick = () => {
    if (!audioUrl) return;
    const audio = new Audio(audioUrl);
    audio.play();
  };

  const regenBtn = document.createElement('button');
  regenBtn.className = 'icon-btn';
  regenBtn.textContent = 'Regenerate';
  regenBtn.onclick = () => sendMessage(lastUserPrompt, true);

  row.append(copyBtn, audioBtn, regenBtn);
  return row;
}

function appendMessage(role, text, audioUrl = null) {
  const item = document.createElement('article');
  item.className = `message ${role}`;

  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.textContent = role === 'user' ? 'You' : 'J. AI Corporate Assistant';

  const body = document.createElement('div');
  body.textContent = text;
  item.append(meta, body);

  if (role === 'assistant') item.append(makeUtilityRow(text, audioUrl));
  chatViewport.appendChild(item);
  chatViewport.scrollTop = chatViewport.scrollHeight;
}

async function loadSessions() {
  const { sessions } = await api('/api/sessions');
  sessionList.innerHTML = '';
  sessions.forEach((s) => {
    const li = document.createElement('li');
    li.textContent = s.session_id;
    if (s.session_id === currentSessionId) li.classList.add('active');
    li.onclick = () => switchSession(s.session_id);
    sessionList.appendChild(li);
  });
}

async function switchSession(sessionId) {
  currentSessionId = sessionId;
  chatViewport.innerHTML = '';
  const { messages } = await api(`/api/sessions/${sessionId}/messages`);
  for (const msg of messages) {
    appendMessage(msg.role, msg.content);
  }
  await loadSessions();
}

async function sendMessage(text, regenerate = false) {
  if (!text || !text.trim()) return;
  lastUserPrompt = text;

  if (!regenerate) appendMessage('user', text);
  const skeleton = document.createElement('div');
  skeleton.className = 'message skeleton';
  chatViewport.appendChild(skeleton);

  try {
    const result = await api('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        session_id: currentSessionId,
        message: text,
        regenerate,
      }),
    });
    skeleton.remove();
    appendMessage('assistant', result.response, result.audio_url);
    await loadSessions();
  } catch (error) {
    skeleton.remove();
    appendMessage('assistant', `Error: ${error.message}`);
  }
}

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const text = messageInput.value.slice(0, 500);
  messageInput.value = '';
  await sendMessage(text);
});

newChatBtn.onclick = async () => {
  currentSessionId = crypto.randomUUID().replaceAll('-', '_');
  chatViewport.innerHTML = '';
  await loadSessions();
};

sidebarToggle.onclick = () => sidebar.classList.toggle('collapsed');

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.lang = 'ur-PK';
  recognition.continuous = false;
  recognition.interimResults = false;

  micBtn.onclick = () => {
    micBtn.classList.add('listening');
    recognition.start();
  };
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    messageInput.value = transcript;
  };
  recognition.onend = () => micBtn.classList.remove('listening');
  recognition.onerror = () => micBtn.classList.remove('listening');
} else {
  micBtn.disabled = true;
}

loadSessions();
