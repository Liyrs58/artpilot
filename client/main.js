/* ArtPilot – CEP panel client */

var cs = new CSInterface();
var BACKEND = "http://127.0.0.1:8000";
var messagesEl = document.getElementById("messages");
var chatForm = document.getElementById("chat-form");
var chatInput = document.getElementById("chat-input");
var statusEl = document.getElementById("status");
var layerList = document.getElementById("layer-list");
var btnRefresh = document.getElementById("btn-refresh-layers");

// ── Helpers ──────────────────────────────────────────────

function addMessage(text, role) {
    var div = document.createElement("div");
    div.className = "msg " + role;
    div.textContent = text;
    messagesEl.appendChild(div);
    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setStatus(connected) {
    statusEl.textContent = connected ? "connected" : "disconnected";
    statusEl.className = connected ? "connected" : "disconnected";
}

// ── XHR wrapper (avoids CORS/fetch issues with file:// origin) ──

function xhrRequest(method, url, data, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    xhr.timeout = 60000;
    if (data) {
        xhr.setRequestHeader("Content-Type", "application/json");
    }
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    callback(null, JSON.parse(xhr.responseText));
                } catch (e) {
                    callback(null, xhr.responseText);
                }
            } else {
                callback(new Error("HTTP " + xhr.status));
            }
        }
    };
    xhr.onerror = function () { callback(new Error("Network error")); };
    xhr.ontimeout = function () { callback(new Error("Timeout")); };
    xhr.send(data ? JSON.stringify(data) : null);
}

// ── Health check ─────────────────────────────────────────

function checkBackend() {
    xhrRequest("GET", BACKEND + "/health", null, function (err) {
        setStatus(!err);
    });
}
checkBackend();
setInterval(checkBackend, 5000);

// ── Layer preview ────────────────────────────────────────

function refreshLayers() {
    cs.evalScript("getLayerNames()", function (result) {
        layerList.innerHTML = "";
        if (!result || result === "EvalScript error.") return;
        var names = result.split(",");
        for (var i = 0; i < names.length; i++) {
            var li = document.createElement("li");
            li.textContent = names[i];
            layerList.appendChild(li);
        }
    });
}
btnRefresh.addEventListener("click", refreshLayers);
refreshLayers();

// ── Run ExtendScript returned by backend ─────────────────

function runExtendScript(code) {
    return new Promise(function (resolve, reject) {
        cs.evalScript(code, function (result) {
            if (result === "EvalScript error.") {
                reject(new Error("ExtendScript execution failed"));
            } else {
                resolve(result);
            }
        });
    });
}

// ── Gather full document context ─────────────────────────

function getDocContext(callback) {
    cs.evalScript("getLayerNames()", function (namesRaw) {
        var layers = [];
        if (namesRaw && namesRaw !== "EvalScript error.") {
            layers = namesRaw.split(",");
        }
        cs.evalScript("app.activeDocument.activeLayer.name", function (active) {
            var activeLayer = (active && active !== "EvalScript error.") ? active : null;
            // Get full document structure for LLM
            cs.evalScript("describeDocument()", function (docInfo) {
                var info = (docInfo && docInfo !== "EvalScript error.") ? docInfo : null;
                callback(layers, activeLayer, info);
            });
        });
    });
}

// ── Chat submit ──────────────────────────────────────────

chatForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = chatInput.value.trim();
    if (!text) return;

    addMessage(text, "user");
    chatInput.value = "";

    getDocContext(function (layers, activeLayer, docInfo) {
        xhrRequest("POST", BACKEND + "/chat", {
            message: text,
            layers: layers,
            active_layer: activeLayer,
            doc_info: docInfo
        }, function (err, data) {
            if (err) {
                addMessage("Error: " + err.message, "error");
                return;
            }
            if (data.reply) {
                addMessage(data.reply, "assistant");
            }
            if (data.script) {
                runExtendScript(data.script).then(function (result) {
                    if (result && result !== "undefined") {
                        addMessage("Result: " + result, "assistant");
                    }
                }).catch(function (e) {
                    addMessage("Script error: " + e.message, "error");
                });
            }
        });
    });
});
