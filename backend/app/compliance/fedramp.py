"""FedRAMP-ready control surface.

Tracks the subset of NIST 800-53 Rev.5 controls the platform claims
to inherit or implement directly. Each control has:

* `id` (e.g. AC-2, AU-2)
* status (inherited / implemented / planned / gap)
* evidence source (pointer to audit pack)
* last-checked timestamp

The Compliance Agent calls `fedramp.refresh()` daily; findings become
`HITLItem`s when status regresses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Literal


Status = Literal["inherited", "implemented", "planned", "gap"]


@dataclass
class Control:
    id: str
    name: str
    family: str
    status: Status
    evidence: str | None = None
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FedRAMPControls:
    def __init__(self) -> None:
        self._controls: dict[str, Control] = {}
        self._lock = RLock()
        seed = [
            # Access Control
            Control("AC-2", "Account Management", "AC", "implemented", "iam-audit-pack-q1.pdf"),
            Control("AC-3", "Access Enforcement", "AC", "implemented", "opa-policies"),
            Control("AC-6", "Least Privilege", "AC", "implemented", "iam-audit-pack-q1.pdf"),
            # Audit
            Control("AU-2", "Event Logging", "AU", "implemented", "audit-pipeline"),
            Control("AU-6", "Audit Review", "AU", "implemented", "audit-dashboard"),
            Control("AU-12", "Audit Generation", "AU", "implemented", "audit-pipeline"),
            # Configuration Management
            Control("CM-2", "Baseline Configuration", "CM", "implemented", "iac-repo"),
            Control("CM-3", "Configuration Change Control", "CM", "implemented", "change-ci"),
            # Contingency
            Control("CP-9", "System Backup", "CP", "implemented", "backup-reports"),
            Control("CP-10", "System Recovery", "CP", "implemented", "dr-runbooks"),
            # Incident Response
            Control("IR-4", "Incident Handling", "IR", "implemented", "incident-console"),
            Control("IR-5", "Incident Monitoring", "IR", "implemented", "live-ops"),
            Control("IR-8", "Incident Response Plan", "IR", "implemented", "pir-agent"),
            # Risk Assessment
            Control("RA-5", "Vulnerability Scanning", "RA", "planned"),
            # SC
            Control("SC-7", "Boundary Protection", "SC", "implemented", "network-policies"),
            Control("SC-12", "Cryptographic Key Establishment", "SC", "implemented", "kms"),
            Control("SC-13", "Cryptographic Protection", "SC", "implemented", "kms"),
            # SI
            Control("SI-4", "System Monitoring", "SI", "implemented", "observability"),
            Control("SI-7", "Software Integrity", "SI", "planned"),
        ]
        for c in seed:
            self._controls[c.id] = c

    def list(self) -> list[Control]:
        with self._lock:
            return list(self._controls.values())

    def summary(self) -> dict[str, int]:
        counts = {"inherited": 0, "implemented": 0, "planned": 0, "gap": 0}
        for c in self._controls.values():
            counts[c.status] += 1
        return counts

    def mark(self, control_id: str, status: Status, evidence: str | None = None) -> Control:
        with self._lock:
            c = self._controls.setdefault(control_id, Control(control_id, control_id, "?", "planned"))
            c.status = status
            c.evidence = evidence
            c.last_checked = datetime.now(timezone.utc)
            return c


fedramp = FedRAMPControls()
