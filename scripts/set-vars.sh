#!/bin/bash
AWS_AccessKey="XXXXXXXXXX"
AWS_SecretAccessKey="XXXXXXXXXX"
AWS_S3_Full="XXXXXXXXXX"
AWS_S3_Original="XXXXXXXXXX"
AWS_S3_Partial="XXXXXXXXXX"
AWS_SNS="XXXXXXXXXX"
AWS_Products_DB="XXXXXXXXXX"
AWS_Services_DB="XXXXXXXXXX"
faas-cli secret $1 aws-access-key --from-literal=$AWS_AccessKey
faas-cli secret $1 aws-secret-access-key --from-literal=$AWS_SecretAccessKey
faas-cli secret $1 aws-s3-full --from-literal=$AWS_S3_Full
faas-cli secret $1 aws-s3-original --from-literal=$AWS_S3_Original
faas-cli secret $1 aws-s3-partial --from-literal=$AWS_S3_Partial
faas-cli secret $1 aws-sns --from-literal=$AWS_SNS
faas-cli secret $1 aws-products-db --from-literal=$AWS_Products_DB
faas-cli secret $1 aws-services-db --from-literal=$AWS_Services_DB
