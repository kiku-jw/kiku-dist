"""Prepare listing - generate marketplace copy from OpenAPI + docs."""

import json
from pathlib import Path
from typing import Any

from kiku_dist.openapi import extract_api_info, load_openapi, validate_openapi


def generate_listing(
    openapi_path: Path,
    readme_path: Path | None = None,
    product_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate marketplace listing content from OpenAPI spec and docs."""

    # Load and validate OpenAPI
    spec = load_openapi(openapi_path)
    if not spec:
        raise ValueError(f"Cannot load OpenAPI from {openapi_path}")

    errors = validate_openapi(spec)
    if errors:
        raise ValueError(f"OpenAPI validation failed: {errors}")

    api_info = extract_api_info(spec)

    # Load README for additional context
    readme_content = ""
    if readme_path and readme_path.exists():
        readme_content = readme_path.read_text()

    # Generate listing sections
    listing = {
        "name": api_info["title"],
        "version": api_info["version"],
        "tagline": _generate_tagline(api_info, readme_content),
        "description": _generate_description(api_info, readme_content),
        "features": _extract_features(readme_content),
        "use_cases": _extract_use_cases(api_info, readme_content),
        "endpoints": _generate_endpoints_doc(spec),
        "pricing": _generate_pricing(product_config),
        "tags": _generate_tags(api_info),
        "category": _suggest_category(api_info),
    }

    return listing


def _generate_tagline(api_info: dict, readme: str) -> str:
    """Generate short tagline (max 150 chars)."""
    desc = api_info.get("description", "")
    if desc and len(desc) <= 150:
        return desc

    # Extract first sentence from description
    if desc:
        first_sentence = desc.split(".")[0]
        if len(first_sentence) <= 150:
            return first_sentence + "."

    return f"{api_info['title']} - {api_info['endpoint_count']} endpoints"


def _generate_description(api_info: dict, readme: str) -> str:
    """Generate full description for marketplace listing."""
    lines = []

    # Title and overview
    lines.append(f"# {api_info['title']}")
    lines.append("")

    if api_info.get("description"):
        lines.append(api_info["description"])
        lines.append("")

    # Key stats
    lines.append("## Quick Facts")
    lines.append(f"- **Endpoints:** {api_info['endpoint_count']}")
    lines.append(f"- **Methods:** {', '.join(api_info['methods'])}")
    if api_info.get("tags"):
        lines.append(f"- **Categories:** {', '.join(api_info['tags'][:5])}")
    lines.append("")

    # Extract key sections from README
    if readme:
        # Try to find Features section
        if "## Features" in readme or "## Key Features" in readme:
            lines.append(_extract_readme_section(readme, "Features"))

        # Try to find How it works
        if "## How" in readme or "## Usage" in readme:
            lines.append(_extract_readme_section(readme, "How"))

    return "\n".join(lines)


def _extract_readme_section(readme: str, section_keyword: str) -> str:
    """Extract a section from README by keyword."""
    lines = readme.split("\n")
    in_section = False
    section_lines = []

    for line in lines:
        if line.startswith("##") and section_keyword.lower() in line.lower():
            in_section = True
            section_lines.append(line)
            continue

        if in_section:
            if line.startswith("##"):
                break
            section_lines.append(line)

    return "\n".join(section_lines)


def _extract_features(readme: str) -> list[str]:
    """Extract feature list from README."""
    features = []

    if not readme:
        return features

    lines = readme.split("\n")
    in_features = False

    for line in lines:
        if "feature" in line.lower() and line.startswith("##"):
            in_features = True
            continue

        if in_features:
            if line.startswith("##"):
                break
            # Extract bullet points
            if line.strip().startswith("-") or line.strip().startswith("*"):
                feature = line.strip().lstrip("-*").strip()
                if feature and len(feature) < 200:
                    features.append(feature)

    return features[:10]  # Max 10 features


def _extract_use_cases(api_info: dict, readme: str) -> list[str]:
    """Extract or generate use cases."""
    use_cases = []

    # Common use cases based on tags
    tag_use_cases = {
        "pii": ["Data anonymization for ML training", "GDPR compliance"],
        "privacy": ["Privacy-first data processing", "Secure data handling"],
        "masking": ["Log sanitization", "Test data generation"],
        "routing": ["Cost optimization", "Latency optimization"],
        "llm": ["AI application development", "Chatbot integration"],
    }

    for tag in api_info.get("tags", []):
        tag_lower = tag.lower()
        for key, cases in tag_use_cases.items():
            if key in tag_lower:
                use_cases.extend(cases)

    return list(set(use_cases))[:5]


def _generate_endpoints_doc(spec: dict) -> list[dict]:
    """Generate endpoint documentation."""
    endpoints = []
    paths = spec.get("paths", {})

    for path, operations in paths.items():
        for method, details in operations.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue

            endpoint = {
                "method": method.upper(),
                "path": path,
                "summary": details.get("summary", ""),
                "description": details.get("description", ""),
            }

            # Extract parameters
            params = details.get("parameters", [])
            if params:
                endpoint["parameters"] = [
                    {"name": p.get("name"), "in": p.get("in"), "required": p.get("required", False)}
                    for p in params
                ]

            endpoints.append(endpoint)

    return endpoints


def _generate_pricing(config: dict | None) -> dict:
    """Generate pricing structure."""
    if config and "rapidapi" in config:
        rapid_config = config["rapidapi"]
        return {
            "model": rapid_config.get("pricing_model", "freemium"),
            "tiers": rapid_config.get("tiers", [
                {"name": "Basic", "price": 0, "requests": 100},
                {"name": "Pro", "price": 29, "requests": 10000},
                {"name": "Ultra", "price": 99, "requests": 100000},
            ])
        }

    # Default pricing
    return {
        "model": "freemium",
        "tiers": [
            {"name": "Basic", "price": 0, "requests": 100},
            {"name": "Pro", "price": 29, "requests": 10000},
            {"name": "Ultra", "price": 99, "requests": 100000},
        ]
    }


def _generate_tags(api_info: dict) -> list[str]:
    """Generate tags for marketplace."""
    tags = list(api_info.get("tags", []))

    # Add common tags based on title/description
    title_lower = api_info.get("title", "").lower()
    desc_lower = api_info.get("description", "").lower()

    keyword_tags = {
        "mask": ["privacy", "pii", "redaction"],
        "route": ["routing", "optimization", "llm"],
        "llm": ["ai", "machine-learning", "nlp"],
        "api": ["rest", "api"],
        "reliable": ["reliability", "monitoring"],
    }

    for keyword, keyword_tags_list in keyword_tags.items():
        if keyword in title_lower or keyword in desc_lower:
            tags.extend(keyword_tags_list)

    # Dedupe and limit
    return list(dict.fromkeys(tags))[:10]


def _suggest_category(api_info: dict) -> str:
    """Suggest RapidAPI category."""
    title_lower = api_info.get("title", "").lower()
    desc_lower = api_info.get("description", "").lower()

    category_keywords = {
        "Data": ["data", "privacy", "pii", "mask", "redact"],
        "AI/ML": ["ai", "ml", "machine learning", "llm", "nlp"],
        "Tools": ["tool", "utility", "helper"],
        "DevOps": ["devops", "monitoring", "reliability", "api"],
    }

    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in title_lower or keyword in desc_lower:
                return category

    return "Other"


def save_listing(listing: dict, output_dir: Path) -> list[Path]:
    """Save listing files to output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    created_files = []

    # listing.md - main description
    listing_md = output_dir / "listing.md"
    listing_md.write_text(listing["description"])
    created_files.append(listing_md)

    # endpoints.md - endpoint documentation
    endpoints_md = output_dir / "endpoints.md"
    endpoints_content = ["# API Endpoints\n"]
    for ep in listing["endpoints"]:
        endpoints_content.append(f"## {ep['method']} {ep['path']}")
        endpoints_content.append(f"{ep['summary']}\n")
        if ep.get("description"):
            endpoints_content.append(ep["description"])
        endpoints_content.append("")
    endpoints_md.write_text("\n".join(endpoints_content))
    created_files.append(endpoints_md)

    # pricing.json
    pricing_json = output_dir / "pricing.json"
    pricing_json.write_text(json.dumps(listing["pricing"], indent=2))
    created_files.append(pricing_json)

    # tags.json
    tags_json = output_dir / "tags.json"
    tags_json.write_text(json.dumps({
        "tags": listing["tags"],
        "category": listing["category"],
    }, indent=2))
    created_files.append(tags_json)

    # metadata.json - full listing data
    metadata_json = output_dir / "metadata.json"
    metadata_json.write_text(json.dumps(listing, indent=2, default=str))
    created_files.append(metadata_json)

    return created_files
