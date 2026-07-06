from flask import Blueprint, jsonify, make_response, request, session

from extensions import db
from flask_login import current_user
from utils.i18n import LANG_COOKIE, SUPPORTED_LANGS, get_all_packs, normalize_lang, set_lang

language_bp = Blueprint("language", __name__, url_prefix="/language")


@language_bp.route("/packs")
def language_packs():
    return jsonify(get_all_packs())


@language_bp.route("/set", methods=["POST"])
def language_set():
    lang = normalize_lang(
        request.json.get("lang") if request.is_json else request.form.get("lang")
    )
    if lang not in SUPPORTED_LANGS:
        return jsonify({"ok": False, "error": "unsupported"}), 400

    session["lang"] = lang
    user = None
    if current_user.is_authenticated and hasattr(current_user, "preferred_language"):
        current_user.preferred_language = lang
        user = current_user
        db.session.commit()

    response = make_response(jsonify({"ok": True, "lang": lang}))
    response.set_cookie(LANG_COOKIE, lang, max_age=60 * 60 * 24 * 365, samesite="Lax")
    return response
