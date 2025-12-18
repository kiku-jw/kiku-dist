"""RapidAPI target for publishing APIs to RapidAPI Hub."""

from pathlib import Path
from typing import Any
import json

from kiku_dist.targets.base import Issue, IssueLevel, Step, Target, TargetResult
from kiku_dist.openapi import load_openapi, validate_openapi, extract_api_info


class RapidAPITarget(Target):
    """Prepare and publish API to RapidAPI Hub."""
    
    name = "rapidapi"
    aliases = ["rapid"]
    description = "Publish API to RapidAPI Hub marketplace"
    required_secrets = ["RAPIDAPI_KEY"]
    required_tools = []
    supports_dry_run = True
    
    def doctor(self, config: dict[str, Any]) -> list[Issue]:
        """Check prerequisites for RapidAPI publish."""
        import os
        
        issues = []
        
        # Check RapidAPI key
        if not os.environ.get("RAPIDAPI_KEY"):
            issues.append(Issue(
                level=IssueLevel.WARNING,
                message="RAPIDAPI_KEY not set",
                fix_hint="Get API key from https://rapidapi.com/developer/dashboard",
            ))
        
        # Check OpenAPI spec
        openapi_path = config.get("docs", {}).get("openapi_path", "openapi.yaml")
        if not Path(openapi_path).exists():
            # Try common locations
            found = False
            for candidate in ["openapi.yaml", "openapi.yml", "openapi.json"]:
                if Path(candidate).exists():
                    found = True
                    break
            
            if not found:
                issues.append(Issue(
                    level=IssueLevel.ERROR,
                    message="OpenAPI spec not found",
                    fix_hint=f"Create {openapi_path} or export from FastAPI",
                ))
        
        # Check RapidAPI config
        rapid_config = config.get("rapidapi", {})
        if not rapid_config.get("category"):
            issues.append(Issue(
                level=IssueLevel.WARNING,
                message="RapidAPI category not set",
                fix_hint="Add [rapidapi] category = '...' to kiku-dist.toml",
            ))
        
        return issues
    
    def plan(self, config: dict[str, Any]) -> list[Step]:
        """Generate RapidAPI publish steps."""
        name = config.get("name", "Unknown API")
        
        steps = [
            Step(
                name="Validate OpenAPI spec",
                description="Check spec is valid and complete",
                command=None,
            ),
            Step(
                name="Generate listing content",
                description="Create description, tags, pricing",
                command=f"kiku-dist prepare listing . --output dist/rapidapi",
            ),
            Step(
                name="Prepare RapidAPI Hub upload",
                description=f"Format {name} for RapidAPI Hub",
                command=None,
            ),
            Step(
                name="Submit to RapidAPI",
                description="Upload via RapidAPI Provider Dashboard",
                command=None,
                dry_run_safe=False,
            ),
        ]
        
        return steps
    
    def execute(self, config: dict[str, Any], dry_run: bool = False) -> TargetResult:
        """Prepare RapidAPI listing package."""
        import os
        from kiku_dist.prepare_listing import generate_listing, save_listing
        
        name = config.get("name", "Unknown API")
        output_dir = Path("dist/rapidapi")
        
        # Find OpenAPI spec
        openapi_path = None
        for candidate in [
            config.get("docs", {}).get("openapi_path"),
            "openapi.yaml",
            "openapi.yml", 
            "openapi.json",
        ]:
            if candidate and Path(candidate).exists():
                openapi_path = Path(candidate)
                break
        
        if not openapi_path:
            return TargetResult(
                success=False,
                message="OpenAPI spec not found",
            )
        
        # Find README
        readme_path = None
        for candidate in ["README.md", "readme.md"]:
            if Path(candidate).exists():
                readme_path = Path(candidate)
                break
        
        try:
            # Generate listing
            listing = generate_listing(openapi_path, readme_path, config)
            
            if dry_run:
                return TargetResult(
                    success=True,
                    message=f"Would generate RapidAPI listing for {name}",
                    artifacts=[
                        f"Endpoints: {len(listing['endpoints'])}",
                        f"Category: {listing['category']}",
                        f"Tags: {', '.join(listing['tags'][:5])}",
                    ],
                )
            
            # Save listing files
            files = save_listing(listing, output_dir)
            
            # Create RapidAPI-specific checklist
            checklist = self._generate_rapidapi_checklist(config, listing, output_dir)
            checklist_path = output_dir / "RAPIDAPI_CHECKLIST.md"
            checklist_path.write_text(checklist)
            files.append(checklist_path)
            
            return TargetResult(
                success=True,
                message=f"RapidAPI listing ready: {output_dir}",
                artifacts=[str(f) for f in files],
                metadata=listing,
            )
            
        except Exception as e:
            return TargetResult(
                success=False,
                message=f"Error generating listing: {e}",
            )
    
    def _generate_rapidapi_checklist(
        self, 
        config: dict[str, Any], 
        listing: dict[str, Any],
        output_dir: Path,
    ) -> str:
        """Generate RapidAPI-specific upload checklist."""
        name = listing.get("name", "API")
        
        return f"""# RapidAPI Publication Checklist - {name}

## Pre-Upload Verification
- [ ] OpenAPI spec validated
- [ ] All endpoints documented
- [ ] Error responses documented
- [ ] Rate limits configured

## Files Ready
- [x] `listing.md` - API description
- [x] `endpoints.md` - Endpoint documentation
- [x] `pricing.json` - Pricing tiers
- [x] `tags.json` - Categories and tags
- [x] `metadata.json` - Full listing data

## RapidAPI Provider Dashboard Steps

### 1. Create New API
1. Go to https://rapidapi.com/provider
2. Click "My APIs" → "Add New API"
3. Choose "Import from OpenAPI/Swagger"
4. Upload: `{config.get("docs", {}).get("openapi_path", "openapi.yaml")}`

### 2. Configure Listing
1. **Name**: {name}
2. **Tagline**: {listing.get("tagline", "")}
3. **Category**: {listing.get("category", "Other")}
4. **Tags**: {", ".join(listing.get("tags", [])[:5])}
5. Copy description from: `{output_dir}/listing.md`

### 3. Configure Pricing
```json
{json.dumps(listing.get("pricing", {}), indent=2)}
```

### 4. Configure MCP (Model Context Protocol)
- RapidAPI now supports MCP automatically
- Each endpoint becomes an MCP tool
- Consumers can use via mcp.rapidapi.com

### 5. Submit for Review
- [ ] All fields complete
- [ ] Pricing configured
- [ ] Test endpoint works
- [ ] Submit!

## Post-Publication
- [ ] Verify API accessible
- [ ] Test via RapidAPI playground
- [ ] Monitor analytics
- [ ] Respond to user questions
"""
