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

// ── Health check ─────────────────────────────────────────

function checkBackend() {
    fetch(BACKEND + "/health")
        .then(function () { setStatus(true); })
        .catch(function () { setStatus(false); });
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

// ── Gather layer context ─────────────────────────────────

function getLayerContext(callback) {
    cs.evalScript("getLayerNames()", function (namesRaw) {
        var layers = [];
        if (namesRaw && namesRaw !== "EvalScript error.") {
            layers = namesRaw.split(",");
        }
        // Active layer name via inline ExtendScript
        cs.evalScript("app.activeDocument.activeLayer.name", function (active) {
            var activeLayer = (active && active !== "EvalScript error.") ? active : null;
            callback(layers, activeLayer);
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

    getLayerContext(function (layers, activeLayer) {
        fetch(BACKEND + "/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                layers: layers,
                active_layer: activeLayer
            })
        })
        .then(function (res) { return res.json(); })
        .then(function (data) {
            if (data.reply) {
                addMessage(data.reply, "assistant");
            }
            if (data.script) {
                return runExtendScript(data.script).then(function (result) {
                    if (result && result !== "undefined") {
                        addMessage("Result: " + result, "assistant");
                    }
                });
            }
        })
        .catch(function (err) {
            addMessage("Error: " + err.message, "error");
        });
    });
});
