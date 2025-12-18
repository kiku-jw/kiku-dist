"""CI runner - trigger workflows on different CI backends."""

import os
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class CITriggerResult:
    """Result of CI trigger."""
    success: bool
    message: str
    run_url: str | None = None


def trigger_github_actions(
    repo: str,
    workflow: str,
    ref: str,
    inputs: dict[str, str] | None = None,
) -> CITriggerResult:
    """Trigger GitHub Actions workflow using gh CLI."""
    cmd = [
        "gh", "workflow", "run", f"{workflow}.yml",
        "--repo", repo,
        "--ref", ref,
    ]
    
    if inputs:
        for key, value in inputs.items():
            cmd.extend(["-f", f"{key}={value}"])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return CITriggerResult(
                success=True,
                message=f"Triggered {workflow} on {repo}",
                run_url=f"https://github.com/{repo}/actions",
            )
        else:
            return CITriggerResult(
                success=False,
                message=f"Failed: {result.stderr}",
            )
    except Exception as e:
        return CITriggerResult(
            success=False,
            message=f"Error: {e}",
        )


def trigger_gitlab_ci(
    project: str,
    ref: str,
    variables: dict[str, str] | None = None,
    gitlab_url: str = "https://gitlab.com",
) -> CITriggerResult:
    """Trigger GitLab CI pipeline via API.
    
    Requires GITLAB_TOKEN environment variable.
    """
    token = os.environ.get("GITLAB_TOKEN")
    if not token:
        return CITriggerResult(
            success=False,
            message="GITLAB_TOKEN not set. Set it with api scope.",
        )
    
    try:
        import httpx
        import urllib.parse
        
        project_encoded = urllib.parse.quote(project, safe="")
        url = f"{gitlab_url}/api/v4/projects/{project_encoded}/trigger/pipeline"
        
        data = {"ref": ref}
        if variables:
            for key, value in variables.items():
                data[f"variables[{key}]"] = value
        
        resp = httpx.post(
            url,
            headers={"PRIVATE-TOKEN": token},
            data=data,
            timeout=30,
        )
        
        if resp.status_code in (200, 201):
            pipeline = resp.json()
            return CITriggerResult(
                success=True,
                message=f"Triggered pipeline #{pipeline.get('id', '?')}",
                run_url=pipeline.get("web_url"),
            )
        else:
            return CITriggerResult(
                success=False,
                message=f"API error {resp.status_code}: {resp.text}",
            )
    except Exception as e:
        return CITriggerResult(
            success=False,
            message=f"Error: {e}",
        )


def trigger_drone_ci(
    repo: str,
    branch: str = "main",
    drone_server: str | None = None,
) -> CITriggerResult:
    """Trigger Drone CI build.
    
    Requires DRONE_TOKEN and optionally DRONE_SERVER environment variables.
    Uses drone CLI if available, otherwise API.
    """
    import shutil
    
    # Try drone CLI first
    if shutil.which("drone"):
        cmd = ["drone", "build", "create", repo]
        if branch:
            cmd.extend(["--branch", branch])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return CITriggerResult(
                    success=True,
                    message=f"Triggered build on {repo}",
                )
            else:
                return CITriggerResult(
                    success=False,
                    message=f"drone CLI failed: {result.stderr}",
                )
        except Exception as e:
            return CITriggerResult(
                success=False,
                message=f"Error: {e}",
            )
    
    # Fallback to API
    token = os.environ.get("DRONE_TOKEN")
    server = drone_server or os.environ.get("DRONE_SERVER")
    
    if not token or not server:
        return CITriggerResult(
            success=False,
            message="DRONE_TOKEN and DRONE_SERVER required. Or install drone CLI.",
        )
    
    try:
        import httpx
        
        url = f"{server}/api/repos/{repo}/builds"
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params={"branch": branch},
            timeout=30,
        )
        
        if resp.status_code in (200, 201):
            build = resp.json()
            return CITriggerResult(
                success=True,
                message=f"Triggered build #{build.get('number', '?')}",
                run_url=f"{server}/{repo}/{build.get('number', '')}",
            )
        else:
            return CITriggerResult(
                success=False,
                message=f"API error {resp.status_code}: {resp.text}",
            )
    except Exception as e:
        return CITriggerResult(
            success=False,
            message=f"Error: {e}",
        )


def trigger_jenkins(
    job_url: str,
    parameters: dict[str, str] | None = None,
) -> CITriggerResult:
    """Trigger Jenkins job.
    
    Requires JENKINS_USER and JENKINS_TOKEN environment variables.
    """
    user = os.environ.get("JENKINS_USER")
    token = os.environ.get("JENKINS_TOKEN")
    
    if not user or not token:
        return CITriggerResult(
            success=False,
            message="JENKINS_USER and JENKINS_TOKEN required.",
        )
    
    try:
        import httpx
        
        # Determine URL - with or without parameters
        if parameters:
            url = f"{job_url}/buildWithParameters"
            resp = httpx.post(
                url,
                auth=(user, token),
                params=parameters,
                timeout=30,
            )
        else:
            url = f"{job_url}/build"
            resp = httpx.post(
                url,
                auth=(user, token),
                timeout=30,
            )
        
        if resp.status_code in (200, 201, 302):
            return CITriggerResult(
                success=True,
                message="Triggered Jenkins job",
                run_url=job_url,
            )
        else:
            return CITriggerResult(
                success=False,
                message=f"API error {resp.status_code}: {resp.text}",
            )
    except Exception as e:
        return CITriggerResult(
            success=False,
            message=f"Error: {e}",
        )


def get_ci_trigger_help(backend: str) -> str:
    """Get setup instructions for CI backend trigger."""
    help_text = {
        "gha": """GitHub Actions:
  1. Install gh CLI: brew install gh
  2. Authenticate: gh auth login
  3. Ensure workflow has workflow_dispatch trigger
  
  Trigger: kiku-dist ci run --backend gha --workflow release""",
        
        "gitlab": """GitLab CI:
  1. Create token: Settings > Access Tokens > Add (api scope)
  2. Set: export GITLAB_TOKEN=<token>
  3. Ensure pipeline trigger is enabled
  
  Trigger: kiku-dist ci run --backend gitlab""",
        
        "drone": """Drone CI:
  Option A - CLI:
    1. Install: brew install drone-cli
    2. Configure: export DRONE_SERVER=https://drone.example.com
    3. Authenticate: export DRONE_TOKEN=<token>
    
  Option B - API only:
    1. Get token from Drone UI
    2. Set DRONE_SERVER and DRONE_TOKEN
  
  Trigger: kiku-dist ci run --backend drone""",
        
        "jenkins": """Jenkins:
  1. Create API token: User > Configure > API Token > Add
  2. Set: export JENKINS_USER=<username>
  3. Set: export JENKINS_TOKEN=<token>
  4. Note your job URL (e.g. https://jenkins.example.com/job/my-project)
  
  Trigger: kiku-dist ci run --backend jenkins --job-url <url>""",
    }
    return help_text.get(backend, f"Unknown backend: {backend}")
