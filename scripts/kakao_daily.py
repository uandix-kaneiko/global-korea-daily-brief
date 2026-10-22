#!/usr/bin/env python3
"""Verified public briefing -> Ncloud SENS brand message; stdlib only."""
import argparse
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import sys
import time
from datetime import datetime
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, build_opener, HTTPRedirectHandler
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

BASE = "https://uandix-kaneiko.github.io/global-korea-daily-brief/"
REPO = "uandix-kaneiko/global-korea-daily-brief"
ROOT = Path(__file__).resolve().parents[1]
KST = ZoneInfo("Asia/Seoul")
STATE_BRANCH = "kakao-delivery-state"


class DeliveryError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def request(method, url, headers=None, data=None):
    """Never retry POST or print provider responses containing phone numbers."""
    body = json.dumps(data, ensure_ascii=False).encode() if data is not None else None
    req = Request(url, body, {"User-Agent": "KB-Daily-Brief/1.0",
                             "Content-Type": "application/json", **(headers or {})}, method=method)
    try:
        with build_opener(NoRedirect()).open(req, timeout=25) as response:
            return response.read(2_000_001)
    except HTTPError as exc:
        # Preserve only the status. Bodies/URLs may contain personal information.
        raise DeliveryError(f"HTTP {exc.code}") from None
    except (URLError, TimeoutError, OSError):
        raise DeliveryError("Network request failed; check status before resending") from None


class BriefParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_header = False
        self.in_h3 = False
        self.header = []
        self.headlines = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "header":
            self.in_header = True
        if tag == "h3":
            self.in_h3 = True
            self.parts = []

    def handle_data(self, text):
        if self.in_header:
            self.header.append(text)
        if self.in_h3:
            self.parts.append(text)

    def handle_endtag(self, tag):
        if tag == "header":
            self.in_header = False
        if tag == "h3" and self.in_h3:
            self.headlines.append(" ".join("".join(self.parts).split()))
            self.in_h3 = False


def parse_brief(raw, day):
    if len(raw) > 2_000_000:
        raise DeliveryError("Briefing response too large")
    parser = BriefParser()
    parser.feed(raw.decode("utf-8"))
    stamp = day.replace("-", ".")
    if stamp not in " ".join(parser.header) or len(parser.headlines) < 3:
        raise DeliveryError("Today's briefing is not ready")
    return parser.headlines[:3]


def verify_publication(day):
    """Both deployed main page and RSS-linked edition must be today's version."""
    cache = f"?verify={int(time.time())}"
    live = request("GET", BASE + cache)
    headlines = parse_brief(live, day)
    if live != (ROOT / "index.html").read_bytes():
        raise DeliveryError("Pages deployment has not caught up with main")
    feed = ElementTree.fromstring(request("GET", BASE + "feed.xml" + cache))
    item = feed.find("./channel/item")
    expected = BASE + f"global-tech-daily-{day}.html"
    if item is None or item.findtext("link") != expected:
        raise DeliveryError("RSS latest edition does not match today")
    parse_brief(request("GET", expected + cache), day)
    return expected, headlines, hashlib.sha256(live).hexdigest()


def message_text(day, headlines):
    lines = [f"글로벌·테크 데일리 | {day.replace('-', '.')}", ""]
    lines += [f"• {title[:75]}" for title in headlines]
    lines += ["", "오늘의 분석과 전체 뉴스는 아래에서 확인하세요."]
    return "\n".join(lines)[:400]


def recipients(raw, limit):
    try:
        items = json.loads(raw)
    except (ValueError, TypeError):
        raise DeliveryError("KAKAO_RECIPIENTS_JSON must be a JSON array") from None
    if not isinstance(items, list) or not items or len(items) > limit:
        raise DeliveryError(f"Recipient count must be 1..{limit}")
    result, seen = [], set()
    for item in items:
        if not isinstance(item, dict) or item.get("consent") is not True:
            raise DeliveryError("Every recipient needs explicit consent=true")
        country, phone = item.get("countryCode", "82"), item.get("to", "")
        if not isinstance(country, str) or not re.fullmatch(r"[1-9]\d{0,3}", country):
            raise DeliveryError("Invalid country code")
        if not isinstance(phone, str) or not re.fullmatch(r"\d{7,15}", phone):
            raise DeliveryError("Invalid recipient number")
        # Treat +82 10... and local 010... as the same recipient.
        identity = (country, phone.lstrip("0"))
        if identity in seen:
            raise DeliveryError("Duplicate recipient")
        seen.add(identity)
        result.append({"countryCode": country, "to": phone})
    return result


def payload(channel, targets, text, link):
    if not channel.startswith("@") or len(channel) < 2:
        raise DeliveryError("KAKAO_CHANNEL_ID must start with @")
    return {"plusFriendId": channel, "messageType": "TEXT", "targeting": "I",
            "isAdult": False, "messages": [
                {**person, "content": text, "useSmsFailover": False,
                 "buttons": [{"type": "WL", "name": "오늘 브리핑 보기",
                              "linkMobile": link, "linkPc": link}]}
                for person in targets]}


def signature(method, uri, timestamp, access, secret):
    value = f"{method} {uri}\n{timestamp}\n{access}".encode()
    return base64.b64encode(hmac.new(secret.encode(), value, hashlib.sha256).digest()).decode()


