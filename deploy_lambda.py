import os
import sys
import time

"""
Necessário Setar as credenciais para o uso do AWS-CLI 

"""

AWS_ACCOUNT = ""
AWS_REGION = "us-east-1"
DOCKER_LOCAL_TAG = ""
LAMBDA_FUNCTION_NAME = ""
LAMBDA_ROLE = ""
ECR_REPO_NAME = ""
ECR_REPO_URI = f"{AWS_ACCOUNT}.dkr.ecr.{AWS_REGION}.amazonaws.com/{ECR_REPO_NAME}"
ECR_REPO_IMAGE_TAG = "latest"


def run_command(command):
    print(f"Running command: {command}")
    # Use subprocess.Popen to capture real-time output
    # process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    process = os.system(command)

    if process != 0:
        print(f"Command failed with exit code {process}")
        return False
    print("Command succeeded")
    return True


def aws_get_token():
    print("Getting AWS Token..")
    aws_cmd = f"aws ecr get-login-password --region {AWS_REGION}"
    docker_cmd = f"docker login --username AWS --password-stdin {ECR_REPO_URI}"
    command = f"{aws_cmd} | {docker_cmd}"

    if not run_command(command):
        print("Failed to retrieve AWS Token.")
        sys.exit(1)
    print("AWS Token retrieved successfully.")


def is_ecr_repo_exists():
    print("Checking ECR repository...")
    cmd = f"aws ecr describe-repositories --repository-names {ECR_REPO_NAME} --region {AWS_REGION}"

    if not run_command(cmd):
        print("ECR repository doesn't exist. It will be created!")
        return False
    print("ECR repository found!")
    return True


def is_lambda_function_exists():
    print("Checking Lambda Function...")
    cmd = f"aws lambda get-function --function-name {LAMBDA_FUNCTION_NAME}"

    if not run_command(cmd):
        print("Lambda Function doesn't exist. It will be created!")
        return False
    print("Lambda Function found!")
    return True


def create_ecr_repo():
    print("Creating ECR Repository..")
    cmd = (
        f"aws ecr create-repository --repository-name {ECR_REPO_NAME} --region {AWS_REGION} "
        f"--image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE "
        f"--tags Key=snykorg,Value=ASX-NBJN Key=vpcx-snykorg,Value=asx-nbjn Key=vpcx-snykorg-id,Value=4e9f960a-3d1d-4487-8b07-073ef51c6bae"
    )

    if not run_command(cmd):
        print("Failed to create ECR repository.")
        sys.exit(1)
    print("ECR Repository created successfully.")


def docker_build():
    print("Building Docker Image..")
    cmd = f"docker build --platform linux/amd64 -t {DOCKER_LOCAL_TAG} ."

    if not run_command(cmd):
        print("Failed to build Docker image.")
        sys.exit(1)
    print("Docker image built successfully.")


def docker_sync_repo_image():
    print("Syncing Image Local With Remote..")
    cmd = f"docker tag {DOCKER_LOCAL_TAG} {ECR_REPO_URI}:{ECR_REPO_IMAGE_TAG}"

    if not run_command(cmd):
        print("Failed to sync Docker image.")
        sys.exit(1)
    print("Docker image synced successfully.")


def ecr_update_repo():
    print("Updating Image remote..")
    cmd = f"docker push {ECR_REPO_URI}:{ECR_REPO_IMAGE_TAG}"

    if not run_command(cmd):
        print("Failed to push Docker image to ECR.")
        sys.exit(1)
    print("Docker image pushed to ECR successfully.")


def lambda_update_function():
    print("Updating Lambda Function")
    cmd = (
        f"aws lambda update-function-code --function-name {LAMBDA_FUNCTION_NAME} "
        f"--image-uri {ECR_REPO_URI}:{ECR_REPO_IMAGE_TAG}"
    )

    if not run_command(cmd):
        print("Failed to update Lambda function.")
        sys.exit(1)
    print("Lambda function updated successfully.")


def lambda_create_function():
    print("Creating Lambda Function ..")
    cmd = (
        f"aws lambda create-function --function-name {LAMBDA_FUNCTION_NAME} "
        f"--package-type Image --code ImageUri={ECR_REPO_URI}:{ECR_REPO_IMAGE_TAG} "
        f"--role {LAMBDA_ROLE}"
    )

    if not run_command(cmd):
        print("Failed to create Lambda function.")
        sys.exit(1)
    print("Lambda function created successfully.")


def run():
    if not is_ecr_repo_exists():
        create_ecr_repo()

    aws_get_token()
    print(f"\n{'-'*100}\n")

    docker_build()
    print(f"\n{'-'*100}\n")

    docker_sync_repo_image()
    print(f"\n{'-'*100}\n")

    ecr_update_repo()
    print(f"\n{'-'*100}\n")

    if not is_lambda_function_exists():
        lambda_create_function()

    attempts = 5
    is_updated = False
    for attempt in range(attempts):
        time.sleep(30)
        print("-" * 100)
        print(f"Attempt {attempt}/5..\n")
        try:
            lambda_update_function()
            is_updated = True
        except Exception:
            continue

    if not is_updated:
        print(f"{'Please, update lambda function manually..'.center(200, "*")}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "update-lambda":
        lambda_update_function()

    else:
        run()
