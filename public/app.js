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
    const el = $(id);
    if (!el) return;
    
    // Default Tailwind colors for dots
    const colors = {
        ok: 'bg-secondary',
        err: 'bg-error',
        pending: 'bg-tertiary'
    };
    
    el.className = `w-2 h-2 rounded-full ${colors[s] || colors.pending}`;
}

function addMsg(role, text) {
    // Hide empty state if visible
    const empty = $('empty-state');
    if (empty) empty.remove();

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
        // Clear old items except placeholder
        $('membar').querySelectorAll('.mem-item').forEach(e => e.remove());
        const ph = $('memph');
        if (res.memories.length === 0) {
            ph.classList.remove('hidden');
        } else {
            ph.classList.add('hidden');
            res.memories.slice(-5).forEach(m => {
                const div = document.createElement('div');
                div.className = 'mem-item p-3 bg-white/50 border border-slate-100 rounded-2xl text-xs text-on-surface-variant font-medium flex items-center gap-2 animate-fadeIn';
                div.innerHTML = `<span class="material-symbols-outlined text-primary text-xs" style="font-size:14px">memory</span> <span>${m.content.length > 40 ? m.content.slice(0, 40) + '…' : m.content}</span>`;
                $('membar').appendChild(div);
            });
        }
        setDot('qd', 'ok');
    }
}

// ── Vapi Voice Call ─────────────────────
function initVapi() {
    try {
        if (typeof Vapi === 'undefined') {
            console.warn('[VAPI] SDK not loaded yet, retrying...');
            setTimeout(initVapi, 1000);
            return;
        }
        
        console.log('[VAPI] Initializing with key:', CFG.vapi_key.substring(0, 8) + '...');
        vapiInst = new Vapi(CFG.vapi_key);
        console.log('[VAPI] Instance created:', vapiInst ? 'OK' : 'FAILED');

        vapiInst.on('call-start', () => {
            console.log('[VAPI] Call started');
            vapiOn = true;
            $('vbtn').classList.add('btn-pulse');
            $('vbtn').querySelector('span').textContent = 'call_end';
            $('vbtn').classList.add('bg-error-container', 'text-error');
            setDot('vd', 'ok');
            toast('Voice call connected');
        });

        vapiInst.on('call-end', () => {
            console.log('[VAPI] Call ended');
            vapiOn = false;
            $('vbtn').classList.remove('btn-pulse', 'bg-error-container', 'text-error');
            $('vbtn').querySelector('span').textContent = 'call';
            toast('Call ended');
        });

        vapiInst.on('message', (msg) => {
            console.log('[VAPI] Message:', msg);
            if (msg.type === 'transcript' && msg.transcriptType === 'final') {
                if (msg.role === 'user') addMsg('user', msg.transcript);
                if (msg.role === 'assistant') {
                    addMsg('ai', msg.transcript);
                    loadMemory();
                }
            }
        });

        vapiInst.on('error', (e) => {
            console.error('[VAPI] Error:', e);
            setDot('vd', 'dr');
            toast('Vapi error: ' + (e.message || 'Connection failed'));
        });
        
        vapiReady = true;
        setDot('vd', 'ok');
        sysMsg('✓ Voice engine ready');
        console.log('[VAPI] Ready! Click call button to start');
    } catch (e) {
        console.error('[VAPI] Init failed:', e);
        setDot('vd', 'dr');
        sysMsg('✗ Voice engine failed: ' + e.message);
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
        $('mbtn').classList.remove('bg-error-container', 'text-error', 'btn-pulse');
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
    if (!vapiInst) {
        if (typeof Vapi === 'undefined') {
            toast('Vapi SDK not loaded - check internet connection');
            console.error('[VAPI] SDK not loaded. Check if https://cdn.jsdelivr.net/npm/@vapi-ai/web@latest/dist/vapi.iife.js is accessible');
        } else {
            toast('Vapi initializing... please wait');
            console.log('[VAPI] Instance not ready yet, retrying init...');
            initVapi();
        }
        return;
    }
    if (vapiOn) {
        vapiInst.stop();
    } else {
        console.log('[VAPI] Starting call with assistant:', CFG.assistant_id);
        vapiInst.start(CFG.assistant_id);
    }
};

$('mbtn').onclick = () => {
    if (!recognition) return toast('Browser speech not supported');
    if (micOn) { recognition.stop(); }
    else {
        recognition.start();
        micOn = true;
        $('mbtn').classList.add('bg-error-container', 'text-error', 'btn-pulse');
        toast('Listening...');
    }
};

document.querySelectorAll('.tab, .mobile-tab').forEach(tab => {
    tab.onclick = () => {
        // Clear all active states
        document.querySelectorAll('.tab, .mobile-tab, .mobile-tab div').forEach(t => {
            t.classList.remove('bg-indigo-50', 'dark:bg-indigo-900/40', 'text-indigo-800', 'dark:text-indigo-100');
            t.classList.add('text-slate-500', 'dark:text-slate-400');
        });
        
        // Match both desktop and mobile tabs for the same mode
        const mode = tab.dataset.mode || tab.parentElement.dataset.mode;
        document.querySelectorAll(`[data-mode="${mode}"]`).forEach(t => {
            t.classList.add('bg-indigo-50', 'dark:bg-indigo-900/40', 'text-indigo-800', 'dark:text-indigo-100');
            t.classList.remove('text-slate-500', 'dark:text-slate-400');
        });

        currentMode = mode;
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
    
    // Check Vapi backend status
    const vapiStatus = await apiCall('/api/ngrok-status', 'GET');
    if (vapiStatus) {
        console.log('[VAPI] Backend status:', vapiStatus);
        if (!vapiStatus.vapi_available) {
            sysMsg('⚠ Vapi backend not available');
        } else if (!vapiStatus.configured) {
            sysMsg('⚠ Ngrok URL not configured');
        } else {
            sysMsg('✓ Vapi backend ready');
        }
    }
    
    initVapi();
    initFallbackMic();
    loadMemory();
    
    setTimeout(() => {
        addMsg('ai', "Namaste! I am Sahayak AI. How can I help you see the world today?");
    }, 1000);
})();
