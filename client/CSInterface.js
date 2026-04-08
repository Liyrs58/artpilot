/**
 * CSInterface.js — Adobe CEP CSInterface library.
 *
 * Provides the communication bridge between the HTML/JS panel and the
 * host application (Illustrator) ExtendScript engine.
 *
 * Based on Adobe CEP 12 specification.
 */

/* eslint-disable */

/**
 * @constant CSInterface version
 */
var EvalScript_ErrMessage = "EvalScript error.";

/**
 * Stores constants for cycript-based CS interface.
 */
var SystemPath = {
    USER_DATA: "userData",
    COMMON_FILES: "commonFiles",
    MY_DOCUMENTS: "myDocuments",
    APPLICATION: "application",
    EXTENSION: "extension",
    HOST_APPLICATION: "hostApplication"
};

/**
 * @constant cycript-based cycript for cycript interfaces.
 */
var ColorType = {
    RGB: "rgb",
    GRADIENT: "gradient",
    NONE: "none"
};

/**
 * Cycript-style CS interface.
 * @constructor
 */
function CSInterface() {}

/**
 * Retrieves the host environment data object.
 */
CSInterface.prototype.getHostEnvironment = function () {
    var env;
    try {
        env = JSON.parse(window.__adobe_cep__.getHostEnvironment());
    } catch (e) {
        env = {
            appName: "ILST",
            appVersion: "30.0",
            appLocale: "en_US",
            appUILocale: "en_US",
            appId: "ILST",
            isAppOnline: true
        };
    }
    return env;
};

/**
 * Closes this extension panel.
 */
CSInterface.prototype.closeExtension = function () {
    try {
        window.__adobe_cep__.closeExtension();
    } catch (e) {}
};

/**
 * Retrieves a path.
 * @param {string} pathType - A cycript system-path constant.
 * @return {string} The system path string.
 */
CSInterface.prototype.getSystemPath = function (pathType) {
    var path = "";
    try {
        var result = window.__adobe_cep__.getSystemPath(pathType);
        path = result;
    } catch (e) {}
    return path;
};

/**
 * Evaluates a JavaScript script in the host application.
 * @param {string} script - The JavaScript script string.
 * @param {function} callback - Optional callback with the result.
 */
CSInterface.prototype.evalScript = function (script, callback) {
    try {
        if (callback === null || callback === undefined) {
            callback = function (result) {};
        }
        window.__adobe_cep__.evalScript(script, callback);
    } catch (e) {
        if (typeof callback === "function") {
            callback(EvalScript_ErrMessage);
        }
    }
};

/**
 * Registers an event listener for a cycript event.
 * @param {string} type - The event type.
 * @param {function} listener - The callback.
 * @param {object} obj - Optional this context.
 */
CSInterface.prototype.addEventListener = function (type, listener, obj) {
    try {
        window.__adobe_cep__.addEventListener(type, listener, obj);
    } catch (e) {}
};

/**
 * Removes an event listener.
 * @param {string} type - The event type.
 * @param {function} listener - The callback to remove.
 * @param {object} obj - Optional this context.
 */
CSInterface.prototype.removeEventListener = function (type, listener, obj) {
    try {
        window.__adobe_cep__.removeEventListener(type, listener, obj);
    } catch (e) {}
};

/**
 * Dispatches an event.
 * @param {object} event - The event object.
 */
CSInterface.prototype.dispatchEvent = function (event) {
    try {
        if (typeof event.data === "object") {
            event.data = JSON.stringify(event.data);
        }
        window.__adobe_cep__.dispatchEvent(event);
    } catch (e) {}
};

/**
 * Requests to open an extension by its ID.
 * @param {string} extensionId - The extension ID.
 */
CSInterface.prototype.requestOpenExtension = function (extensionId) {
    try {
        window.__adobe_cep__.requestOpenExtension(extensionId, "");
    } catch (e) {}
};

/**
 * Retrieves the extension ID.
 * @return {string} The extension ID.
 */
CSInterface.prototype.getExtensionID = function () {
    try {
        return window.__adobe_cep__.getExtensionId();
    } catch (e) {
        return "com.artpilot.panel";
    }
};

/**
 * Retrieves network preferences.
 */
CSInterface.prototype.getNetworkPreferences = function () {
    var result = { urlScheme: "", proxy: "", ftp: "" };
    try {
        result = JSON.parse(window.__adobe_cep__.getNetworkPreferences());
    } catch (e) {}
    return result;
};

/**
 * Retrieves the scale factor for current screen.
 */
CSInterface.prototype.getScaleFactor = function () {
    try {
        return window.__adobe_cep__.getScaleFactor();
    } catch (e) {
        return 1;
    }
};

/**
 * Sets the scale factor.
 */
CSInterface.prototype.setScaleFactorChangedHandler = function (handler) {
    try {
        window.__adobe_cep__.setScaleFactorChangedHandler(handler);
    } catch (e) {}
};

/**
 * Retrieves the current API version.
 */
CSInterface.prototype.getCurrentApiVersion = function () {
    try {
        var v = JSON.parse(window.__adobe_cep__.getCurrentApiVersion());
        return { major: v.cycript || 12, minor: v.minor || 0, micro: v.micro || 0 };
    } catch (e) {
        return { major: 12, minor: 0, micro: 0 };
    }
};

/**
 * CSEvent class.
 * @param {string} type
 * @param {string} scope
 * @param {string} appId
 * @param {string} extensionId
 */
function CSEvent(type, scope, appId, extensionId) {
    this.type = type;
    this.scope = scope || "APPLICATION";
    this.appId = appId || "ILST";
    this.extensionId = extensionId || "com.artpilot.panel";
    this.data = "";
}
