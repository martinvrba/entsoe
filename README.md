# entsoe

This project deploys an **AWS Lambda function** that queries the [ENTSO-E Transparency Platform API](https://transparency.entsoe.eu/) on a schedule, processes XML energy data (generation and optionally consumption), converts it to CSV, and uploads it to an S3 bucket.

It uses **Terraform** to manage the AWS infrastructure, including the Lambda function, S3 bucket, IAM roles, and EventBridge triggers.

## Features

- Fetches ENTSO-E time series data using the ENTSO-E API
- Parses and filters XML for relevant time series (with `inBiddingZone_Domain` → Generation)
- Dynamically includes the `psrType` column in the CSV if present
- Stores generated CSVs in S3 under structured paths (by document type, process type, date)
- Runs on a configurable schedule using EventBridge

## Project Structure

See `main.tf`.

## Requirements

- Terraform >= 1.4.2
- ENTSO-E API access
- AWS credentials for a user that has sufficient permissions to:
  - create S3 buckets
  - create/update Lambda functions
  - manage IAM roles and policies
  - create EventBridge rules
- An S3 bucket for the Terraform backend state (as referenced in `provider.tf`) — this bucket must already exist before running `terraform init`
- An existing AWS Lambda layer that includes the `isodate` and `requests` Python libraries — this layer must be referenced in `lambda.tf`

## Setup

1. **Clone the repository**
```bash
git clone https://github.com/martinvrba/entsoe.git
cd entsoe
```

2. **Update variables**
Edit `terraform.tfvars` to set:

    **Mandatory**:
    - `security_token` — your ENTSO-E API key (this is required)

    **Optional (has defaults)** — you can override if needed:
    - `api_url`
    - `document_type`
    - `process_type`
    - `in_domain`
    - `lambda_schedule_expression`
    - `extra_params` (optional; e.g. `psrType=B01`)
    - `s3_bucket_name`

    You **must** provide the `security_token` for the Lambda to authenticate with the ENTSO-E API. The other variables can rely on their defaults or be customized in `terraform.tfvars`.

3. **Initialize Terraform**
```bash
terraform init
```

4. **Apply infrastructure**
```bash
terraform apply
```

This will:  
✅ Create an S3 bucket  
✅ Deploy the Lambda function  
✅ Set up the IAM roles/policies  
✅ Configure the EventBridge schedule

## Lambda Function Overview

The Lambda:
- Requests ENTSO-E XML data
- Parses the data into `timestamp,quantity` or `timestamp,psrType,quantity` format
- Writes a CSV to the S3 bucket under:
  ```
  s3://<bucket>/<documentType>/<processType>/<inDomain>/<year>/<month>/<day>/data.csv
  ```

## Cleanup

To remove all deployed resources:
```bash
terraform destroy
```
