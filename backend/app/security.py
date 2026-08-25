import re
from typing import Tuple, Optional, Set
import nh3

from app.database import settings

# -----------------------------------------------------------------------------
# Allowlist Definitions for HTML Artifacts (Checkpoints 2 & 4)
# -----------------------------------------------------------------------------

ALLOWED_TAGS: Set[str] = {
    # Document structure
    "html", "head", "body", "title", "meta", "style",
    # Semantic containers
    "div", "section", "article", "header", "footer", "main", "nav", "aside",
    # Headings & Typography
    "h1", "h2", "h3", "h4", "h5", "h6", "p", "span", "strong", "em", "b", "i", "u",
    "small", "blockquote", "pre", "code", "hr", "br", "mark",
    # Lists
    "ul", "ol", "li", "dl", "dt", "dd",
    # Tables
    "table", "thead", "tbody", "tfoot", "tr", "th", "td", "caption",
    # Links & Media
    "a", "img", "figure", "figcaption",
}

ALLOWED_ATTRIBUTES = {
    "*": {"class", "id", "style", "title", "dir", "lang", "role"},
    "a": {"href", "target", "title"},
    "img": {"src", "alt", "title", "width", "height", "loading"},
    "table": {"border", "cellpadding", "cellspacing"},
    "th": {"scope", "colspan", "rowspan"},
    "td": {"colspan", "rowspan"},
    "meta": {"charset", "name", "content"},
}

ALLOWED_URL_SCHEMES: Set[str] = {"http", "https", "mailto"}

# -----------------------------------------------------------------------------
# Prohibited patterns for strict reject mode / CSS sanitization
# -----------------------------------------------------------------------------

REJECT_TAG_PATTERNS = [
    re.compile(r"<\s*script\b[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*/\s*script\s*>", re.IGNORECASE),
    re.compile(r"<\s*iframe\b[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*object\b[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*embed\b[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*applet\b[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*form\b[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*base\b[^>]*>", re.IGNORECASE),
    re.compile(r"<\s*meta\b[^>]*\bhttp-equiv\b[^>]*>", re.IGNORECASE),
]

REJECT_ATTR_PATTERN = re.compile(
    r"""(?:\bon\w+\s*=\s*['"][^'"]*['"]|\bon\w+\s*=\s*[^>\s]+)""",
    re.IGNORECASE,
)

REJECT_SCHEME_PATTERN = re.compile(
    r"""(?:href|src|action)\s*=\s*['"]\s*(?:javascript|data|vbscript|file):""",
    re.IGNORECASE,
)

DANGEROUS_CSS_PATTERNS = [
    re.compile(r"@import\b[^;]*;", re.IGNORECASE),
    re.compile(r"expression\s*\([^)]*\)", re.IGNORECASE),
    re.compile(r"behavior\s*:[^;]+;", re.IGNORECASE),
    re.compile(r"url\s*\(\s*['\"]?(?:javascript|data|vbscript|file):[^)]*\)", re.IGNORECASE),
    re.compile(r"-moz-binding\s*:[^;]+;", re.IGNORECASE),
]


def sanitize_css(css_text: str) -> str:
    """Removes dangerous expressions, external imports, and script protocols from CSS."""
    cleaned = css_text
    for pat in DANGEROUS_CSS_PATTERNS:
        cleaned = pat.sub("", cleaned)
    return cleaned


def sanitize_and_validate_html(
    raw_html: str,
    mode: Optional[str] = None,
) -> Tuple[str, str, bool, Optional[str]]:
    """
    Main HTML artifact sanitization and validation pipeline.

    Args:
        raw_html: The generated HTML string.
        mode: "sanitize" or "reject". If None, reads settings.artifact_sanitization_mode.

    Returns:
        (cleaned_html: str, validation_status: str, original_modified: bool, validation_error: Optional[str])
        - validation_status: "valid" | "sanitized" | "rejected"
        - original_modified: True if sanitization removed unsafe elements, False otherwise
        - validation_error: Descriptive error reason if rejected
    """
    if not raw_html or not raw_html.strip():
        return "", "valid", False, None

    active_mode = (mode or getattr(settings, "artifact_sanitization_mode", "sanitize")).lower().strip()

    # --- REJECT MODE (Previous strict behavior) ---
    if active_mode == "reject":
        for pattern in REJECT_TAG_PATTERNS:
            match = pattern.search(raw_html)
            if match:
                tag = match.group(0)[:30]
                return "", "rejected", False, f"Forbidden HTML element detected: '{tag}'"

        if REJECT_ATTR_PATTERN.search(raw_html):
            return "", "rejected", False, "Forbidden inline event handler detected"

        if REJECT_SCHEME_PATTERN.search(raw_html):
            return "", "rejected", False, "Forbidden URI scheme detected"

        return raw_html.strip(), "valid", False, None

    # --- SANITIZE MODE (Default new pipeline) ---
    try:
        # Check if raw input contained prohibited tokens
        had_unsafe_constructs = bool(
            re.search(r"<\s*script\b", raw_html, re.IGNORECASE)
            or REJECT_ATTR_PATTERN.search(raw_html)
            or REJECT_SCHEME_PATTERN.search(raw_html)
            or re.search(r"<\s*iframe\b", raw_html, re.IGNORECASE)
            or re.search(r"<\s*object\b", raw_html, re.IGNORECASE)
            or re.search(r"<\s*embed\b", raw_html, re.IGNORECASE)
            or re.search(r"<\s*applet\b", raw_html, re.IGNORECASE)
            or re.search(r"<\s*form\b", raw_html, re.IGNORECASE)
            or any(pat.search(raw_html) for pat in DANGEROUS_CSS_PATTERNS)
        )

        # 1. Sanitize CSS blocks if present
        def clean_style_match(m):
            tag_open = m.group(1)
            css_body = m.group(2)
            tag_close = m.group(3)
            return f"{tag_open}{sanitize_css(css_body)}{tag_close}"

        preprocessed_html = re.sub(
            r"(<style\b[^>]*>)([\s\S]*?)(</style>)",
            clean_style_match,
            raw_html,
            flags=re.IGNORECASE,
        )

        # 2. Structural HTML sanitization using nh3 (Rust Ammonia)
        cleaned_html = nh3.clean(
            preprocessed_html,
            tags=ALLOWED_TAGS,
            clean_content_tags={"script"},
            attributes=ALLOWED_ATTRIBUTES,
            url_schemes=ALLOWED_URL_SCHEMES,
            link_rel="noopener noreferrer",
        ).strip()

        if not cleaned_html:
            return "", "rejected", False, "Artifact content became empty after sanitization"

        validation_status = "sanitized" if had_unsafe_constructs else "valid"
        original_modified = had_unsafe_constructs

        return cleaned_html, validation_status, original_modified, None

    except Exception as exc:
        return "", "rejected", False, f"HTML sanitization error: {str(exc)}"


# Backwards compatibility alias
def validate_and_sanitize_html(html_content: str) -> Tuple[bool, str, Optional[str]]:
    cleaned, status, modified, error = sanitize_and_validate_html(html_content)
    is_valid = status in ["valid", "sanitized"] and len(cleaned) > 0
    return is_valid, cleaned, error
