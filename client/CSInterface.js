/*
 * CSInterface.js – Minimal wrapper for Adobe CEP.
 *
 * In production the real CSInterface.js is loaded from the CEP runtime.
 * Replace this file with Adobe's official CSInterface.js (v11+) from:
 * https://github.com/niclasmattsson/user-content-samples/tree/master/AdobeCEP
 * or your Creative Cloud SDK install at:
 * /Library/Application Support/Adobe/CEP/extensions/com.adobe.CSXS.*/CSInterface.js
 *
 * This stub allows the panel to load outside Illustrator for UI testing.
 */

function CSInterface() {}

CSInterface.prototype.evalScript = function (script, callback) {
    // In a real CEP environment this calls into ExtendScript.
    // Stub: just return an error string so the panel knows it's outside the host.
    if (typeof callback === "function") {
        callback("EvalScript error.");
    }
};

CSInterface.prototype.addEventListener = function () {};
CSInterface.prototype.removeEventListener = function () {};
CSInterface.prototype.requestOpenExtension = function () {};
CSInterface.prototype.getSystemPath = function (pathType) { return ""; };
CSInterface.prototype.getHostEnvironment = function () {
    return { appName: "ILST", appVersion: "28.0" };
};
