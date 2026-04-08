import logging
import os
import subprocess


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(name)s %(levelname)s, %(message)s",
    # filename="./pipeline_logs.log",
)

ADC_PATH = os.path.join(os.path.dirname(__file__), "adc.json")


def authenticate() -> None:
    """Activate service account and configure Docker registry auth."""
    logging.info("Authenticating with %s", ADC_PATH)
    subprocess.run(
        ["gcloud", "auth", "activate-service-account", "--key-file", ADC_PATH],
        check=True,
    )
    subprocess.run(
        ["gcloud", "auth", "configure-docker", "us-central1-docker.pkg.dev", "--quiet"],
        check=True,
    )


def run_docker_commands() -> None:
    """
    Build and push the Docker image to Artifact Registry.
    """
    image_name = "us-central1-docker.pkg.dev/dw-onfly-dev/hackaton-events/fullstack:latest"

    try:
        # Build image without cache
        logging.info("🔨 Building Docker image...")
        subprocess.run(
            ["docker", "build", "--no-cache", "-t", image_name, "."],
            check=True,
        )

        # Push image
        logging.info("🚀 Pushing Docker image to Artifact Registry...")
        subprocess.run(
            ["docker", "push", image_name],
            check=True,
        )

        logging.info("✅ Build and push completed successfully!")

    except subprocess.CalledProcessError as error:
        logging.info(f"❌ Error executing command: {error}")


def deploy_cloud_run() -> None:
    """Deploy the latest image to Cloud Run."""
    image_name = "us-central1-docker.pkg.dev/dw-onfly-dev/hackaton-events/fullstack:latest"
    service_name = "hackaton-event"
    region = "us-central1"

    env_vars = []
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    env_vars.append(line)

    cmd = [
        "gcloud", "run", "deploy", service_name,
        "--image", image_name,
        "--region", region,
        "--port", "8080",
        "--allow-unauthenticated",
    ]

    if env_vars:
        cmd += ["--set-env-vars", ",".join(env_vars)]

    # Switch to user account for deploy (SA lacks iam.serviceaccounts.actAs on dev project)
    logging.info("Switching to user account for deploy...")
    subprocess.run(
        ["gcloud", "config", "set", "account", "manuel.ventura@onfly.com.br"],
        check=True,
    )

    logging.info("Deploying to Cloud Run...")
    subprocess.run(cmd, check=True)
    logging.info("Deploy completed successfully!")


if __name__ == "__main__":
    authenticate()
    run_docker_commands()
    deploy_cloud_run()
