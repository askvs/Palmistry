# AWS production (default)

Target: ECR -> ECS Fargate + RDS Postgres 16 + ALB. Azure remains
replaceable: any registry/DB/blob can substitute via the same env vars.

1. Provision: ECR repos ($ECR_BACKEND_REPO, $ECR_FRONTEND_REPO),
   RDS Postgres 16 (1 db `palmistry`), ALB with target-group health
   check `GET /health` (healthy threshold 2, interval 30s).
2. Secrets: store SECRET_KEY, DATABASE_URL (= RDS_DATABASE_URL),
   GOOGLE_CLIENT_ID/SECRET, OPENAI/GROQ keys in AWS Secrets Manager;
   inject as container env. Never bake into images.
3. Push: `deploy.yml` pushes :$GITHUB_SHA tags on main.
4. Run: ECS service backend (2 tasks, 0.5 vCPU/1GB, env DEBUG=false,
   REFRESH_COOKIE_SECURE=true, CORS_ORIGINS=["https://<app-domain>"]),
   frontend (1 task, NEXT_PUBLIC_API_BASE_URL=https://<api-domain>
   baked at build time). Migrate: run `alembic upgrade head` as a
   one-off ECS task before switching traffic.
5. Uploads: default stays the `uploads` EFS/EBS volume. S3 is opt-in:
   set S3_UPLOADS_BUCKET and point the avatar service at it (adapter
   to be added with that milestone); empty keeps local disk.
6. Rollback: re-point ECS service to the previous :SHA tag.
