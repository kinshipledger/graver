"""Readable offline specimens for the Find a Grave parser contract.

These responses are deliberately generated from small, maintained domain fixtures.
They are not recordings of provider pages and contain no incidental page chrome,
scripts, account data, cookies, or session metadata.
"""

import json
import re
from html import escape
from pathlib import Path
from urllib.parse import parse_qs, urlparse

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(kind: str, name: str) -> dict:
    path = FIXTURES / kind / f"{name}.json"
    return json.loads(path.read_text())


MEMORIALS = {
    item["findagrave_url"]: item
    for item in (
        _load_fixture("memorials", name)
        for name in (
            "andrew-jackson",
            "carl-sagan",
            "dennis-macalistair-ritchie",
            "george-washington",
            "grace-brewster-hopper",
            "isaac-asimov",
            "james-fenimore-cooper",
            "john-j-pershing",
            "john-quincy-adams",
            "martin-luther-king",
            "rachel-machado-levy",
            "rod-serling",
            "thomas-jefferson",
        )
    )
}

CEMETERIES = {
    item["findagrave_url"]: item
    for item in (
        _load_fixture("cemeteries", name)
        for name in (
            "arlington-national-cemetery",
            "crown-hill-memorial-park",
            "monticello-graveyard",
        )
    )
}
CEMETERIES.update(
    {
        "https://www.findagrave.com/cemetery/1990395/honolulu-memorial": {
            "cemetery_id": 1990395,
            "findagrave_url": (
                "https://www.findagrave.com/cemetery/1990395/honolulu-memorial"
            ),
            "name": "Honolulu Memorial",
            "location": "Honolulu, Honolulu County, Hawaii, USA",
            "coords": "21.3132,-157.8475",
            "num_memorials": 2,
        },
        "https://www.findagrave.com/cemetery/2783285/rachel-levy-gravesite": {
            "cemetery_id": 2783285,
            "findagrave_url": (
                "https://www.findagrave.com/cemetery/2783285/" "rachel-levy-gravesite"
            ),
            "name": "Rachel Levy Gravesite",
            "location": "Albemarle County, Virginia, USA",
            "coords": "38.0092,-78.4527",
            "num_memorials": 1,
        },
    }
)


def _display_name(memorial: dict) -> str:
    tokens = []
    if memorial.get("prefix"):
        tokens.append(escape(memorial["prefix"]))
    name_tokens = memorial["name"].split()
    maiden = memorial.get("maiden_name")
    nickname = memorial.get("nickname")
    if len(name_tokens) > 1 and (maiden or nickname):
        tokens.extend(escape(token) for token in name_tokens[:-1])
        if maiden:
            tokens.append(f"<i>{escape(maiden)}</i>")
        if nickname:
            tokens.append(f"“{escape(nickname)}”")
        tokens.append(escape(name_tokens[-1]))
    else:
        tokens.append(escape(memorial["name"]))
    if memorial.get("suffix"):
        tokens.append(escape(memorial["suffix"]))
    return " ".join(tokens)


def _badges(memorial: dict, search: bool = False) -> str:
    parts = []
    if memorial.get("famous"):
        title = "Famous Memorial" if search else "Famous memorial"
        parts.append(f'<span title="{title}"></span>')
    if memorial.get("veteran"):
        parts.append('<span title="Veteran">VVeteran</span>')
    return "".join(parts)


