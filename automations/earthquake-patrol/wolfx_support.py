"""Validated Wolfx EEW parsing, geocoding, and Push copy policies."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple


BAIDU_REVERSE_GEOCODING_URL = "https://api.map.baidu.com/reverse_geocoding/v3/"
WOLFX_MAX_EVENT_AGE_SECONDS = 300
PUSH_MAGNITUDE_BOUNDARY = 4.0
LOW_MAGNITUDE_PUSH_TITLES = (
    "刚刚，{short_location}发生{magnitude}级地震",
    "{short_location}地震预警，{magnitude}级",
    "【地震快讯】{city_location}初估{magnitude}级",
    "{short_location}地震预警，初估{magnitude}级",
    "{short_location}发生{magnitude}级地震",
    "刚刚！{short_location}{magnitude}级地震",
    "{magnitude}级！震中{city_location}",
    "{city_location}初估{magnitude}级地震",
)
LOW_MAGNITUDE_PUSH_CONTENTS = (
    "预警首报，稍后更新",
    "初步定位，持续更新",
    "首报数据，稍后更新",
    "正式结果稍后更新",
    "初步测定，结果待定",
    "正式测定稍后更新",
    "参数初报，持续更新",
    "正式测定结果待更新",
)
HIGH_MAGNITUDE_PUSH_TITLES = (
    "{magnitude}级！{short_location}发生地震",
    "刚刚，{short_location}发生{magnitude}级地震",
    "【地震快讯】{short_location}{magnitude}级",
    "{short_location}{magnitude}级地震！",
    "{city_location}发生{magnitude}级地震",
    "{magnitude}级地震！震中{short_location}",
    "{short_location}突发{magnitude}级地震",
    "{short_location}地震，初估{magnitude}级",
)
HIGH_MAGNITUDE_PUSH_CONTENTS = (
    "请注意安全，谨慎避险",
    "保持冷静，注意避险",
    "正式测定结果稍后更新",
    "如有震感，请注意安全",
    "远离玻璃，注意落物",
    "参数初报，持续更新",
    "正式结果稍后更新",
)


def wolfx_location_fallback(raw_location: Any) -> str:
    """Return a safe Yibin county-or-better name supplied by Wolfx."""
    location = re.sub(r"\s+", "", str(raw_location or "")).replace("附近", "").strip()
    prefix = "四川宜宾市"
    if not location.startswith(prefix) or not location[len(prefix) :]:
        raise ValueError("Wolfx location is not a usable Yibin county-level name")
    return location


def _push_locations(raw_location: Any) -> Tuple[str, str]:
    location = re.sub(r"\s+", "", str(raw_location or "")).replace("附近", "").strip()
    full_prefix = "四川宜宾市"
    city_prefix = "宜宾市"
    short_prefix = "宜宾"
    if location.startswith(full_prefix):
        suffix = location[len(full_prefix) :]
        if not suffix:
            raise ValueError("Push location is missing a Yibin district or county")
        return short_prefix + suffix, city_prefix + suffix
    if location.startswith(city_prefix):
        suffix = location[len(city_prefix) :]
        if not suffix:
            raise ValueError("Push location is missing a Yibin district or county")
        return short_prefix + suffix, location
    if location.startswith(short_prefix):
        suffix = location[len(short_prefix) :]
        if not suffix:
            raise ValueError("Push location is missing a Yibin district or county")
        return location, city_prefix + suffix
    if not location:
        raise ValueError("Push location is required")
    return location, location


def _stable_choice(values: Tuple[str, ...], event_key: str, namespace: str) -> str:
    digest = hashlib.sha256(f"{namespace}\0{event_key}".encode("utf-8")).digest()
    return values[int.from_bytes(digest[:8], "big") % len(values)]


def build_wolfx_push_copy(event: Any) -> Tuple[str, str]:
    if not event.precise_location:
        raise ValueError("precise location is required for Wolfx Push")
    short_location, city_location = _push_locations(event.precise_location)
    values = {
        "short_location": short_location,
        "city_location": city_location,
        "magnitude": f"{event.magnitude:.1f}",
    }
    if event.magnitude < PUSH_MAGNITUDE_BOUNDARY:
        title_templates = LOW_MAGNITUDE_PUSH_TITLES
        content_pool = LOW_MAGNITUDE_PUSH_CONTENTS
        magnitude_band = "low"
    else:
        title_templates = HIGH_MAGNITUDE_PUSH_TITLES
        content_pool = HIGH_MAGNITUDE_PUSH_CONTENTS
        magnitude_band = "high"
    title_pool = tuple(
        title
        for template in title_templates
        if len(title := template.format(**values)) <= 20
    )
    approved_content_pool = tuple(content for content in content_pool if len(content) <= 10)
    if not title_pool or not approved_content_pool:
        raise ValueError("Push copy is too long for approved title or content limits")
    return (
        _stable_choice(title_pool, event.key, f"{magnitude_band}-title"),
        _stable_choice(
            approved_content_pool,
            event.key,
            f"{magnitude_band}-content",
        ),
    )


def parse_wolfx_payload(
    payload: Dict[str, Any],
    *,
    now: Optional[datetime] = None,
    max_age_seconds: int = WOLFX_MAX_EVENT_AGE_SECONDS,
) -> Dict[str, Any]:
    source_type = str(
        payload.get("type") or payload.get("_wolfx_channel") or ""
    ).strip()
    if source_type not in {"sc_eew", "cenc_eew"}:
        raise ValueError("unsupported Wolfx message type")

    raw_event_id = str(payload.get("EventID") or "").strip()
    if not raw_event_id or len(raw_event_id) > 80:
        raise ValueError("invalid Wolfx event id")
    normalized_id = re.sub(r"_\d+$", "", raw_event_id)
    normalized_id = re.sub(r"[^A-Za-z0-9_-]+", "_", normalized_id).strip("_")
    if not normalized_id:
        raise ValueError("invalid Wolfx event id")
    try:
        report_number = int(payload.get("ReportNum"))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid Wolfx report number") from exc
    if not (1 <= report_number <= 1000):
        raise ValueError("invalid Wolfx report number")

    try:
        occurred_at = datetime.strptime(
            str(payload["OriginTime"]), "%Y-%m-%d %H:%M:%S"
        )
        report_time = datetime.strptime(
            str(payload["ReportTime"]), "%Y-%m-%d %H:%M:%S"
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid Wolfx event time") from exc
    report_delay = (report_time - occurred_at).total_seconds()
    if not (-60 <= report_delay <= 600):
        raise ValueError("invalid Wolfx report delay")
    age_seconds = ((now or datetime.now()) - occurred_at).total_seconds()
    if age_seconds > int(max_age_seconds):
        raise ValueError("stale Wolfx event")
    if age_seconds < -60:
        raise ValueError("Wolfx event time is in the future")

    magnitude_field = "Magunitude" if source_type == "sc_eew" else "Magnitude"
    location = str(payload.get("HypoCenter") or "").strip()
    try:
        longitude = float(payload.get("Longitude"))
        latitude = float(payload.get("Latitude"))
        magnitude = float(payload.get(magnitude_field))
        depth = (
            float(payload.get("Depth"))
            if payload.get("Depth") is not None
            else None
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid Wolfx numeric fields") from exc
    if not location or len(location) > 100:
        raise ValueError("invalid Wolfx location")
    if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
        raise ValueError("invalid Wolfx coordinates")
    if not (0 <= magnitude <= 10):
        raise ValueError("invalid Wolfx magnitude")
    if depth is not None and not (0 <= depth <= 800):
        raise ValueError("invalid Wolfx depth")

    return {
        "id": occurred_at.strftime("%Y%m%d%H%M%S"),
        "uniEventId": "WX" + normalized_id,
        "oriTime": occurred_at.strftime("%Y-%m-%d %H:%M:%S"),
        "locName": location,
        "epiLon": longitude,
        "epiLat": latitude,
        "focDepth": depth,
        "magnitude": magnitude,
        "isPreliminary": True,
        "_source": "wolfx_sc" if source_type == "sc_eew" else "wolfx_cenc",
    }


class ReverseGeocoder:
    def __init__(self, api_key: str, transport: Any):
        self.api_key = str(api_key).strip()
        self.transport = transport

    @staticmethod
    def _clean_name(value: Any) -> str:
        return re.sub(r"\s+", "", str(value or "")).replace("附近", "").strip()

    def reverse(self, latitude: float, longitude: float) -> str:
        if not self.api_key:
            raise RuntimeError("Baidu reverse geocoding API key is missing")
        payload = self.transport.request_json(
            "GET",
            BAIDU_REVERSE_GEOCODING_URL,
            params={
                "ak": self.api_key,
                "output": "json",
                "coordtype": "wgs84ll",
                "extensions_poi": 1,
                "entire_poi": 1,
                "sort_strategy": "distance",
                "radius": 1000,
                "region_data_source": 2,
                "location": f"{float(latitude):.6f},{float(longitude):.6f}",
            },
        )
        if payload.get("status") != 0:
            raise RuntimeError(
                "Baidu reverse geocoding failed: "
                + str(payload.get("message") or payload.get("status") or "unknown")
            )
        result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
        component = (
            result.get("addressComponent")
            if isinstance(result.get("addressComponent"), dict)
            else {}
        )
        province = self._clean_name(component.get("province"))
        city = self._clean_name(component.get("city"))
        district = self._clean_name(component.get("district"))
        if province != "四川省" or city != "宜宾市" or not district:
            raise RuntimeError("reverse geocoding result is outside Yibin")

        town = self._clean_name(component.get("town"))
        village = self._clean_name(component.get("village"))
        if village:
            return village if village.startswith(town) else town + village

        regions = result.get("poiRegions") if isinstance(result.get("poiRegions"), list) else []
        for region in regions:
            if not isinstance(region, dict):
                continue
            name = self._clean_name(region.get("name"))
            distance = str(region.get("distance") or "").strip()
            direction = self._clean_name(region.get("direction_desc"))
            if name and (distance in {"", "0", "0.0"} or "内" in direction):
                return name

        pois = result.get("pois") if isinstance(result.get("pois"), list) else []
        nearby = []
        for poi in pois:
            if not isinstance(poi, dict):
                continue
            name = self._clean_name(poi.get("name"))
            try:
                distance = float(poi.get("distance"))
            except (TypeError, ValueError):
                continue
            if name and 0 <= distance <= 100:
                nearby.append((distance, name))
        if nearby:
            return min(nearby)[1]

        street = self._clean_name(component.get("street"))
        if street:
            return town + street if not street.startswith(town) else street

        # A verified county name is an acceptable fast-alert fallback. Keep the
        # full administrative name and never manufacture an “附近” qualifier.
        province_short = province[:-1] if province.endswith("省") else province
        return province_short + city + district
