import os
import re
import requests
from config import SHORTENER_API

def clean_filename(filename: str) -> dict:
    name = os.path.basename(filename)

    # remove extension
    name = re.sub(r"\.[^.]+$", "", name)

    # normalize separators
    normalized = re.sub(r"[._]+", " ", name)

    # year
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", normalized)
    year = int(year_match.group(1)) if year_match else None

    # quality
    quality_match = re.search(
        r"\b(480p|720p|1080p|2160p|4K|HDRip|WEB[- ]DL|BluRay|BRRip|DVDRip)\b",
        normalized,
        re.IGNORECASE
    )
    quality = quality_match.group(1) if quality_match else ""

    # language
    lang_match = re.search(
        r"\b(Hindi|English|Tamil|Telugu|Malayalam|Kannada|Dual Audio|Multi Audio)\b",
        normalized,
        re.IGNORECASE
    )
    language = lang_match.group(1) if lang_match else ""

    title = normalized
    if year:
        title = re.split(rf"\b{year}\b", title, maxsplit=1)[0]
    title = re.sub(
        r"\b(480p|720p|1080p|2160p|4K|HDRip|WEB[- ]DL|BluRay|BRRip|DVDRip|Hindi|English|Tamil|Telugu|Malayalam|Kannada|Dual Audio|Multi Audio)\b",
        "",
        title,
        flags=re.IGNORECASE
    )
    title = re.sub(r"\s+", " ", title).strip(" -_.")

    return {
        "title": title or normalized.strip(),
        "year": year,
        "quality": quality,
        "language": language,
    }

def shortify(url: str) -> str:
    if not SHORTENER_API:
        return url

    try:
        response = requests.post(
            SHORTENER_API,
            json={"originalURL": url},
            timeout=10
        )
        if response.ok:
            data = response.json()
            return data.get("shortURL") or data.get("short_url") or url
    except Exception:
        pass

    return url