def memorial_html(memorial: dict) -> str:
    burial_place = memorial.get("burial_place") or "Burial Details Unknown"
    cemetery_id = memorial.get("cemetery_id")
    if cemetery_id is None:
        burial = f'<span id="otherPlace">{escape(burial_place)}</span>'
    else:
        burial_parts = burial_place.split(", ")
        address_parts = 4 if len(burial_parts) >= 5 else 3
        cemetery_name = ", ".join(burial_parts[:-address_parts])
        address = ",".join(burial_parts[-address_parts:])
        burial = (
            '<div itemtype="https://schema.org/Cemetery">'
            f'<a href="/cemetery/{cemetery_id}/synthetic">'
            f"{escape(cemetery_name)}</a></div>"
            f'<span itemprop="address">{escape(address)}</span>'
        )
    if memorial.get("coords"):
        burial += (
            '<span itemtype="https://schema.org/Map">'
            f'<a href="https://maps.example.test/?q={escape(memorial["coords"])}">'
            "Map</a></span>"
        )

    original_name = ""
    if memorial.get("original_name"):
        original_name = (
            "<dt>Original Name</dt>" f"<dd>{escape(memorial['original_name'])}</dd>"
        )
    plot = ""
    if memorial.get("plot"):
        plot = f"<dt>Plot</dt><dd>{escape(memorial['plot'])}</dd>"
    description = (
        "A maintained synthetic biography specimen."
        if memorial.get("has_bio")
        else f"Find a Grave memorial for {escape(memorial['name'])}"
    )
    added = ""
    if memorial.get("date_added"):
        added = (
            '<input id="addedDate" type="hidden" '
            f'value="Added: {escape(memorial["date_added"])}">'
        )
    return f"""<html><head>
<link rel="canonical" href="{escape(memorial['findagrave_url'])}">
<meta property="og:description" content="{description}">
</head><body>{added}<div class="synthetic-vitals">
<h1 id="bio-name">{_badges(memorial)}{_display_name(memorial)}</h1>
<dl>{original_name}
<dt>Birth</dt><dd><time itemprop="birthDate">{escape(memorial['birth'])}</time>
<div itemprop="birthPlace">{escape(memorial.get('birth_place') or '')}</div></dd>
<dt>Death</dt><dd><span itemprop="deathDate">{escape(memorial['death'])}</span>
<div itemprop="deathPlace">{escape(memorial.get('death_place') or '')}</div></dd>
<dt>{escape(memorial.get('memorial_type') or 'Burial')}</dt><dd>{burial}</dd>
{plot}<dt>Memorial ID</dt><dd><span id="memNumberLabel">{memorial['memorial_id']}</span></dd>
</dl></div></body></html>"""


def cemetery_html(cemetery: dict) -> str:
    location = cemetery["location"].split(", ", 2)
    locality, region, country = (location + [""] * 3)[:3]
    latitude, longitude = cemetery["coords"].split(",", 1)
    return f"""<html><head>
<link rel="canonical" href="{escape(cemetery['findagrave_url'])}">
</head><body><h1 itemprop="name">{escape(cemetery['name'])}</h1>
<span itemprop="addressLocality">{escape(locality)}</span>
<span itemprop="addressRegion">{escape(region)}</span>
<span itemprop="addressCountry">{escape(country)}</span>
<span title="Latitude:">{escape(latitude)}</span>
<span title="Longitude:">{escape(longitude)}</span>
<div id="MemorialsAll"><ul><li><a>View Memorials {cemetery['num_memorials']:,}</a></li></ul></div>
</body></html>"""


def _summary_group(memorial: dict) -> str:
    memorial_type = memorial.get("memorial_type") or "Burial"
    type_button = (
        f"<button>{escape(memorial_type)}</button>"
        if memorial_type in {"Cenotaph", "Monument"}
        else ""
    )
    burial_place = memorial.get("burial_place") or "Synthetic Cemetery, Test County"
    cemetery_name, _, cemetery_location = burial_place.partition(", ")
    cemetery_id = memorial.get("cemetery_id") or 900001
    plot = memorial.get("plot")
    plot_html = f"<p>Plot info: {escape(plot)}</p>" if plot else ""
    path = urlparse(memorial["findagrave_url"]).path
    return f"""<div role="group"><a href="{escape(path)}">Open</a>
<div class="memorial-item--info">
<h2 class="name-grave">{_badges(memorial, search=True)}<i class="pe-2">{_display_name(memorial)}</i></h2>
<div class="memorial-item---grave"><h2>{type_button}</h2>
<b class="birthDeathDates">{escape(memorial['birth'])} – {escape(memorial['death'])}</b></div>
</div><div class="memorial-item---cemet">
<form action="/cemetery/{cemetery_id}/synthetic">{escape(cemetery_name)}</form>
<p>{escape(cemetery_location)}</p>{plot_html}</div></div>"""


def _synthetic_summary(index: int, *, surname: str = "Example", veteran=True) -> dict:
    return {
        "memorial_id": 900000 + index,
        "findagrave_url": (
            f"https://www.findagrave.com/memorial/{900000 + index}/"
            f"test-person-{index}"
        ),
        "name": f"Test Person {surname} {index}",
        "prefix": None,
        "suffix": None,
        "nickname": None,
        "maiden_name": None,
        "famous": False,
        "veteran": veteran,
        "birth": f"1 Jan {1800 + index}",
        "death": f"1 Jan {1870 + index}",
        "memorial_type": "Burial",
        "burial_place": "Synthetic Cemetery, Test County, Test State, USA",
        "cemetery_id": 900001,
        "plot": f"Plot {index}",
    }


