# AWS Deployment Guide

## Required AWS Services

- Amazon ECS or EKS for the FastAPI container.
- Amazon RDS PostgreSQL for `resume_analyses`.
- Amazon S3 for original resume storage.
- Amazon Bedrock with Claude Sonnet model access enabled.
- Amazon OpenSearch Service for resume indexing.
- AWS Secrets Manager for JWT secret, database URL, and service credentials.
- Application Load Balancer or API Gateway in front of the service.

## Environment Variables

- `JWT_SECRET`
- `DATABASE_URL`
- `AWS_REGION`
- `S3_BUCKET`
- `BEDROCK_MODEL_ID`
- `ENABLE_LLM=true`
- `ENABLE_S3_UPLOAD=true`
- `ENABLE_OPENSEARCH_INDEXING=true`
- `OPENSEARCH_HOST`

## IAM Policy Scope

Grant the task role:

- `bedrock:InvokeModel` for the configured Claude Sonnet model.
- `s3:PutObject` for `arn:aws:s3:::<bucket>/resumes/*`.
- OpenSearch HTTP permissions for index and document write operations.
- Secrets Manager read access for the service secrets.

## Deployment Steps

1. Build and push the Docker image to ECR.
2. Apply `app/db/schema.sql` to the RDS database.
3. Create the S3 bucket and OpenSearch index.
4. Configure ECS/EKS environment variables from Secrets Manager.
5. Set `RESUME_SERVICE_URL=http://<resume-service>:5008` in the API gateway.
6. Add health checks on `/health`.
7. Verify upload through `POST /api/resume/upload` with a valid MedicoJobs JWT.
