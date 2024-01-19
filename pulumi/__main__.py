"""An AWS Python Pulumi program."""

from pulumi_aws import s3

import pulumi

# Create an AWS resource (S3 Bucket)
bucket = s3.Bucket("my-bucket")

# Export the name of the bucket
pulumi.export("bucket_name", bucket.id)
