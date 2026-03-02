## Running with Docker

### Build the image

From the project root:

```bash
docker build -t get-insight-backend .
```

### Run the container

Set the required environment variables (replace the placeholder values):

```bash
docker run --rm -p 8000:8000 \
  -e GOOGLE_API_KEY="your-google-api-key" \
  -e CHROMA_API_KEY="your-chroma-api-key" \
  -e CHROMA_TENANT="your-chroma-tenant" \
  -e CHROMA_DATABASE="your-chroma-database" \
  get-insight-backend
```

The API will be available at `http://localhost:8000`. You can open the interactive docs at `http://localhost:8000/docs`.

---

## CI/CD (Docker Hub)

A GitHub Actions workflow builds and pushes the Docker image to Docker Hub on push to `main`/`master` (and on manual run).

### Required secrets

In your repo: **Settings → Secrets and variables → Actions**, add:

| Secret               | Description                                      |
|----------------------|--------------------------------------------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username                         |
| `DOCKERHUB_TOKEN`    | Docker Hub access token (Account → Security)     |

### Workflow steps

1. **Checkout** – clone the repository  
2. **Set up Docker Buildx** – enable buildx for build cache  
3. **Log in to Docker Hub** – using the secrets above (skipped on pull requests)  
4. **Extract metadata** – generate image tags (branch, commit SHA, `latest` on default branch)  
5. **Build and push** – build the image and push to `docker.io/<DOCKERHUB_USERNAME>/get-insight` (push skipped on pull requests)

### Manual run

Trigger the workflow manually: **Actions → Build and Push Docker Image → Run workflow**.

