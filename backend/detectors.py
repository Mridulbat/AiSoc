import ipaddress
import math
import re
import unicodedata
from urllib.parse import urlsplit, urlunsplit, unquote

TOKENS = ("login", "verify", "password", "secure", "wallet", "account", "update")


def normalize_message(text):
    return " ".join(unicodedata.normalize("NFKC", text).lower().split())


def url_features(text):
    text = text.strip()
    if not text or len(text) > 4096 or re.search(r"[\s\x00-\x1f\x7f\\]", text):
        raise ValueError("Enter an HTTP or HTTPS URL without spaces or control characters.")
    if "://" not in text:
        text = "https://" + text
    try:
        u = urlsplit(text)
        if u.scheme.lower() not in ("http", "https") or not u.hostname:
            raise ValueError()
        port = u.port
        host = u.hostname.rstrip(".").encode("idna").decode("ascii").lower()
        try:
            ipaddress.ip_address(host)
            is_ip = True
        except ValueError:
            is_ip = False
            if (
                len(host) > 253
                or "." not in host
                or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", p) for p in host.split("."))
            ):
                raise ValueError()
        netloc = "[" + host + "]" if ":" in host else host
        if port and port != (443 if u.scheme == "https" else 80):
            netloc += ":" + str(port)
        if u.username is not None:
            netloc = u.netloc.rsplit("@", 1)[0] + "@" + netloc
        canonical = urlunsplit((u.scheme.lower(), netloc, u.path or "/", u.query, ""))
    except (ValueError, UnicodeError):
        raise ValueError("Invalid URL hostname, scheme or port.") from None
    decoded = unquote(u.path + "?" + u.query).lower()
    entropy = -sum((host.count(c) / len(host)) * math.log2(host.count(c) / len(host)) for c in set(host))
    f = dict(
        length=len(canonical),
        host_length=len(host),
        dots=host.count("."),
        subdomains=max(0, host.count(".") - 1),
        ip=int(is_ip),
        punycode=int("xn--" in host),
        https=int(u.scheme == "https"),
        at=int(u.username is not None),
        hyphens=host.count("-"),
        encoded=text.count("%"),
        tokens=sum(t in decoded for t in TOKENS),
        digits=sum(c.isdigit() for c in host),
        path_length=len(u.path),
        query_length=len(u.query),
        entropy=entropy,
        unusual_port=int(port is not None and port not in (80, 443)),
    )
    return canonical, f


def url_rules(f):
    rules = [
        (f["ip"], "ip_host", "The address uses an IP number instead of a recognizable domain.", 2),
        (f["at"], "userinfo", "Text before @ can disguise the actual destination.", 3),
        (f["punycode"], "idn", "Internationalised domain: check carefully for lookalike letters.", 1),
        (not f["https"], "http", "The connection is not encrypted with HTTPS.", 1),
        (f["subdomains"] > 2, "subdomains", "Many hostname levels can obscure the destination.", 1),
        (
            f["tokens"] > 1,
            "credentials",
            "The path contains multiple account or credential-related terms.",
            1,
        ),
        (f["encoded"] > 3, "encoding", "Heavy percent encoding can obscure the address.", 1),
        (f["length"] > 200, "length", "The address is unusually long.", 1),
        (f["unusual_port"], "port", "The address uses an unusual web port.", 1),
    ]
    return [dict(code=c, detail=d, weight=w) for yes, c, d, w in rules if yes]


def sms_rules(text):
    text = normalize_message(text)
    patterns = [
        (
            "secrets",
            r"\b(otp|password|pin|verification code)\b",
            "The message mentions authentication secrets.",
            2,
        ),
        (
            "urgency",
            r"\b(urgent|immediately|suspended|expire|act now)\b",
            "Urgent language can pressure you into acting without checking.",
            1,
        ),
        (
            "money",
            r"\b(pay|payment|transfer|fee|prize|winner|lottery)\b",
            "Money or prize language warrants independent verification.",
            1,
        ),
        (
            "link",
            r"(https?://|www\.)",
            "The message contains a link; its destination has not been visited.",
            1,
        ),
    ]
    return [dict(code=c, detail=d, weight=w) for c, p, d, w in patterns if re.search(p, text)]


def risk(evidence, score):
    points = sum(e["weight"] for e in evidence)
    return (
        "high"
        if points >= 4 or (score is not None and score >= 0.8)
        else "review"
        if points or (score is not None and score >= 0.4)
        else "low"
    )
