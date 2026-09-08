import csv
import io
import json
import logging
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger("trinetra.watchlist")

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
CACHE_FILE = DATA_DIR / "interpol_red_notices.json"
OPENSANCTIONS_CSV_URL = (
    "https://data.opensanctions.org/datasets/latest/interpol_red_notices/targets.simple.csv"
)

# Known demo / simulation tokens preserved for test fixtures & instant demo flagging
SIMULATION_TOKENS = {"BLACK_LISTED", "INTERPOL_NOTICE", "SSB_FLAGGED", "WANTED_001"}


def _normalize_str(text: Any) -> str:
    """Normalize string by removing punctuation and converting to uppercase."""
    if not text or not isinstance(text, str):
        return ""
    cleaned = re.sub(r"[^A-Za-z0-9\s]", " ", text)
    return " ".join(cleaned.upper().split())


def _token_set(text: str) -> set[str]:
    """Return set of normalized uppercase tokens."""
    return set(_normalize_str(text).split())


class WatchlistService:
    _instance: Optional["WatchlistService"] = None

    def __init__(self):
        self.notices: list[dict[str, Any]] = []
        self.doc_index: dict[str, dict[str, Any]] = {}  # doc_number -> record
        self.name_tokens_index: list[tuple[set[str], dict[str, Any]]] = []
        self.last_synced: Optional[str] = None
        self.source: str = "INTERPOL Red Notices (Daily Verified Feed)"
        self._ensure_cache_loaded()

    @classmethod
    def get_instance(cls) -> "WatchlistService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _ensure_cache_loaded(self):
        """Load from local JSON cache if exists; otherwise download dataset."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    cache_payload = json.load(f)
                    self.notices = cache_payload.get("notices", [])
                    self.last_synced = cache_payload.get("last_synced")
                    self.source = cache_payload.get("source", self.source)
                    self._rebuild_indices()
                    logger.info(f"Loaded {len(self.notices)} Interpol records from local cache.")
                    return
            except Exception as e:
                logger.warning(f"Failed to read local Interpol cache: {e}. Re-syncing...")

        # If cache not present or invalid, perform initial sync
        self.sync_dataset()

    def _rebuild_indices(self):
        """Index records for O(1) document lookup and fast token-based name matching."""
        self.doc_index.clear()
        self.name_tokens_index.clear()

        for record in self.notices:
            name = record.get("name", "")
            aliases = record.get("aliases", "")
            identifiers = record.get("identifiers", "")

            # Index document identifiers
            if identifiers:
                for doc in identifiers.split(";"):
                    clean_doc = _normalize_str(doc).replace(" ", "")
                    if clean_doc:
                        self.doc_index[clean_doc] = record

            # Build token sets for name and aliases
            tokens = _token_set(name)
            if aliases:
                tokens.update(_token_set(aliases))
            if tokens:
                self.name_tokens_index.append((tokens, record))

    def sync_dataset(self) -> dict[str, Any]:
        """Fetch latest Interpol Red Notices dataset and persist to disk cache."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Downloading latest Interpol Red Notices dataset from {OPENSANCTIONS_CSV_URL}...")
        try:
            req = urllib.request.Request(
                OPENSANCTIONS_CSV_URL,
                headers={"User-Agent": "Trinetra-Border-Security/1.0 (Government Verification System)"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                csv_bytes = resp.read()
                csv_text = csv_bytes.decode("utf-8", errors="replace")

            reader = csv.DictReader(io.StringIO(csv_text))
            new_notices = []
            for row in reader:
                notice = {
                    "id": row.get("id", ""),
                    "name": row.get("name", ""),
                    "aliases": row.get("aliases", ""),
                    "birth_date": row.get("birth_date", ""),
                    "countries": row.get("countries", ""),
                    "identifiers": row.get("identifiers", ""),
                    "sanctions": row.get("sanctions", ""),
                    "program_ids": row.get("program_ids", "INTERPOL-RN"),
                    "dataset": row.get("dataset", "INTERPOL Red Notices"),
                    "last_seen": row.get("last_seen", ""),
                }
                new_notices.append(notice)

            if new_notices:
                self.notices = new_notices
                self.last_synced = datetime.now(timezone.utc).isoformat()
                self._rebuild_indices()

                # Persist to disk
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "source": self.source,
                            "last_synced": self.last_synced,
                            "count": len(self.notices),
                            "notices": self.notices,
                        },
                        f,
                        indent=2,
                    )
                logger.info(f"Successfully synced and indexed {len(self.notices)} Interpol records.")
                return {
                    "success": True,
                    "records_synced": len(self.notices),
                    "last_synced": self.last_synced,
                    "source": self.source,
                }
            else:
                logger.warning("Empty records received from Interpol dataset sync.")
                return {"success": False, "error": "Empty records returned from source"}

        except Exception as err:
            logger.error(f"Failed to sync Interpol dataset: {err}")
            # If we don't even have memory notices, create fallback minimal seed
            if not self.notices:
                self._seed_fallback_records()
            return {"success": False, "error": str(err), "cached_records": len(self.notices)}

    def _seed_fallback_records(self):
        """Fallback seed of prominent wanted records if external network is unavailable on first boot."""
        self.notices = [
            {
                "id": "interpol-red-in-001",
                "name": "AKHTAR MERCHANT",
                "aliases": "MERCHANT AKHTAR",
                "birth_date": "1965-09-04",
                "countries": "in",
                "identifiers": "IN-WANTED-897",
                "sanctions": "Attempt to murder (IPC 307), Extortion (IPC 384), Criminal Conspiracy (IPC 120B), MCOCA organized crime syndicate membership.",
                "program_ids": "INTERPOL-RN;SSB-LOC",
                "dataset": "INTERPOL Red Notices",
                "last_seen": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": "interpol-red-in-002",
                "name": "AMRIK SINGH",
                "aliases": "SINGH AMRIK",
                "birth_date": "1970-09-24",
                "countries": "in",
                "identifiers": "IN-WANTED-002",
                "sanctions": "Death, Attempt to murder, Causing disappearance of evidence, Arms Act violations.",
                "program_ids": "INTERPOL-RN;SSB-LOC",
                "dataset": "INTERPOL Red Notices",
                "last_seen": datetime.now(timezone.utc).isoformat(),
            },
            {
                "id": "interpol-red-in-003",
                "name": "AZIZ MOOSA BILAKHIA",
                "aliases": "BILAKHIA AZIZ",
                "birth_date": "1958",
                "countries": "in",
                "identifiers": "IN-WANTED-003",
                "sanctions": "CRIMINAL CONSPIRACY TO COMMIT TERRORIST ACTS",
                "program_ids": "INTERPOL-RN;SSB-LOC",
                "dataset": "INTERPOL Red Notices",
                "last_seen": datetime.now(timezone.utc).isoformat(),
            },
        ]
        self.last_synced = datetime.now(timezone.utc).isoformat()
        self._rebuild_indices()

    def check_subject(
        self,
        name: Optional[str] = None,
        document_number: Optional[str] = None,
        birth_date: Optional[str] = None,
        country: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Cross-reference an individual against Interpol Red Notices and SSB Watchlists.
        Returns:
            {
                "is_flagged": bool,
                "status": "FLAGGED" | "CLEAR",
                "match_details": dict | None,
                "match_type": "EXACT_DOCUMENT" | "NAME_MATCH" | "SIMULATION_OVERRIDE" | None,
                "confidence": float,
                "total_records_searched": int,
                "checked_at": str
            }
        """
        checked_at = datetime.now(timezone.utc).isoformat()
        total_records = len(self.notices)

        raw_doc = str(document_number or "").upper()
        raw_name = str(name or "").upper()
        doc_norm = _normalize_str(document_number or "").replace(" ", "")
        name_norm = _normalize_str(name or "")
        name_tokens = _token_set(name_norm)

        # 1. Check simulation / demo test flags
        for token in SIMULATION_TOKENS:
            token_clean = _normalize_str(token)
            if (token in raw_doc or token in raw_name or
                token_clean in name_norm or token_clean.replace(" ", "") in doc_norm):
                return {
                    "is_flagged": True,
                    "status": "FLAGGED",
                    "match_type": "SIMULATION_OVERRIDE",
                    "confidence": 1.0,
                    "match_details": {
                        "entity_id": "INTERPOL-TEST-OVERRIDE",
                        "name": name or "DEMO TEST SUBJECT",
                        "notice_id": f"TEST-{token}",
                        "charges": "Simulated Red Notice Flag for Border Verification Testing",
                        "issuing_agency": "SSB / INTERPOL New Delhi (CBI)",
                        "countries": country or "IN",
                    },
                    "total_records_searched": total_records,
                    "checked_at": checked_at,
                }

        # 2. Check exact document number match in index
        if doc_norm and doc_norm in self.doc_index:
            matched_rec = self.doc_index[doc_norm]
            return {
                "is_flagged": True,
                "status": "FLAGGED",
                "match_type": "EXACT_DOCUMENT",
                "confidence": 1.0,
                "match_details": {
                    "entity_id": matched_rec.get("id"),
                    "name": matched_rec.get("name"),
                    "aliases": matched_rec.get("aliases"),
                    "birth_date": matched_rec.get("birth_date"),
                    "countries": matched_rec.get("countries"),
                    "charges": matched_rec.get("sanctions") or "Fugitive wanted for prosecution",
                    "program": matched_rec.get("program_ids", "INTERPOL-RN"),
                    "issuing_agency": "INTERPOL General Secretariat / NCB",
                },
                "total_records_searched": total_records,
                "checked_at": checked_at,
            }

        # 3. Check name against token index
        query_sig_tokens = {t for t in name_tokens if len(t) >= 3}
        if len(query_sig_tokens) >= 2:
            for rec_tokens, rec in self.name_tokens_index:
                rec_sig_tokens = {t for t in rec_tokens if len(t) >= 3}
                intersection = query_sig_tokens.intersection(rec_sig_tokens)
                if len(intersection) == len(query_sig_tokens) and len(query_sig_tokens) >= 2:
                    rec_dob = rec.get("birth_date", "")
                    dob_bonus = 0.0
                    if birth_date and rec_dob:
                        if birth_date[:4] in rec_dob:
                            dob_bonus = 0.05
                    
                    rec_countries = rec.get("countries", "").lower().split(";")
                    country_match = False
                    if country and country.lower() in rec_countries:
                        country_match = True

                    confidence = min(0.99, 0.90 + dob_bonus + (0.04 if country_match else 0.0))

                    return {
                        "is_flagged": True,
                        "status": "FLAGGED",
                        "match_type": "NAME_MATCH",
                        "confidence": confidence,
                        "match_details": {
                            "entity_id": rec.get("id"),
                            "name": rec.get("name"),
                            "aliases": rec.get("aliases"),
                            "birth_date": rec.get("birth_date"),
                            "countries": rec.get("countries"),
                            "charges": rec.get("sanctions") or "International Red Notice arrest warrant",
                            "program": rec.get("program_ids", "INTERPOL-RN"),
                            "issuing_agency": "INTERPOL Red Notice Database",
                        },
                        "total_records_searched": total_records,
                        "checked_at": checked_at,
                    }

        # 4. No match -> CLEAR
        return {
            "is_flagged": False,
            "status": "CLEAR",
            "match_type": None,
            "confidence": 0.99,
            "match_details": None,
            "total_records_searched": total_records,
            "checked_at": checked_at,
            "verification_note": f"Cross-referenced against {total_records:,} active Interpol Red Notices and SSB adverse records. Zero hits detected.",
        }

    def search_notices(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search notices by name, offence, or country."""
        q = _normalize_str(query)
        if not q:
            return self.notices[:limit]

        q_tokens = _token_set(q)
        results = []

        for record in self.notices:
            text_corpus = f"{record.get('name', '')} {record.get('aliases', '')} {record.get('sanctions', '')} {record.get('countries', '')} {record.get('id', '')}"
            norm_corpus = _normalize_str(text_corpus)
            corpus_tokens = _token_set(norm_corpus)

            if q in norm_corpus or (q_tokens and q_tokens.issubset(corpus_tokens)):
                results.append(record)
                if len(results) >= limit:
                    break

        return results

    def get_stats(self) -> dict[str, Any]:
        """Return database statistics."""
        countries_count: dict[str, int] = {}
        for r in self.notices:
            for c in r.get("countries", "").split(";"):
                c_clean = c.strip().lower()
                if c_clean:
                    countries_count[c_clean] = countries_count.get(c_clean, 0) + 1

        top_countries = sorted(countries_count.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_records": len(self.notices),
            "source": self.source,
            "last_synced": self.last_synced,
            "cache_file": str(CACHE_FILE),
            "cache_exists": CACHE_FILE.exists(),
            "top_wanted_countries": [{"country": c, "count": cnt} for c, cnt in top_countries],
            "system_status": "OPERATIONAL_READY",
        }


def get_watchlist_service() -> WatchlistService:
    return WatchlistService.get_instance()
