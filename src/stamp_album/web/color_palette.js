/**
 * Color palette generator (P2-L4).
 * Generates complementary, analogous, triadic, and split-complementary color schemes.
 */

(function() {
    "use strict";

    function initColorPaletteGenerator() {
        // Add palette button to wizard color section
        var colorSection = document.getElementById("section-border");
        if (!colorSection) return;

        // Check if already added
        if (document.getElementById("color-palette-btn")) return;

        var paletteBtn = document.createElement("button");
        paletteBtn.id = "color-palette-btn";
        paletteBtn.className = "collection-action-btn";
        paletteBtn.style.marginTop = "8px";
        paletteBtn.textContent = "🎨 Generate Palette";
        paletteBtn.addEventListener("click", togglePalettePanel);

        var colorOpts = colorSection.querySelector(".wizard-color-options");
        if (colorOpts) {
            colorOpts.parentNode.insertBefore(paletteBtn, colorOpts.nextSibling);
        }
    }

    function togglePalettePanel() {
        var existing = document.getElementById("color-palette-panel");
        if (existing) { existing.remove(); return; }

        var panel = document.createElement("div");
        panel.id = "color-palette-panel";
        panel.style.cssText = "margin-top:8px;padding:12px;background:var(--bg-tertiary);border-radius:8px;";

        panel.innerHTML = '<div style="font-size:11px;font-weight:600;color:var(--text-secondary);margin-bottom:8px">Color Palette Generator</div>' +
            '<div style="display:flex;gap:6px;margin-bottom:8px;align-items:center;">' +
            '<label style="font-size:11px;color:var(--text-muted)">Base:</label>' +
            '<input type="color" id="palette-base-color" value="#3366cc" style="width:32px;height:24px;border:none;border-radius:4px;cursor:pointer;">' +
            '<select id="palette-scheme" style="flex:1;padding:4px 8px;background:var(--bg-primary);border:1px solid var(--border-color);border-radius:4px;color:var(--text-primary);font-size:11px;">' +
            '<option value="complementary">Complementary</option>' +
            '<option value="analogous">Analogous</option>' +
            '<option value="triadic">Triadic</option>' +
            '<option value="split-complementary">Split Complementary</option>' +
            '<option value="tetradic">Tetradic (Rectangle)</option>' +
            '</select>' +
            '<button id="palette-generate" class="collection-action-btn" style="padding:4px 10px">Generate</button>' +
            '</div>' +
            '<div id="palette-results" style="display:flex;gap:4px;flex-wrap:wrap;"></div>' +
            '<div id="palette-preview" style="margin-top:8px;padding:8px;border-radius:4px;text-align:center;font-size:12px;color:white;text-shadow:0 1px 2px rgba(0,0,0,0.5);">Preview</div>';

        var btn = document.getElementById("color-palette-btn");
        btn.parentNode.insertBefore(panel, btn.nextSibling);

        document.getElementById("palette-generate").addEventListener("click", generatePalette);
        // Generate initial palette
        generatePalette();
    }

    function generatePalette() {
        var baseHex = document.getElementById("palette-base-color").value;
        var scheme = document.getElementById("palette-scheme").value;
        var rgb = hexToRgb(baseHex);
        var hsl = rgbToHsl(rgb.r, rgb.g, rgb.b);

        var colors = [];
        switch (scheme) {
            case "complementary":
                colors = [hsl, { h: (hsl.h + 180) % 360, s: hsl.s, l: hsl.l }];
                break;
            case "analogous":
                colors = [
                    { h: (hsl.h - 30 + 360) % 360, s: hsl.s, l: hsl.l },
                    hsl,
                    { h: (hsl.h + 30) % 360, s: hsl.s, l: hsl.l }
                ];
                break;
            case "triadic":
                colors = [
                    hsl,
                    { h: (hsl.h + 120) % 360, s: hsl.s, l: hsl.l },
                    { h: (hsl.h + 240) % 360, s: hsl.s, l: hsl.l }
                ];
                break;
            case "split-complementary":
                colors = [
                    hsl,
                    { h: (hsl.h + 150) % 360, s: hsl.s, l: hsl.l },
                    { h: (hsl.h + 210) % 360, s: hsl.s, l: hsl.l }
                ];
                break;
            case "tetradic":
                colors = [
                    hsl,
                    { h: (hsl.h + 90) % 360, s: hsl.s, l: hsl.l },
                    { h: (hsl.h + 180) % 360, s: hsl.s, l: hsl.l },
                    { h: (hsl.h + 270) % 360, s: hsl.s, l: hsl.l }
                ];
                break;
        }

        var results = document.getElementById("palette-results");
        results.innerHTML = "";
        colors.forEach(function(c) {
            var rgb = hslToRgb(c.h, c.s, c.l);
            var hex = rgbToHex(rgb.r, rgb.g, rgb.b);
            var swatch = document.createElement("div");
            swatch.style.cssText = "width:32px;height:32px;border-radius:4px;cursor:pointer;background:" + hex + ";border:2px solid var(--border-color);transition:transform 0.15s;";
            swatch.title = hex;
            swatch.addEventListener("click", function() {
                // Apply this color to the border color selection
                var colorBtns = document.querySelectorAll(".wizard-color-btn");
                colorBtns.forEach(function(b) { b.classList.remove("selected"); });
                // Set the color picker
                document.getElementById("palette-base-color").value = hex;
                // Visual feedback
                swatch.style.transform = "scale(1.1)";
                setTimeout(function() { swatch.style.transform = "scale(1)"; }, 200);
            });
            results.appendChild(swatch);
        });

        // Update preview
        var preview = document.getElementById("palette-preview");
        if (colors.length > 0) {
            var firstColor = hslToRgb(colors[0].h, colors[0].s, colors[0].l);
            preview.style.background = rgbToHex(firstColor.r, firstColor.g, firstColor.b);
            preview.textContent = colors.map(function(c) {
                var rgb = hslToRgb(c.h, c.s, c.l);
                return rgbToHex(rgb.r, rgb.g, rgb.b);
            }).join("  ");
        }
    }

    // Color conversion utilities
    function hexToRgb(hex) {
        var r = parseInt(hex.slice(1, 3), 16);
        var g = parseInt(hex.slice(3, 5), 16);
        var b = parseInt(hex.slice(5, 7), 16);
        return { r: r, g: g, b: b };
    }

    function rgbToHex(r, g, b) {
        return "#" + [r, g, b].map(function(x) { return Math.round(x).toString(16).padStart(2, "0"); }).join("");
    }

    function rgbToHsl(r, g, b) {
        r /= 255; g /= 255; b /= 255;
        var max = Math.max(r, g, b), min = Math.min(r, g, b);
        var h, s, l = (max + min) / 2;
        if (max === min) { h = s = 0; }
        else {
            var d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
            else if (max === g) h = ((b - r) / d + 2) / 6;
            else h = ((r - g) / d + 4) / 6;
        }
        return { h: h * 360, s: s * 100, l: l * 100 };
    }

    function hslToRgb(h, s, l) {
        h /= 360; s /= 100; l /= 100;
        var r, g, b;
        if (s === 0) { r = g = b = l; }
        else {
            var hue2rgb = function(p, q, t) {
                if (t < 0) t += 1;
                if (t > 1) t -= 1;
                if (t < 1/6) return p + (q - p) * 6 * t;
                if (t < 1/2) return q;
                if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                return p;
            };
            var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            var p = 2 * l - q;
            r = hue2rgb(p, q, h + 1/3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1/3);
        }
        return { r: r * 255, g: g * 255, b: b * 255 };
    }

    document.addEventListener("DOMContentLoaded", initColorPaletteGenerator);
})();
