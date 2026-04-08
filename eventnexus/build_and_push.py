import logging
import os
import re
import subprocess
from urllib.parse import quote, urlparse, urlunparse


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s %(levelname)s, %(message)s",
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "eventnexus-frontend")
ADC_PATH = os.path.join(SCRIPT_DIR, "adc.json")
REGISTRY = "us-central1-docker.pkg.dev/dw-onfly-dev/hackaton-events"
BACKEND_IMAGE = f"{REGISTRY}/fullstack:latest"
FRONTEND_IMAGE = f"{REGISTRY}/frontend:latest"
REGION = "us-central1"
SERVICE_YAML = os.path.join(SCRIPT_DIR, "service.yaml")


def _url_encode_password(db_url: str) -> str:
    """URL-encode the password in a PostgreSQL connection string.

    Uses regex because urlparse chokes on special chars like / in passwords.
    Pattern: scheme://user:password@host:port/dbname?params
    """
    match = re.match(
        r'^(?P<scheme>[^:]+)://(?P<user>[^:]+):(?P<password>.+)@(?P<rest>.+)$',
        db_url,
    )
    if not match:
        return db_url
    encoded_pw = quote(match.group("password"), safe="")
    return f"{match.group('scheme')}://{match.group('user')}:{encoded_pw}@{match.group('rest')}"


def _read_env() -> dict[str, str]:
    """Read .env file and return key-value pairs with encoded DB URLs."""
    env_path = os.path.join(SCRIPT_DIR, ".env")
    env_vars = {}
    if not os.path.exists(env_path):
        return env_vars

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            env_vars[key] = value

    # URL-encode passwords in database URLs
    for key in ("DATABASE_URL", "DIRECT_URL"):
        if key in env_vars:
            env_vars[key] = _url_encode_password(env_vars[key])

    return env_vars


def authenticate() -> None:
    logging.info("Authenticating...")
    subprocess.run(
        ["gcloud", "auth", "activate-service-account", "--key-file", ADC_PATH],
        check=True,
    )
    subprocess.run(
        ["gcloud", "auth", "configure-docker", "us-central1-docker.pkg.dev", "--quiet"],
        check=True,
    )


def build_and_push() -> None:
    logging.info("Building backend...")
    subprocess.run(
        ["docker", "build", "--no-cache", "-t", BACKEND_IMAGE, "."],
        cwd=SCRIPT_DIR, check=True,
    )
    logging.info("Pushing backend...")
    subprocess.run(["docker", "push", BACKEND_IMAGE], check=True)

    logging.info("Building frontend...")
    subprocess.run(
        ["docker", "build", "--no-cache", "--build-arg", "VITE_API_URL=",
         "-t", FRONTEND_IMAGE, "."],
        cwd=FRONTEND_DIR, check=True,
    )
    logging.info("Pushing frontend...")
    subprocess.run(["docker", "push", FRONTEND_IMAGE], check=True)

    logging.info("Build and push completed!")


def deploy() -> None:
    env_vars = _read_env()

    # Build env section for the backend container in service.yaml
    import yaml

    with open(SERVICE_YAML) as f:
        svc = yaml.safe_load(f)

    containers = svc["spec"]["template"]["spec"]["containers"]
    for container in containers:
        if "fullstack" in container.get("image", ""):
            container["env"] = [
                {"name": k, "value": v} for k, v in env_vars.items()
            ]
            break

    with open(SERVICE_YAML, "w") as f:
        yaml.dump(svc, f, default_flow_style=False, allow_unicode=True)

    logging.info("Updated service.yaml with env vars from .env")

    # Switch to user account for deploy
    logging.info("Switching to user account for deploy...")
    subprocess.run(
        ["gcloud", "config", "set", "account", "manuel.ventura@onfly.com.br"],
        check=True,
    )

    logging.info("Deploying to Cloud Run...")
    subprocess.run(
        ["gcloud", "run", "services", "replace", SERVICE_YAML, "--region", REGION],
        check=True,
    )

    logging.info("Deploy completed!")


if __name__ == "__main__":
    authenticate()
    build_and_push()
    deploy()
