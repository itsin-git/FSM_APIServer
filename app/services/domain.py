"""Domain service – builds XML response for GET /phoenix/rest/config/Domain."""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import Dict, List

from app.repositories.domain import DomainRepository

logger = logging.getLogger("fsmapi.service.domain")


def _bool_text(value) -> str:
    """Convert PostgreSQL boolean (True/False/None) to 'true'/'false' string."""
    return "true" if value is True else "false"


def _build_xml(domains: list, collectors_by_domain: Dict[int, List[str]]) -> str:
    root = ET.Element("response")
    root.set("requestId", "0")
    root.set("timestamp", str(int(time.time() * 1000)))

    result_el = ET.SubElement(root, "result")
    domains_el = ET.SubElement(result_el, "domains")

    for d in domains:
        domain_el = ET.SubElement(domains_el, "domain")
        domain_el.set("entityVersion", str(d.get("entity_version") or 0))
        domain_el.set("creationTime", str(d.get("creation_time") or 0))
        domain_el.set("custId", str(d.get("cust_org_id") or 0))
        domain_el.set("id", str(d.get("id") or 0))
        domain_el.set("lastModified", str(d.get("last_modified_time") or 0))
        domain_el.set("ownerId", str(d.get("owner_id") or 0))
        domain_el.set("xmlId", f"Domain${d.get('name', '')}")

        # <collectors> — only when collectors exist for this domain
        domain_id = d.get("domain_id")
        collectors = collectors_by_domain.get(domain_id, [])
        if collectors:
            collectors_el = ET.SubElement(domain_el, "collectors")
            for nat_id in collectors:
                c_el = ET.SubElement(collectors_el, "collector")
                c_el.text = f"EventCollector${nat_id}"

        ET.SubElement(domain_el, "custProperties")

        disabled_el = ET.SubElement(domain_el, "disabled")
        disabled_el.text = _bool_text(d.get("disabled"))

        domain_id_el = ET.SubElement(domain_el, "domainId")
        domain_id_el.text = str(domain_id or 0)

        exclude_range = d.get("exclude_range")
        if exclude_range:
            er_el = ET.SubElement(domain_el, "excludeRange")
            er_el.text = exclude_range

        include_range = d.get("include_range")
        if include_range:
            ir_el = ET.SubElement(domain_el, "includeRange")
            ir_el.text = include_range

        initialized_el = ET.SubElement(domain_el, "initialized")
        initialized_el.text = _bool_text(d.get("initialized"))

        name_el = ET.SubElement(domain_el, "name")
        name_el.text = d.get("name", "")

    ET.SubElement(result_el, "eventForwardingRules")

    xml_body = ET.tostring(root, encoding="unicode")
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + xml_body


class DomainService:
    def __init__(self, repo: DomainRepository):
        self._repo = repo

    async def list_domains_xml(self) -> str:
        domains = await self._repo.list_domains()
        raw_collectors = await self._repo.list_domain_collectors()

        collectors_by_domain: Dict[int, List[str]] = defaultdict(list)
        for row in raw_collectors:
            collectors_by_domain[row["cust_org_id"]].append(row["natural_id"])

        return _build_xml(domains, collectors_by_domain)
