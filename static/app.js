const el = (id) => document.getElementById(id);
const chatViewport = el('chatViewport');
let sessionId = crypto.randomUUID().replaceAll('-', '_');
let language = 'ur-PK';
let lastPrompt = '';

async function api(path, options = {}) { const r = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options }); if (!r.ok) throw new Error(await r.text()); return r.json(); }

function utilRow(msg) {
  const row = document.createElement('div'); row.className = 'utility-row';
  const mk = (txt, fn) => { const b = document.createElement('button'); b.className = 'icon-btn'; b.textContent = txt; b.onclick = fn; return b; };
  row.append(mk('Copy', async (e) => { await navigator.clipboard.writeText(msg.content); e.target.textContent = '✓'; setTimeout(() => e.target.textContent = 'Copy', 1000); }));
  row.append(mk('Play', () => msg.audio_url && new Audio(msg.audio_url).play()));
  row.append(mk('Regen', () => send(lastPrompt)));
  row.append(mk('Like', () => rate(msg.message_id, 5)));
  row.append(mk('Dislike', () => rate(msg.message_id, 1)));
  row.append(mk('Edit', async () => { const text = prompt('Edit message', msg.content); if (text) await send(text); }));
  row.append(mk('Delete', async () => { await api(`/api/sessions/${sessionId}/messages/${msg.message_id}`, { method: 'DELETE' }); await loadMessages(); }));
  return row;
}
function render(role, content, msg = {}) { const a = document.createElement('article'); a.className = `message ${role}`; a.innerHTML = `<div>${role}</div><div>${content}</div>`; if (role === 'assistant') a.append(utilRow({ content, ...msg })); chatViewport.append(a); chatViewport.scrollTop = chatViewport.scrollHeight; }

async function loadSessions(query = '') { const data = await api(`/api/sessions${query ? `?query=${encodeURIComponent(query)}` : ''}`); const ul = el('sessionList'); ul.innerHTML = ''; data.sessions.forEach(s => { const li = document.createElement('li'); li.innerHTML = `<span>${s.title}</span><div><button data-id='${s.session_id}' class='pin'>📌</button><button data-id='${s.session_id}' class='open'>↗</button></div>`; ul.append(li); }); ul.querySelectorAll('.open').forEach(b => b.onclick = async () => { sessionId = b.dataset.id; await loadMessages(); }); ul.querySelectorAll('.pin').forEach(b => b.onclick = async () => { await api(`/api/sessions/${b.dataset.id}`, { method: 'PUT', body: JSON.stringify({ pinned: true }) }); await loadSessions(); }); }
async function loadMessages() { const data = await api(`/api/sessions/${sessionId}/messages`); chatViewport.innerHTML = ''; data.messages.forEach(m => render(m.role, m.content, m)); }
async function rate(message_id, rating) { await api('/api/feedback', { method: 'POST', body: JSON.stringify({ session_id: sessionId, message_id, rating, comment: '' }) }); }

async function send(text) {
  if (!text?.trim()) return; lastPrompt = text; render('user', text); const sk = document.createElement('div'); sk.className = 'message skeleton'; chatViewport.append(sk);
  const creativity = Number(el('creativity').value);
  const result = await api('/api/chat', { method: 'POST', body: JSON.stringify({ session_id: sessionId, message: text.slice(0,500), language, creativity }) });
  sk.remove(); render('assistant', result.response, result); drawSuggestions(result.suggestions || []); await loadSessions();
}
function drawSuggestions(list){ const w = el('suggestions'); w.innerHTML=''; list.forEach(t=>{const c=document.createElement('button');c.className='chip';c.textContent=t;c.onclick=()=>send(t);w.append(c);}); }

el('chatForm').onsubmit = async (e) => { e.preventDefault(); const msg = el('messageInput').value; el('messageInput').value=''; await send(msg); };
el('newChatBtn').onclick = async () => { sessionId = crypto.randomUUID().replaceAll('-', '_'); chatViewport.innerHTML=''; await loadSessions(); };
el('searchInput').oninput = async (e) => loadSessions(e.target.value);
el('exportBtn').onclick = async () => { const data = await api(`/api/sessions/${sessionId}/messages`); const blob = new Blob([JSON.stringify(data, null, 2)], {type:'application/json'}); const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `${sessionId}.json`; a.click(); };
el('langBtn').onclick = () => { language = language === 'ur-PK' ? 'en-US' : 'ur-PK'; el('langBtn').textContent = `Lang: ${language}`; };
el('titleInput').onchange = async (e) => { await api(`/api/sessions/${sessionId}`, { method:'PUT', body: JSON.stringify({ title: e.target.value }) }); await loadSessions(); };
el('sidebarToggle').onclick = () => el('sidebar').classList.toggle('collapsed');

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SR) { const rec = new SR(); rec.lang = 'ur-PK'; rec.onstart = () => el('micBtn').classList.add('listening'); rec.onend = () => el('micBtn').classList.remove('listening'); rec.onresult = (e)=>{el('messageInput').value=e.results[0][0].transcript;}; el('micBtn').onclick=()=>rec.start(); }

loadSessions();
