import boto3
import csv
import isodate
import logging
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    try:
        # Load required environment variables
        api_url = os.environ.get("API_URL")
        document_type = os.environ.get("DOCUMENT_TYPE")
        in_domain = os.environ.get("IN_DOMAIN")
        process_type = os.environ.get("PROCESS_TYPE")
        s3_bucket_name = os.environ.get("S3_BUCKET_NAME")
        security_token = os.environ.get("SECURITY_TOKEN")
        extra_params = os.environ.get("EXTRA_PARAMS")  # Optional extra parameters

        for var_name, env_var in [
            ("API_URL", api_url),
            ("DOCUMENT_TYPE", document_type),
            ("IN_DOMAIN", in_domain),
            ("PROCESS_TYPE", process_type),
            ("S3_BUCKET_NAME", s3_bucket_name),
            ("SECURITY_TOKEN", security_token),
        ]:
            if not env_var:
                logger.error(f"Environment variable {var_name} is not set")
                raise ValueError(f"Missing required environment variable: {var_name}")

        # Set period_start and period_end to cover today's date (UTC)
        now = datetime.now(timezone.utc)
        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0).strftime(
            "%Y%m%d%H%M"
        )
        period_end = (
            (now + timedelta(days=1))
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .strftime("%Y%m%d%H%M")
        )

        # Build query parameters for the API request
        params = {
            "documentType": document_type,
            "processType": process_type,
            "in_Domain": in_domain,
            "periodStart": period_start,
            "periodEnd": period_end,
            "securityToken": security_token,
        }

        if extra_params:
            for pair in extra_params.split("&"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    params[k] = v

        # Log parameters without exposing sensitive tokens
        logged_params = {
            k: ("***" if k == "securityToken" else v) for k, v in params.items()
        }
        logger.info(f"Requesting data from {api_url} with params: {logged_params}")

        # Make API request
        response = requests.get(api_url, params=params)
        response.raise_for_status()

        # Define the XML namespace used in the response
        ns = {"ns": "urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0"}

        # Parse the XML response
        root = ET.fromstring(response.text)
        logger.info("XML parsed successfully")

        # Check if any TimeSeries (with inBiddingZone) has psrType
        has_psr_type = any(
            ts.find("ns:MktPSRType/ns:psrType", ns) is not None
            for ts in root.findall(".//ns:TimeSeries", ns)
            if ts.find("ns:inBiddingZone_Domain.mRID", ns) is not None
        )

        # Prepare to write CSV output
        file_path = "/tmp/data.csv"
        with open(file_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            # Dynamically set CSV header
            if has_psr_type:
                writer.writerow(["timestamp", "psrType", "quantity"])
            else:
                writer.writerow(["timestamp", "quantity"])

            # Loop over all TimeSeries elements
            for timeseries in root.findall(".//ns:TimeSeries", ns):
                in_bidding_zone = timeseries.find("ns:inBiddingZone_Domain.mRID", ns)
                if in_bidding_zone is None:
                    # Skip if no inBiddingZone (only process TimeSeries reflecting Generation; outBiddingZone reflects Consumption)
                    continue

                # Directly extract psrType if header expects it
                if has_psr_type:
                    psr_type = timeseries.find("ns:MktPSRType/ns:psrType", ns).text

                period = timeseries.find(".//ns:Period", ns)
                if period is None:
                    logger.warning("No Period found for a TimeSeries")
                    continue

                start_str = period.find(".//ns:timeInterval/ns:start", ns).text
                resolution_str = period.find(".//ns:resolution", ns).text

                start_time = datetime.strptime(start_str, "%Y-%m-%dT%H:%MZ")
                step = isodate.parse_duration(resolution_str)

                points = period.findall(".//ns:Point", ns)
                for point in points:
                    position = int(point.find("ns:position", ns).text)
                    quantity = point.find("ns:quantity", ns).text
                    timestamp = start_time + (position - 1) * step

                    if has_psr_type:
                        writer.writerow(
                            [timestamp.isoformat() + "Z", psr_type, quantity]
                        )
                    else:
                        writer.writerow([timestamp.isoformat() + "Z", quantity])

        logger.info(f"Data written to {file_path}")

        # Upload CSV file to S3
        s3 = boto3.client("s3")
        s3_file_path = f"{document_type}/{process_type}/{in_domain}/{now.year}/{now.month:02d}/{now.day:02d}/"
        s3_file_name = "data.csv"

        s3.upload_file(file_path, s3_bucket_name, s3_file_path + s3_file_name)
        logger.info(
            f"Successfully uploaded to s3://{s3_bucket_name}/{s3_file_path}{s3_file_name}"
        )

        return {
            "statusCode": 200,
            "body": f"Successfully uploaded to s3://{s3_bucket_name}/{s3_file_path}{s3_file_name}",
        }

    except Exception as e:
        logger.error("An error occurred during processing", exc_info=True)
        return {"statusCode": 500, "body": f"Error: {str(e)}"}
