(function () {
    const packs = window.I18N_PACKS || {};
    let currentLang = window.CURRENT_LANG || "bn";

    function getNested(pack, key) {
        if (!pack) return null;
        return pack[key] || null;
    }

    function translate(key, lang) {
        lang = lang || currentLang;
        let text = getNested(packs[lang], key);
        if (!text && lang !== "en") {
            text = getNested(packs.en, key);
        }
        return text || key;
    }

    function applyLanguage(lang) {
        currentLang = lang;
        document.documentElement.lang = lang === "bn" ? "bn" : "en";
        document.body.classList.toggle("lang-bn", lang === "bn");
        document.body.classList.toggle("lang-en", lang === "en");

        document.querySelectorAll("[data-i18n]").forEach(function (el) {
            const key = el.getAttribute("data-i18n");
            const text = translate(key, lang);
            if (el.tagName === "INPUT" || el.tagName === "TEXTAREA") {
                if (el.hasAttribute("data-i18n-placeholder")) {
                    el.placeholder = text;
                }
            } else {
                el.textContent = text;
            }
        });

        document.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
            const key = el.getAttribute("data-i18n-placeholder");
            el.placeholder = translate(key, lang);
        });

        document.querySelectorAll("[data-i18n-title]").forEach(function (el) {
            const key = el.getAttribute("data-i18n-title");
            el.title = translate(key, lang);
        });

        document.querySelectorAll(".lang-switch-btn").forEach(function (btn) {
            const btnLang = btn.getAttribute("data-lang");
            btn.classList.toggle("active", btnLang === lang);
        });

        window.CURRENT_LANG = lang;
        window.t = translate;
    }

    function persistLanguage(lang) {
        const csrf = document.querySelector('meta[name="csrf-token"]');
        const headers = { "Content-Type": "application/json" };
        if (csrf) {
            headers["X-CSRFToken"] = csrf.getAttribute("content");
        }
        return fetch("/language/set", {
            method: "POST",
            headers: headers,
            body: JSON.stringify({ lang: lang }),
            credentials: "same-origin",
        });
    }

    function initLanguageToggle() {
        document.querySelectorAll(".lang-switch-btn").forEach(function (btn) {
            btn.addEventListener("click", function () {
                const lang = btn.getAttribute("data-lang");
                if (!lang || lang === currentLang) return;
                applyLanguage(lang);
                persistLanguage(lang).catch(function () {});
            });
        });
    }

    window.I18n = {
        apply: applyLanguage,
        translate: translate,
        getLang: function () { return currentLang; },
    };

    document.addEventListener("DOMContentLoaded", function () {
        applyLanguage(currentLang);
        initLanguageToggle();
    });
})();
