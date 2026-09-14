/**
 * Language Translator – client-side logic.
 *
 * Features:
 *  - Populates language dropdowns from the /languages endpoint
 *  - Translates text via POST /translate
 *  - Swap languages button
 *  - Browser Web Speech API for speech-to-text input (optional)
 *  - Copy-to-clipboard
 *  - Character counter
 *  - Graceful error toasts
 */

document.addEventListener("DOMContentLoaded", () => {
    // ── DOM refs ────────────────────────────────────────────────────────────
    const sourceSelect  = document.getElementById("source-lang");
    const targetSelect  = document.getElementById("target-lang");
    const sourceText    = document.getElementById("source-text");
    const resultText    = document.getElementById("result-text");
    const detectedLang  = document.getElementById("detected-lang");
    const charCount     = document.getElementById("char-count");
    const translateBtn  = document.getElementById("translate-btn");
    const swapBtn       = document.getElementById("swap-btn");
    const clearBtn      = document.getElementById("clear-btn");
    const copyBtn       = document.getElementById("copy-btn");
    const micBtn        = document.getElementById("mic-btn");
    const errorToast    = document.getElementById("error-toast");

    const MAX_CHARS = 5000;
    let languageMap = {};     // code → name
    let recognition = null;   // SpeechRecognition instance
    let isListening = false;

    // ── Initialise ─────────────────────────────────────────────────────────
    fetchLanguages();
    initSpeechRecognition();

    // ── Fetch languages ────────────────────────────────────────────────────
    async function fetchLanguages() {
        try {
            const res = await fetch("/languages");
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.error || `HTTP ${res.status}`);
            }
            const data = await res.json();
            populateDropdowns(data.common, data.others);
        } catch (err) {
            showError("Could not load languages: " + err.message);
            // Fallback: leave the hardcoded option in place
        }
    }

    function populateDropdowns(common, others) {
        // Source: keep "Auto-detect" as first option
        sourceSelect.innerHTML = '<option value="auto">Auto-detect</option>';
        // Target: start empty
        targetSelect.innerHTML = "";

        const addGroup = (select, label, items) => {
            const group = document.createElement("optgroup");
            group.label = label;
            items.forEach(lang => {
                const opt = document.createElement("option");
                opt.value = lang.code;
                opt.textContent = lang.name;
                group.appendChild(opt);
                languageMap[lang.code] = lang.name;
            });
            select.appendChild(group);
        };

        addGroup(sourceSelect, "Common", common);
        addGroup(sourceSelect, "All Languages", others);
        addGroup(targetSelect, "Common", common);
        addGroup(targetSelect, "All Languages", others);

        // Default target to Spanish
        targetSelect.value = "es";
    }

    // ── Translate ──────────────────────────────────────────────────────────
    translateBtn.addEventListener("click", doTranslate);

    // Ctrl+Enter / Cmd+Enter shortcut
    sourceText.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            doTranslate();
        }
    });

    async function doTranslate() {
        const text = sourceText.value.trim();
        if (!text) { showError("Please enter some text to translate."); return; }

        // UI: loading state
        translateBtn.disabled = true;
        translateBtn.innerHTML = '<span class="spinner"></span> Translating…';
        resultText.innerHTML = '<span class="placeholder-text">Translating…</span>';
        detectedLang.textContent = "";

        try {
            const res = await fetch("/translate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text,
                    source: sourceSelect.value,
                    target: targetSelect.value,
                }),
            });

            const data = await res.json().catch(() => ({}));

            if (!res.ok) {
                throw new Error(data.error || `HTTP ${res.status}`);
            }

            resultText.textContent = data.translatedText;
            if (data.detectedSourceLanguage && sourceSelect.value === "auto") {
                const name = languageMap[data.detectedSourceLanguage] || data.detectedSourceLanguage;
                detectedLang.textContent = `Detected language: ${name}`;
            }
        } catch (err) {
            resultText.innerHTML = '<span class="placeholder-text">Translation failed.</span>';
            showError(err.message);
        } finally {
            translateBtn.disabled = false;
            translateBtn.innerHTML = '<span class="material-icons-round">translate</span> Translate';
        }
    }

    // ── Swap languages ─────────────────────────────────────────────────────
    swapBtn.addEventListener("click", () => {
        const srcVal = sourceSelect.value;
        const tgtVal = targetSelect.value;

        if (srcVal === "auto") {
            showError("Cannot swap when source is set to Auto-detect.");
            return;
        }

        sourceSelect.value = tgtVal;
        targetSelect.value = srcVal;

        // Also swap text content if there's a translation
        const currentResult = resultText.textContent;
        if (currentResult && !resultText.querySelector(".placeholder-text")) {
            sourceText.value = currentResult;
            resultText.innerHTML = '<span class="placeholder-text">Translation will appear here…</span>';
            updateCharCount();
        }
    });

    // ── Clear ──────────────────────────────────────────────────────────────
    clearBtn.addEventListener("click", () => {
        sourceText.value = "";
        resultText.innerHTML = '<span class="placeholder-text">Translation will appear here…</span>';
        detectedLang.textContent = "";
        updateCharCount();
        sourceText.focus();
    });

    // ── Copy translation ───────────────────────────────────────────────────
    copyBtn.addEventListener("click", async () => {
        const text = resultText.textContent;
        if (!text || resultText.querySelector(".placeholder-text")) return;

        try {
            await navigator.clipboard.writeText(text);
            // Brief visual feedback
            const icon = copyBtn.querySelector(".material-icons-round");
            icon.textContent = "check";
            setTimeout(() => { icon.textContent = "content_copy"; }, 1500);
        } catch {
            showError("Could not copy to clipboard.");
        }
    });

    // ── Character counter ──────────────────────────────────────────────────
    sourceText.addEventListener("input", updateCharCount);

    function updateCharCount() {
        const len = sourceText.value.length;
        charCount.textContent = len.toLocaleString();
        charCount.style.color = len > MAX_CHARS ? "var(--error)" : "";
    }

    // ── Speech-to-Text (Web Speech API) ────────────────────────────────────
    function initSpeechRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) return; // not supported – button stays hidden

        micBtn.style.display = "flex";
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = (event) => {
            let transcript = "";
            for (let i = 0; i < event.results.length; i++) {
                transcript += event.results[i][0].transcript;
            }
            sourceText.value = transcript;
            updateCharCount();
        };

        recognition.onerror = (event) => {
            if (event.error === "no-speech") return;       // benign
            if (event.error === "aborted") return;         // user cancelled
            showError("Speech recognition error: " + event.error);
            stopListening();
        };

        recognition.onend = () => {
            if (isListening) {
                // Restart if user hasn't explicitly stopped
                try { recognition.start(); } catch { /* already started */ }
            }
        };

        micBtn.addEventListener("click", toggleListening);
    }

    function toggleListening() {
        if (isListening) {
            stopListening();
        } else {
            startListening();
        }
    }

    function startListening() {
        // Set recognition language to match the source language selector
        const lang = sourceSelect.value === "auto" ? "en-US" : sourceSelect.value;
        recognition.lang = lang;
        try {
            recognition.start();
            isListening = true;
            micBtn.classList.add("mic-active");
            micBtn.title = "Listening… click to stop";
        } catch {
            showError("Could not start speech recognition.");
        }
    }

    function stopListening() {
        recognition.stop();
        isListening = false;
        micBtn.classList.remove("mic-active");
        micBtn.title = "Speech-to-text (click to speak)";
    }

    // ── Error toast ────────────────────────────────────────────────────────
    let toastTimer = null;

    function showError(message) {
        errorToast.textContent = message;
        errorToast.classList.remove("hidden");
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => {
            errorToast.classList.add("hidden");
        }, 5000);
    }
});
