#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "dnspython>=2.6.1",
#     "httpx>=0.27.0",
#     "PyYAML>=6.0.1",
# ]
# ///
"""
Inspect a domain or URL and suggest `EgressAllowedDomains` entries.

This is designed for the VPC firewall stacks in this repository, which set
`FirewallDomainRedirectionAction: TRUST_REDIRECTION_DOMAIN` on the ALLOW rule.
Because of that, DNS CNAME redirection targets are described but not added to
the recommended allowlist by default. HTTP redirects and Helm package hosts are
included because clients will query those hostnames directly.

Examples:
    uv run scripts/inspect_egress_domains.py aws.github.io
    uv run scripts/inspect_egress_domains.py https://aws.github.io/eks-charts/index.yaml
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

import dns.exception
import dns.resolver
import httpx
import yaml


MAX_REDIRECTS = 10
MAX_BODY_BYTES = 1_000_000
USER_AGENT = "nuon-egress-domain-inspector/1.0"


@dataclass
class DnsInspection:
    queried_host: str
    cname_chain: list[str] = field(default_factory=list)
    ipv4: list[str] = field(default_factory=list)
    ipv6: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class HttpHop:
    url: str
    status_code: int | None
    location: str | None = None
    content_type: str | None = None
    error: str | None = None


@dataclass
class HelmInspection:
    package_hosts: list[str] = field(default_factory=list)
    metadata_hosts: list[str] = field(default_factory=list)
    chart_count: int = 0
    version_count: int = 0
    error: str | None = None


def normalize_host(host: str | None) -> str | None:
    if not host:
        return None
    return host.rstrip(".").lower()


def ordered_unique(values: Iterable[str]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        normalized = normalize_host(value)
        if normalized:
            seen.setdefault(normalized, None)
    return list(seen.keys())


def normalize_target(target: str) -> tuple[str, str]:
    parsed = urlparse(target)
    if parsed.scheme:
        host = normalize_host(parsed.hostname)
        if not host:
            raise ValueError(f"Unable to determine hostname from target: {target}")
        return target, host

    host = normalize_host(target)
    if not host:
        raise ValueError(f"Unable to determine hostname from target: {target}")
    return f"https://{host}/", host


def resolve_record(host: str, rdtype: str) -> list[str]:
    try:
        answers = dns.resolver.resolve(host, rdtype)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
        return []
    return [normalize_host(str(answer)) or str(answer) for answer in answers]


def inspect_dns(host: str) -> DnsInspection:
    inspection = DnsInspection(queried_host=host)
    current = host
    visited = {host}

    for _ in range(10):
        targets = resolve_record(current, "CNAME")
        if not targets:
            break

        next_host = targets[0]
        inspection.cname_chain.append(next_host)

        if next_host in visited:
            inspection.errors.append(f"CNAME loop detected at {next_host}")
            break

        visited.add(next_host)
        current = next_host

    inspection.ipv4 = resolve_record(current, "A")
    inspection.ipv6 = resolve_record(current, "AAAA")
    if not inspection.ipv4 and not inspection.ipv6:
        inspection.errors.append("No A or AAAA answers returned")

    return inspection


def fetch_url_chain(url: str, timeout: float) -> tuple[list[HttpHop], bytes, str | None]:
    chain: list[HttpHop] = []
    current_url = url
    body = b""
    final_content_type: str | None = None

    with httpx.Client(
        headers={"User-Agent": USER_AGENT},
        follow_redirects=False,
        timeout=httpx.Timeout(timeout),
    ) as client:
        for _ in range(MAX_REDIRECTS + 1):
            try:
                with client.stream("GET", current_url) as response:
                    location = response.headers.get("location")
                    content_type = response.headers.get("content-type")
                    hop = HttpHop(
                        url=current_url,
                        status_code=response.status_code,
                        location=location,
                        content_type=content_type,
                    )
                    chain.append(hop)

                    if response.is_redirect and location:
                        current_url = urljoin(current_url, location)
                        continue

                    final_content_type = content_type
                    for chunk in response.iter_bytes():
                        body += chunk
                        if len(body) >= MAX_BODY_BYTES:
                            body = body[:MAX_BODY_BYTES]
                            break
                    break
            except httpx.HTTPError as exc:
                chain.append(HttpHop(url=current_url, status_code=None, error=str(exc)))
                break

    return chain, body, final_content_type


def extract_url_hosts(values: Iterable[str]) -> list[str]:
    hosts: list[str] = []
    for value in values:
        parsed = urlparse(value)
        if parsed.scheme and parsed.hostname:
            host = normalize_host(parsed.hostname)
            if host:
                hosts.append(host)
    return ordered_unique(hosts)


def inspect_helm_index(body: bytes) -> HelmInspection | None:
    text = body.decode("utf-8", errors="replace")
    if "entries:" not in text:
        return None

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return HelmInspection(error=f"Unable to parse YAML: {exc}")

    if not isinstance(data, dict) or not isinstance(data.get("entries"), dict):
        return None

    inspection = HelmInspection()
    package_hosts: list[str] = []
    metadata_hosts: list[str] = []

    entries: dict[str, Any] = data["entries"]
    inspection.chart_count = len(entries)
    for versions in entries.values():
        if not isinstance(versions, list):
            continue
        inspection.version_count += len(versions)
        for version in versions:
            if not isinstance(version, dict):
                continue
            package_hosts.extend(extract_url_hosts(version.get("urls", [])))
            metadata_hosts.extend(extract_url_hosts(version.get("sources", [])))
            metadata_hosts.extend(extract_url_hosts([version.get("home", "")]))
            metadata_hosts.extend(extract_url_hosts([version.get("icon", "")]))

    inspection.package_hosts = ordered_unique(package_hosts)
    inspection.metadata_hosts = ordered_unique(metadata_hosts)
    return inspection


def fallback_http_if_needed(url: str, timeout: float) -> tuple[str, list[HttpHop], bytes, str | None]:
    chain, body, content_type = fetch_url_chain(url, timeout)
    if chain and chain[-1].error and url.startswith("https://"):
        fallback_url = "http://" + url[len("https://") :]
        fallback_chain, fallback_body, fallback_content_type = fetch_url_chain(fallback_url, timeout)
        if fallback_chain and not fallback_chain[-1].error:
            return fallback_url, fallback_chain, fallback_body, fallback_content_type
    return url, chain, body, content_type


def describe_dns(inspection: DnsInspection) -> list[str]:
    lines = [f"Queried host: {inspection.queried_host}"]
    if inspection.cname_chain:
        lines.append("CNAME chain: " + " -> ".join([inspection.queried_host, *inspection.cname_chain]))
    else:
        lines.append("CNAME chain: none")

    if inspection.ipv4:
        lines.append("IPv4 answers: " + ", ".join(inspection.ipv4))
    if inspection.ipv6:
        lines.append("IPv6 answers: " + ", ".join(inspection.ipv6))
    for error in inspection.errors:
        lines.append(f"DNS note: {error}")
    return lines


def describe_http(chain: list[HttpHop]) -> list[str]:
    if not chain:
        return ["No HTTP response captured."]

    lines: list[str] = []
    for hop in chain:
        if hop.error:
            lines.append(f"{hop.url} -> ERROR: {hop.error}")
            continue

        line = f"{hop.url} -> {hop.status_code}"
        if hop.location:
            line += f" -> {urljoin(hop.url, hop.location)}"
        lines.append(line)

    redirect_hosts = ordered_unique(
        urlparse(urljoin(hop.url, hop.location)).hostname
        for hop in chain
        if hop.location
    )
    if redirect_hosts:
        lines.append("HTTP redirect hosts requiring explicit allow entries: " + ", ".join(redirect_hosts))
    else:
        lines.append("HTTP redirect hosts requiring explicit allow entries: none")
    return lines


def build_recommendations(
    start_host: str,
    chain: list[HttpHop],
    helm: HelmInspection | None,
) -> tuple[list[str], dict[str, str]]:
    recommendations: list[str] = []
    reasons: dict[str, str] = {}

    def add(host: str | None, reason: str) -> None:
        normalized = normalize_host(host)
        if not normalized:
            return
        if normalized not in reasons:
            recommendations.append(normalized)
            reasons[normalized] = reason

    add(start_host, "Original hostname queried by the workload")

    for hop in chain:
        if hop.location:
            redirect_host = normalize_host(urlparse(urljoin(hop.url, hop.location)).hostname)
            add(redirect_host, "HTTP redirect target host")

    if helm:
        for host in helm.package_hosts:
            add(host, "Helm chart package host from index.yaml urls")

    return recommendations, reasons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="Domain or URL to inspect")
    parser.add_argument("--timeout", type=float, default=15.0, help="Network timeout in seconds (default: 15)")
    args = parser.parse_args()

    try:
        url, start_host = normalize_target(args.target)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 1

    url, chain, body, content_type = fallback_http_if_needed(url, args.timeout)
    dns_inspection = inspect_dns(start_host)
    helm_inspection = inspect_helm_index(body)
    recommendations, reasons = build_recommendations(start_host, chain, helm_inspection)

    print("Target")
    print(f"  Input: {args.target}")
    print(f"  URL: {url}")
    print(f"  Host: {start_host}")
    print()

    print("DNS")
    for line in describe_dns(dns_inspection):
        print(f"  {line}")
    print()

    print("HTTP")
    for line in describe_http(chain):
        print(f"  {line}")
    if content_type:
        print(f"  Final content-type: {content_type}")
    print()

    print("Content Inspection")
    if helm_inspection and not helm_inspection.error:
        print("  Detected Helm repository index.yaml")
        print(f"  Charts: {helm_inspection.chart_count}")
        print(f"  Versions: {helm_inspection.version_count}")
        print(
            "  Chart package hosts: "
            + (", ".join(helm_inspection.package_hosts) if helm_inspection.package_hosts else "none")
        )
        print(
            "  Metadata/reference hosts not added automatically: "
            + (", ".join(helm_inspection.metadata_hosts) if helm_inspection.metadata_hosts else "none")
        )
    elif helm_inspection and helm_inspection.error:
        print(f"  Helm index parsing failed: {helm_inspection.error}")
    else:
        print("  No Helm index detected.")
    print()

    print("Recommended EgressAllowedDomains Entries")
    for host in recommendations:
        print(f"  - {host}: {reasons[host]}")
    print()

    print("Parameter Value")
    print("  " + ",".join(recommendations))
    print()

    print("Notes")
    print(
        "  - This repository's firewall templates use TRUST_REDIRECTION_DOMAIN, so DNS CNAME targets are described above"
    )
    print("    but are not added automatically to the allowlist recommendation.")
    print("  - HTTP redirect hosts are added because clients will resolve and request those hosts directly.")
    print("  - Helm chart package hosts from index.yaml urls are added because Helm downloads those archives directly.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
