import logging
import os
import subprocess


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
