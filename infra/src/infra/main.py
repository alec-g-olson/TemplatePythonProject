"""An AWS Python Pulumi program.

Attributes:
    | bucket: An AWS bucket.
"""

from pulumi_aws import s3

# Create an AWS resource (S3 Bucket)
bucket = s3.Bucket("my-bucket")
