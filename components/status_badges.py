import html


def badge_html(status):
    s = str(status or "")
    lower = s.lower()
    if lower in {"active","available","completed","loaded","valid","saved"}:
        cls="success"
    elif lower in {"pending","ready for loading"}:
        cls="warning"
    elif lower in {"confirmed","in progress"}:
        cls="info"
    elif lower in {"cancelled","inactive","unavailable","failed","invalid"}:
        cls="danger"
    else:
        cls="neutral"
    return f'<span class="aq-status aq-status-{cls}">{html.escape(s)}</span>'