class Sens:
    def __init__(self):
        self.access = required("SENS_ACCESS_KEY")
        self.secret = required("SENS_SECRET_KEY")
        self.path = "/brandmessage/v2/services/" + quote(required("SENS_SERVICE_ID"), safe=":") + "/messages"

    def call(self, method, suffix="", data=None):
        uri = self.path + suffix
        stamp = str(int(time.time() * 1000))
        headers = {"x-ncp-apigw-timestamp": stamp, "x-ncp-iam-access-key": self.access,
                   "x-ncp-apigw-signature-v2": signature(method, uri, stamp, self.access, self.secret)}
        return json.loads(request(method, "https://sens.apigw.ntruss.com" + uri, headers, data))

    def results(self, request_id, expected):
        counts = {"success": 0, "fail": 0, "processing": 0}
        token = None
        for _ in range(10):
            query = {"requestId": request_id, "pageSize": "100"}
            if token:
                query["nextToken"] = token
            data = self.call("GET", "?" + urlencode(query))
            if str(data.get("statusCode")) != "202":
                raise DeliveryError("Provider result lookup was not successful")
            for item in data.get("messages", []):
                status = item.get("messageStatusName", "processing")
                counts[status if status in counts else "processing"] += 1
            if not data.get("hasMore"):
                counts["processing"] += max(0, expected - sum(counts.values()))
                return counts
            token = data.get("nextToken")
            if not token:
                break
        raise DeliveryError("Incomplete provider result pagination")


def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise DeliveryError(f"Missing setting: {name}")
    return value


class Ledger:
    """Durable date lock on a separate branch; no phone numbers stored."""
    def __init__(self, day):
        self.headers = {"Authorization": "Bearer " + required("GITHUB_TOKEN"),
                        "Accept": "application/vnd.github+json"}
        self.path = f"/contents/delivery/{day}.json"
        self.day = day

    def api(self, method, path, data=None):
        return json.loads(request(method, f"https://api.github.com/repos/{REPO}" + path,
                                  self.headers, data))

    def read(self):
        try:
            data = self.api("GET", self.path + "?ref=" + STATE_BRANCH)
            return json.loads(base64.b64decode(data["content"])), data["sha"]
        except DeliveryError as exc:
            if str(exc) == "HTTP 404":
                return None, None
            raise

    def write(self, value, sha=None):
        data = {"message": f"Kakao delivery {self.day}: {value['status']}",
                "branch": STATE_BRANCH,
                "content": base64.b64encode(json.dumps(value, ensure_ascii=False).encode()).decode()}
        if sha:
            data["sha"] = sha
        result = self.api("PUT", self.path, data)
        return result["content"]["sha"]

    def claim(self, record):
        try:
            self.api("GET", "/git/ref/heads/" + STATE_BRANCH)
        except DeliveryError as exc:
            if str(exc) != "HTTP 404":
                raise
            main = self.api("GET", "/git/ref/heads/main")
            self.api("POST", "/git/refs", {"ref": "refs/heads/" + STATE_BRANCH,
                                            "sha": main["object"]["sha"]})
        # No existing SHA: GitHub refuses if another run already claimed today.
        return self.write(record)


def reconcile(sens, ledger, record, sha):
    counts = sens.results(record["request_id"], record["recipient_count"])
    record.update(counts=counts, checked_at=datetime.now(KST).isoformat())
    record["status"] = ("processing" if counts["processing"] else
                        "delivery_failed" if counts["fail"] else "delivered")
    ledger.write(record, sha)
    print(json.dumps({"status": record["status"], "counts": counts}))
    if counts["fail"]:
        raise DeliveryError("Some deliveries failed; inspect SENS console, no automatic resend")


def run(send=False):
    now = datetime.now(KST)
    day = now.date().isoformat()
    if send and not (8 * 60 <= now.hour * 60 + now.minute < 20 * 60 + 50):
        raise DeliveryError("Sending allowed only 08:00..20:49 Asia/Seoul")
    if not send:
        link, headlines, _ = verify_publication(day)
        print("DRY RUN: no messages sent\n" + message_text(day, headlines) + "\n" + link)
        return
    sens = Sens()
    ledger = Ledger(day)
    existing, sha = ledger.read()
    if existing:
        if existing.get("request_id"):
            reconcile(sens, ledger, existing, sha)
        else:
            raise DeliveryError("Date is locked after an uncertain send; review before any resend")
        return
    max_count = int(os.environ.get("KAKAO_MAX_RECIPIENTS", "50"))
    if not 1 <= max_count <= 200:
        raise DeliveryError("KAKAO_MAX_RECIPIENTS must be 1..200")
    targets = recipients(required("KAKAO_RECIPIENTS_JSON"), max_count)
    link, headlines, digest = verify_publication(day)
    body = payload(required("KAKAO_CHANNEL_ID"), targets, message_text(day, headlines), link)
    record = {"date": day, "status": "pending", "recipient_count": len(targets),
              "brief_sha256": digest, "started_at": now.isoformat()}
    sha = ledger.claim(record)
    # Claim is persisted BEFORE the network send. Never retry an uncertain POST.
    response = sens.call("POST", data=body)
    if str(response.get("statusCode")) != "202" or not response.get("requestId"):
        raise DeliveryError("Provider did not confirm acceptance; date remains locked")
    record.update(status="accepted", request_id=response["requestId"])
    sha = ledger.write(record, sha)
    reconcile(sens, ledger, record, sha)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Actually send (otherwise preview only)")
    args = parser.parse_args()
    try:
        run(args.send)
    except (DeliveryError, ValueError, KeyError, ElementTree.ParseError, UnicodeError) as exc:
        # Never log an untrusted response or recipient object.
        reason = str(exc) if isinstance(exc, DeliveryError) else type(exc).__name__
        print("Delivery stopped: " + reason, file=sys.stderr)
        sys.exit(1)
