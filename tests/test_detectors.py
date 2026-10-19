import pytest
from backend.detectors import url_features, url_rules, sms_rules, normalize_message, risk


@pytest.mark.parametrize(
    "value",
    [
        "",
        "javascript:alert(1)",
        "https://",
        "https://a..com",
        "https://example.com:99999",
        "https://a.com/ space",
        "https://a.com\\evil",
        "https://-a.com",
        "https://example.com/\x00",
    ],
)
def test_invalid_url(value):
    with pytest.raises(ValueError):
        url_features(value)


@pytest.mark.parametrize("url", ["http://192.0.2.1/a", "https://[2001:db8::1]/"])
def test_ip(url):
    _, features = url_features(url)
    assert features["ip"] == 1
    assert "ip_host" in [e["code"] for e in url_rules(features)]


def test_canonical_and_idn():
    assert url_features("HTTPS://Example.COM:443#fragment")[0] == "https://example.com/"
    assert url_features("https://bücher.example/")[1]["punycode"] == 1
    assert url_features("https://trusted.example@evil.example/login/verify")[1]["at"] == 1


def test_no_safe_verdict():
    assert risk(url_rules(url_features("https://example.com")[1]), None) == "low"
    assert risk(url_rules(url_features("http://192.0.2.1/login/verify")[1]), None) == "high"


def test_sms():
    assert normalize_message("  ＯＴＰ   NOW ") == "otp now"
    assert len(sms_rules("Urgent pay your OTP immediately")) == 3
    assert not sms_rules("See you at dinner tomorrow")
