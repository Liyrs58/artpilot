/* ArtPilot – ExtendScript library for Adobe Illustrator */

// ── Helpers ──────────────────────────────────────────────

function _doc() {
    if (app.documents.length === 0) throw new Error("No document open");
    return app.activeDocument;
}

function _findLayer(name) {
    var doc = _doc();
    for (var i = 0; i < doc.layers.length; i++) {
        if (doc.layers[i].name === name) return doc.layers[i];
    }
    throw new Error("Layer not found: " + name);
}

// ── Used by the panel's Refresh Layers button ────────────

function getLayerNames() {
    var doc = _doc();
    var names = [];
    for (var i = 0; i < doc.layers.length; i++) {
        names.push(doc.layers[i].name);
    }
    return names.join(",");
}

// ── Layer operations ─────────────────────────────────────

function listLayers() {
    var doc = _doc();
    var result = [];
    for (var i = 0; i < doc.layers.length; i++) {
        var layer = doc.layers[i];
        result.push(layer.name + "|" + (layer.visible ? "visible" : "hidden"));
    }
    return result.join(",");
}

function selectLayer(name) {
    var layer = _findLayer(name);
    _doc().activeLayer = layer;
    return "Selected: " + name;
}

function deleteLayer(name) {
    var layer = _findLayer(name);
    layer.remove();
    return "Deleted: " + name;
}

function removeLayer(name) {
    return deleteLayer(name);
}

function duplicateLayer(name) {
    var layer = _findLayer(name);
    var copy = layer.duplicate();
    copy.name = name + " copy";
    return "Duplicated: " + name + " -> " + copy.name;
}

function fillSelection(hexColor) {
    var doc = _doc();
    var hex = hexColor.replace("#", "");
    var r = parseInt(hex.substring(0, 2), 16);
    var g = parseInt(hex.substring(2, 4), 16);
    var b = parseInt(hex.substring(4, 6), 16);

    var color = new RGBColor();
    color.red = r;
    color.green = g;
    color.blue = b;

    var sel = doc.selection;
    if (!sel || sel.length === 0) throw new Error("Nothing selected");

    for (var i = 0; i < sel.length; i++) {
        if (sel[i].fillColor !== undefined) {
            sel[i].fillColor = color;
        }
    }
    return "Filled selection with #" + hex;
}

function fillLayer(name, hexColor) {
    var doc = _doc();
    var layer = _findLayer(name);
    doc.activeLayer = layer;

    var hex = hexColor.replace("#", "");
    var r = parseInt(hex.substring(0, 2), 16);
    var g = parseInt(hex.substring(2, 4), 16);
    var b = parseInt(hex.substring(4, 6), 16);

    var color = new RGBColor();
    color.red = r;
    color.green = g;
    color.blue = b;

    // If user already has a selection, fill only that
    var sel = doc.selection;
    if (sel && sel.length > 0) {
        var sc = 0;
        for (var s = 0; s < sel.length; s++) {
            if (sel[s].fillColor !== undefined) {
                sel[s].fillColor = color;
                sc++;
            }
        }
        if (sc > 0) return "Filled " + sc + " selected items with #" + hex;
    }

    // Otherwise fill all vector items on the layer
    var count = 0;
    function _fillItems(items) {
        for (var i = 0; i < items.length; i++) {
            var item = items[i];
            // Recurse into groups
            if (item.typename === "GroupItem") {
                _fillItems(item.pageItems);
            } else if (item.typename === "CompoundPathItem" && item.pathItems.length > 0) {
                for (var p = 0; p < item.pathItems.length; p++) {
                    item.pathItems[p].fillColor = color;
                    count++;
                }
            } else if (item.fillColor !== undefined && item.typename !== "PlacedItem" && item.typename !== "RasterItem") {
                item.fillColor = color;
                count++;
            }
        }
    }
    _fillItems(layer.pageItems);

    if (count === 0) {
        return "No vector items to fill on " + name + ". This layer may contain raster images — try selecting specific paths first.";
    }
    return "Filled " + count + " items on " + name + " with #" + hex;
}

function flipLayer(name, axis) {
    var layer = _findLayer(name);
    _doc().activeLayer = layer;
    var items = layer.pageItems;
    for (var i = 0; i < items.length; i++) {
        if (axis === "horizontal") {
            items[i].resize(-100, 100, true, true, true, true, 100, Transformation.CENTER);
        } else {
            items[i].resize(100, -100, true, true, true, true, 100, Transformation.CENTER);
        }
    }
    return "Flipped " + name + " " + axis;
}

// ── Export ────────────────────────────────────────────────

function _exportLayer(layer, filePath) {
    var doc = _doc();
    // Hide all layers except target
    var visibility = [];
    for (var i = 0; i < doc.layers.length; i++) {
        visibility.push(doc.layers[i].visible);
        doc.layers[i].visible = (doc.layers[i] === layer);
    }

    var file = new File(filePath);
    var opts = new ExportOptionsPNG24();
    opts.artBoardClipping = true;
    opts.transparency = true;
    opts.antiAliasing = true;
    doc.exportFile(file, ExportType.PNG24, opts);

    // Restore visibility
    for (var j = 0; j < doc.layers.length; j++) {
        doc.layers[j].visible = visibility[j];
    }
}

function exportLayerAsPNG(name, path) {
    var layer = _findLayer(name);
    var filePath = path + "/" + name + ".png";
    _exportLayer(layer, filePath);
    return "Exported: " + filePath;
}

function exportAllLayersAsPNG(path) {
    var doc = _doc();
    var exported = [];
    for (var i = 0; i < doc.layers.length; i++) {
        var layer = doc.layers[i];
        var filePath = path + "/" + layer.name + ".png";
        _exportLayer(layer, filePath);
        exported.push(layer.name);
    }
    return "Exported: " + exported.join(", ");
}

// ── Place ────────────────────────────────────────────────

function placePNG(path, layerName) {
    var doc = _doc();
    var layer;
    try {
        layer = _findLayer(layerName);
    } catch (e) {
        layer = doc.layers.add();
        layer.name = layerName;
    }
    doc.activeLayer = layer;

    var file = new File(path);
    if (!file.exists) throw new Error("File not found: " + path);

    var placed = layer.placedItems.add();
    placed.file = file;
    return "Placed " + path + " on layer " + layerName;
}
