"""Bangla + English UI translations loaded from static/lang/*.json"""

import json
from datetime import datetime
from pathlib import Path

from flask import g, has_request_context, request, session

DEFAULT_LANG = "bn"
SUPPORTED_LANGS = ("bn", "en")
LANG_COOKIE = "lang"
_TRANSLATIONS = {}

BN_MONTHS = (
    "জানুয়ারি",
    "ফেব্রুয়ারি",
    "মার্চ",
    "এপ্রিল",
    "মে",
    "জুন",
    "জুলাই",
    "আগস্ট",
    "সেপ্টেম্বর",
    "অক্টোবর",
    "নভেম্বর",
    "ডিসেম্বর",
)

BN_WEEKDAYS = (
    "সোমবার",
    "মঙ্গলবার",
    "বুধবার",
    "বৃহস্পতিবার",
    "শুক্রবার",
    "শনিবার",
    "রবিবার",
)


def _lang_dir():
    return Path(__file__).resolve().parent.parent / "static" / "lang"


def load_lang_pack(lang):
    lang = normalize_lang(lang)
    if lang not in _TRANSLATIONS:
        path = _lang_dir() / f"{lang}.json"
        with open(path, encoding="utf-8") as handle:
            _TRANSLATIONS[lang] = json.load(handle)
    return _TRANSLATIONS[lang]


def normalize_lang(lang):
    if not lang:
        return DEFAULT_LANG
    lang = str(lang).strip().lower()
    if lang.startswith("bn") or lang in ("bangla", "বাংলা"):
        return "bn"
    if lang.startswith("en"):
        return "en"
    return lang if lang in SUPPORTED_LANGS else DEFAULT_LANG


def get_lang():
    if has_request_context():
        if getattr(g, "lang", None):
            return g.lang
        if session.get("lang"):
            return normalize_lang(session["lang"])
        cookie_lang = request.cookies.get(LANG_COOKIE)
        if cookie_lang:
            return normalize_lang(cookie_lang)
        from flask_login import current_user

        if current_user.is_authenticated:
            pref = getattr(current_user, "preferred_language", None)
            if pref:
                return normalize_lang(pref)
    return DEFAULT_LANG


def set_lang(lang, user=None):
    lang = normalize_lang(lang)
    session["lang"] = lang
    if user is not None and hasattr(user, "preferred_language"):
        user.preferred_language = lang
    return lang


def t(key, **kwargs):
    lang = get_lang()
    pack = load_lang_pack(lang)
    text = pack.get(key)
    if text is None and lang != "en":
        text = load_lang_pack("en").get(key)
    if text is None:
        text = key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text


def translate_payment_method(method):
    key = f"payment_method.{method.lower().replace(' ', '_')}"
    translated = t(key)
    return translated if translated != key else method


def translate_payment_status(status):
    key = f"status.{status.lower().replace(' ', '_')}"
    translated = t(key)
    return translated if translated != key else status


def translate_stock_status(status):
    mapping = {
        "In Stock": "status.in_stock",
        "Low Stock": "status.low_stock",
        "Out of Stock": "status.out_of_stock",
    }
    key = mapping.get(status)
    if key:
        return t(key)
    return status


def format_date_locale(value, include_time=False):
    if value is None:
        return "—"
    if not isinstance(value, datetime):
        return str(value)

    lang = get_lang()
    if lang == "bn":
        month = BN_MONTHS[value.month - 1]
        base = f"{value.day} {month} {value.year}"
        if include_time:
            hour = value.strftime("%I").lstrip("0") or "12"
            minute = value.strftime("%M")
            ampm = "সকাল" if value.hour < 12 else "বিকেল"
            if value.hour >= 12 and value.hour < 16:
                ampm = "দুপুর"
            elif value.hour >= 16 and value.hour < 19:
                ampm = "বিকেল"
            elif value.hour >= 19:
                ampm = "রাত"
            base = f"{base}, {hour}:{minute} {ampm}"
        return base

    if include_time:
        return value.strftime("%d %b %Y %I:%M %p")
    return value.strftime("%d %b %Y")


def format_weekday_locale(value):
    if value is None:
        return ""
    lang = get_lang()
    if lang == "bn":
        return BN_WEEKDAYS[value.weekday()]
    return value.strftime("%A")


def get_all_packs():
    return {lang: load_lang_pack(lang) for lang in SUPPORTED_LANGS}
