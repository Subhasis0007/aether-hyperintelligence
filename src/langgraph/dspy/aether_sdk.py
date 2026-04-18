from __future__ import annotations

import json
import os
import pathlib
from dataclasses import dataclass
from typing import List, Any

import requests


@dataclass
class MetricItem:
    incident_text: str
    kb_articles_used: str
    recent_changes: str
    verified_priority: str
    verified_category: str
    was_auto_resolved: bool


@dataclass
class MetricsBundle:
    successful: List[MetricItem]
    failed: List[MetricItem]


class AetherMetricsStore:
    def __init__(self, supabase_url: str | None = None, supabase_key: str | None = None):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key

    def load_last_30_days(self, agent: str) -> MetricsBundle:
        # Preferred path: Supabase REST
        if self.supabase_url and self.supabase_key:
            try:
                base = self.supabase_url.rstrip("/")
                endpoint = f"{base}/rest/v1/aether_agent_metrics"
                params = {
                    "agent": f"eq.{agent}",
                    "select": "incident_text,kb_articles_used,recent_changes,verified_priority,verified_category,was_auto_resolved,success",
                    "order": "created_at.desc",
                    "limit": "200"
                }
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Accept": "application/json"
                }
                resp = requests.get(endpoint, headers=headers, params=params, timeout=30)
                resp.raise_for_status()
                rows = resp.json()
                successful = []
                failed = []
                for r in rows:
                    item = MetricItem(
                        incident_text=r.get("incident_text", ""),
                        kb_articles_used=r.get("kb_articles_used", ""),
                        recent_changes=r.get("recent_changes", ""),
                        verified_priority=str(r.get("verified_priority", "")),
                        verified_category=r.get("verified_category", ""),
                        was_auto_resolved=bool(r.get("was_auto_resolved", False)),
                    )
                    if bool(r.get("success", True)):
                        successful.append(item)
                    else:
                        failed.append(item)
                return MetricsBundle(successful=successful, failed=failed)
            except Exception as ex:
                print(f"[WARN] Supabase load failed, falling back to local sample metrics: {ex}")

        # Fallback path: local JSON sample
        sample_path = pathlib.Path(__file__).parent / "data" / "sample_metrics.json"
        payload = json.loads(sample_path.read_text(encoding="utf-8-sig"))
        successful = [MetricItem(**x) for x in payload.get("successful", [])]
        failed = [MetricItem(**x) for x in payload.get("failed", [])]
        return MetricsBundle(successful=successful, failed=failed)


class GitHubPRCreator:
    def __init__(self, github_token: str):
        self.github_token = github_token

    def create(self, title: str, body: str, auto_merge: bool = False) -> dict[str, Any]:
        repo = os.environ.get("GITHUB_REPOSITORY")
        if not repo:
            raise RuntimeError("GITHUB_REPOSITORY is not set.")
        owner, name = repo.split("/", 1)

        branch = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME") or "main"

        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        payload = {
            "title": title,
            "body": body,
            "head": branch,
            "base": os.environ.get("AETHER_PR_BASE_BRANCH", "main")
        }

        url = f"https://api.github.com/repos/{owner}/{name}/pulls"
        resp = requests.post(url, headers=headers, json=payload, timeout=30)

        # If PR already exists, do not fail the run unnecessarily.
        if resp.status_code == 422:
            print("[INFO] PR may already exist. GitHub returned 422.")
            return {"status": "exists", "response": resp.text}

        resp.raise_for_status()
        pr = resp.json()

        if auto_merge:
            print("[INFO] Auto-merge requested. Enable via branch protection / repository settings if needed.")

        return pr
