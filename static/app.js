// ══════════════════════════════════════════
//  SAHAYAK AI — FRONTEND LOGIC
// ══════════════════════════════════════════

const CFG = {
    vapi_key: '207cc262-011c-4044-b24f-7fe19d7e6dab',
    assistant_id: 'bbf7d2d6-fd0a-4087-b925-1ad5a1f0d669'
};

const $ = id => document.getElementById(id);
let vapiInst = null, vapiOn = false, vapiReady = false;
let currentMode = 'chat';
let isSending = false;
let recognition = null, micOn = false;
const userID = 'user_' + Math.random().toString(36).substr(2, 9);

// ── UI Helpers ───────────────────────────
function toast(t) {
    const e = $('toast');
    e.textContent = t;
    e.classList.add('show');
    setTimeout(() => e.classList.remove('show'), 3000);
}

function setDot(id, s) {
    $(id).className = 'dot ' + (s === 'ok' ? 'dg' : s === 'err' ? 'dr' : 'dy');
}

function addMsg(role, text) {
    const d = document.createElement('div');
    d.className = 'm ' + (role === 'user' ? 'mu' : 'ma');
    d.textContent = text;
    $('msgs').appendChild(d);
    $('msgs').scrollTop = $('msgs').scrollHeight;
}

function sysMsg(t) {
    const d = document.createElement('div');
    d.className = 'ms';
    d.textContent = t;
    $('msgs').appendChild(d);
    $('msgs').scrollTop = $('msgs').scrollHeight;
}

function showTyping() {
    const d = document.createElement('div');
    d.className = 'typing ma';
    d.id = 'typ';
    d.innerHTML = '<div class="da"></div><div class="da"></div><div class="da"></div>';
    $('msgs').appendChild(d);
    $('msgs').scrollTop = $('msgs').scrollHeight;
}

function hideTyping() {
    const t = $('typ');
    if (t) t.remove();
}

// ── Backend API Calls ────────────────────
async function apiCall(endpoint, method = 'POST', body = null) {
    try {
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (body) options.body = JSON.stringify(body);
        const r = await fetch(endpoint, options);
        return await r.json();
    } catch (e) {
        console.error('API Error:', e);
        return null;
    }
}

async function sendMsg() {
    const text = $('txt').value.trim();
    if (!text || isSending) return;

    isSending = true;
    addMsg('user', text);
    $('txt').value = '';
    $('txt').style.height = 'auto';
    showTyping();

    const res = await apiCall('/api/chat', 'POST', {
        user_id: userID,
        message: text,
        mode: currentMode // Backend can use this to force intent
    });

    hideTyping();
    if (res && res.reply) {
        addMsg('ai', res.reply);
        speak(res.reply);
    } else {
        addMsg('ai', '⚠️ Server connection lost. Please try again.');
    }
    isSending = false;
    loadMemory();
}

async function loadMemory() {
    const res = await apiCall(`/api/memory/${userID}`, 'GET');
    if (res && res.memories) {
        $('membar').querySelectorAll('.mc').forEach(e => e.remove());
        const ph = $('memph');
        if (res.memories.length === 0) {
            ph.style.display = 'inline';
        } else {
            ph.style.display = 'none';
            res.memories.slice(-5).forEach(m => {
                const span = document.createElement('span');
                span.className = 'mc';
                span.textContent = m.content.length > 25 ? m.content.slice(0, 25) + '…' : m.content;
                $('membar').appendChild(span);
            });
        }
        setDot('qd', 'ok');
    }
}

// ── Vapi Voice Call ─────────────────────
function initVapi() {
    try {
        vapiInst = new Vapi(CFG.vapi_key);

        vapiInst.on('call-start', () => {
            vapiOn = true;
            $('vbtn').classList.add('on');
            $('vbtn').innerHTML = '🔴';
            setDot('vd', 'ok');
            toast('Voice call connected');
        });

        vapiInst.on('call-end', () => {
            vapiOn = false;
            $('vbtn').classList.remove('on');
            $('vbtn').innerHTML = '📞';
            toast('Call ended');
        });

        vapiInst.on('message', (msg) => {
            if (msg.type === 'transcript' && msg.transcriptType === 'final') {
                if (msg.role === 'user') addMsg('user', msg.transcript);
                if (msg.role === 'assistant') {
                    addMsg('ai', msg.transcript);
                    loadMemory();
                }
            }
        });

        vapiInst.on('error', (e) => {
            console.error('Vapi Error:', e);
            setDot('vd', 'dr');
            toast('Vapi connection error');
        });

        setDot('vd', 'ok');
        sysMsg('✓ Voice engine ready');
    } catch (e) {
        console.warn('Vapi failed to load:', e);
        setDot('vd', 'dr');
    }
}

// ── Browser Mic Fallback ────────────────
function initFallbackMic() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onresult = (e) => {
        const text = e.results[0][0].transcript;
        $('txt').value = text;
        sendMsg();
    };

    recognition.onend = () => {
        micOn = false;
        $('mbtn').classList.remove('on');
    };
}

function speak(text) {
    if (!window.speechSynthesis || vapiOn) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'en-IN';
    u.rate = 0.9;
    window.speechSynthesis.speak(u);
}

// ── Event Listeners ─────────────────────
$('sbtn').onclick = sendMsg;
$('txt').onkeydown = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); } };

$('vbtn').onclick = () => {
    if (!vapiInst) return toast('Vapi not initialized');
    if (vapiOn) vapiInst.stop();
    else vapiInst.start(CFG.assistant_id);
};

$('mbtn').onclick = () => {
    if (!recognition) return toast('Browser speech not supported');
    if (micOn) { recognition.stop(); }
    else {
        recognition.start();
        micOn = true;
        $('mbtn').classList.add('on');
        toast('Listening...');
    }
};

document.querySelectorAll('.tab').forEach(tab => {
    tab.onclick = () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        currentMode = tab.dataset.mode;
        toast(`Switched to ${currentMode} mode`);
        
        // Auto-trigger for specific modes
        if (currentMode === 'ocr') {
            $('txt').value = "Read the text in front of me.";
            sendMsg();
        } else if (currentMode === 'vision') {
            $('txt').value = "What is in front of me?";
            sendMsg();
        }
    };
});

// ── Boot ────────────────────────────────
(async () => {
    sysMsg('Connecting to Gemini & Qdrant...');
    const health = await apiCall('/api/health', 'GET');
    if (health) {
        setDot('gd', 'ok');
        setDot('qd', 'ok');
        sysMsg('✓ Memory & Intelligence online');
    } else {
        setDot('gd', 'dr');
        setDot('qd', 'dr');
    }
    initVapi();
    initFallbackMic();
    loadMemory();
    
    setTimeout(() => {
        addMsg('ai', "Namaste! I am Sahayak AI. How can I help you see the world today?");
    }, 1000);
})();
