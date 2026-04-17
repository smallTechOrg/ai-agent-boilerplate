# CI/CD Pipeline

## Overview

Automated test → deploy pipeline via GitHub Actions. Pushes to `staging` deploy to the shared staging VM. Pushes to `main` deploy to the dedicated production VM.

## Architecture

```
Push to staging ──▶ test ──▶ SSH deploy to staging-instance (port 5000)
Push to main   ──▶ test ──▶ SSH deploy to ai-agent-prod   (port 5000)
```

## Pipeline Stages

### 1. Test (`test` job)

Runs on every push to `main` or `staging`.

- **Service container**: PostgreSQL 16 on `localhost:5432` (DB: `test_chatdb`)
- **Python**: 3.12
- **Lint**: `ruff check .` (inside `code/`)
- **Tests**: `pytest test/ -v` (inside `code/`)

### 2. Deploy Staging (`deploy-staging` job)

Triggers only on pushes to `staging`. Requires the `test` job to pass.

1. Authenticates to GCP using the service account key
2. Sets `BRANCH_NAME=staging` in VM instance metadata (used by `config.py` → `get_db_name()` to select `staging_chat_db`)
3. SSHs into the staging VM and runs:
   - `git fetch --all && git reset --hard origin/staging`
   - `scripts/deploy.sh` (activates venv, installs deps, generates `.env`, restarts Flask on port 5000)
4. Verifies `GET /health` returns 200

### 3. Deploy Production (`deploy-production` job)

Triggers only on pushes to `main`. Requires the `test` job to pass.

Same as staging but targets `ai-agent-prod` VM and sets `BRANCH_NAME=main` (selects `prod_chat_db`).

## GitHub Secrets Required

Configure these in **repo Settings → Secrets and variables → Actions**:

| Secret | Environment | Value |
|--------|-------------|-------|
| `GCP_SA_KEY` | (repo-level) | Service account JSON key with `compute.instanceAdmin.v1` role |
| `GCP_PROJECT` | (repo-level) | `ai-agent-boilerplate0` |
| `GCP_VM_INSTANCE_NAME_STAGING` | staging | `staging-instance` |
| `GCP_ZONE_STAGING` | staging | `us-central1-f` |
| `GCP_VM_INSTANCE_NAME_PROD` | production | `ai-agent-prod` |
| `GCP_ZONE_PROD` | production | VM zone for production |

## GitHub Environments

Create two environments in **repo Settings → Environments**:

- **staging** — no protection rules needed
- **production** — recommended: add required reviewers for manual approval gate before prod deploys

## VM Prerequisites

Each VM must have:

1. Repo cloned at `/home/vivek/Ai-agent-boilerplate/ai-agent-boilerplate`
2. Python 3.12 virtualenv at `venv/`
3. SSH key added to GitHub for `git fetch` to work
4. `curl` installed (for health checks)

## Deploy Script

The existing `scripts/deploy.sh` handles the on-VM deployment:

1. Activates virtualenv
2. `pip install -r requirements.txt`
3. Generates `.env` via `python3 get_env.py` (pulls secrets from GCP Secret Manager)
4. Kills any existing Flask process
5. Starts Flask on `0.0.0.0:5000` via `nohup`

## Rollback

To rollback, push the previous good commit to the target branch:

```bash
git revert HEAD && git push origin main
```

Or manually SSH into the VM and reset:

```bash
gcloud compute ssh VM_NAME --zone=ZONE --command="
  cd /home/vivek/Ai-agent-boilerplate/ai-agent-boilerplate &&
  sudo git reset --hard GOOD_COMMIT_SHA &&
  sudo ./scripts/deploy.sh
"
```
