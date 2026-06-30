PER_PAGE_DEFAULT = 10


def get_page():
    from flask import request

    try:
        page = int(request.args.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    return max(page, 1)


def get_search():
    from flask import request

    return request.args.get("q", "").strip()