def search_html(memorials: list[dict], total: int | None = None) -> str:
    count = len(memorials) if total is None else total
    groups = "".join(_summary_group(memorial) for memorial in memorials)
    return (
        f"<html><body><h1>{count:,} matching records found</h1>{groups}</body></html>"
    )


def _memorial_for_name(params: dict[str, list[str]]) -> dict | None:
    def normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.casefold())

    first = normalize(params.get("firstname", [""])[0])
    middle = normalize(params.get("middlename", [""])[0])
    last = normalize(params.get("lastname", [""])[0])
    if not any((first, middle, last)):
        return None
    for memorial in MEMORIALS.values():
        normalized = normalize(memorial["name"])
        if first and first not in normalized:
            continue
        if middle and middle not in normalized:
            continue
        if last and last not in normalized:
            continue
        return memorial
    return None


def general_search(params: dict[str, list[str]]) -> str:
    first = params.get("firstname", [""])[0]
    last = params.get("lastname", [""])[0]
    page = int(params.get("page", ["1"])[0])
    matched = _memorial_for_name(params)
    if matched is not None:
        return search_html([matched])
    if last.casefold() == "jackson":
        start = (page - 1) * 20 + 1
        rows = [
            _synthetic_summary(index, surname="Jackson")
            for index in range(start, start + 20)
        ]
        return search_html(rows, total=40)
    active_filters = {
        key: value
        for key, value in params.items()
        if any(item not in {"", "r"} for item in value) and key not in {"page"}
    }
    if not first and not last and not active_filters:
        return search_html([])
    rows = [_synthetic_summary(index) for index in range(1, 6)]
    return search_html(rows, total=5)


def cemetery_search(cemetery_id: int, params: dict[str, list[str]]) -> str:
    first = params.get("firstname", [""])[0].casefold()
    page = int(params.get("page", ["1"])[0])
    if cemetery_id == 1990395:
        item = _synthetic_summary(1)
        item["name"] = "Adrian Williams" if first == "adrian" else "Harold Costill"
        item["memorial_type"] = "Monument" if first == "adrian" else "Cenotaph"
        return search_html([item])
    if cemetery_id == 49269:
        start = (page - 1) * 20 + 1
        rows = [_synthetic_summary(index) for index in range(start, start + 20)]
        return search_html(rows, total=40)
    if cemetery_id == 641519:
        start = (page - 1) * 20 + 1
        count = 20 if "page" in params else 18
        rows = [
            _synthetic_summary(index, veteran=True)
            for index in range(start, start + count)
        ]
        return search_html(rows, total=count)
    if cemetery_id == 2783285:
        return search_html(
            [
                MEMORIALS[
                    _load_fixture("memorials", "rachel-machado-levy")["findagrave_url"]
                ]
            ]
        )
    return search_html([])


def response_for(url: str) -> tuple[int, str]:
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    params = parse_qs(parsed.query, keep_blank_values=True)

    if base_url == "https://www.findagrave.com/memorial/should-produce-404":
        return 404, "<html><body><p>Not found</p></body></html>"
    if base_url.endswith("/memorial/900101/example-merged"):
        return (
            404,
            "<div class='jumbotron text-center'>Memorial has been merged"
            "<p><a href='/memorial/900102/example-replacement'>"
            "Merged memorial</a></p></div>",
        )
    if base_url.endswith("/memorial/900103/example-removed"):
        return (
            404,
            "<div class='jumbotron text-center'>This memorial has been removed.</div>",
        )
    if base_url in MEMORIALS:
        return 200, memorial_html(MEMORIALS[base_url])
    if base_url in CEMETERIES:
        return 200, cemetery_html(CEMETERIES[base_url])
    if parsed.path == "/memorial/search":
        return 200, general_search(params)
    match = re.fullmatch(r"/cemetery/(\d+)/memorial-search", parsed.path)
    if match:
        return 200, cemetery_search(int(match.group(1)), params)
    raise AssertionError(f"No synthetic provider response is defined for {url}")
