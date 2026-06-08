# Quillin Hub: Deployment & Integration Guide

This document outlines the deployment strategy and GitHub integration for the Quillin Hub, transitioning it from a local prototype to a production-ready service.

## 🏗️ Architecture Overview

The Quillin Hub utilizes a **Hybrid Architecture** to ensure high performance, accessibility, and security.

- **Main QUILL Repository (Repo A)**: The source of truth for all plugin code and manifests (`examples/quillins/`).
- **Quillin Hub Repository (Repo B)**: Contains the Flask backend, Docker orchestration, and the static site generator.
- **GitHub Pages**: Hosts the static "Showcase" layer as a branch of Repo B.

---

## 🛠️ Deployment Steps

### 1. Infrastructure Setup
The Hub is deployed as a Dockerized service.

**Prerequisites**: A Linux VPS with Docker and Docker Compose installed.

1. **Clone the Hub Repository** to the server.
2. **Configure Environment**: Create a `.env` file in the root:
   ```env
   SECRET_KEY=your-secure-random-string
   DATABASE_URL=postgresql://user:pass@db:5432/quillin_hub
   GITHUB_TOKEN=your-github-personal-access-token
   ```
3. **Launch**:
   ```bash
   docker-compose up -d --build
   ```
4. **Initialize Database**:
   ```bash
   docker-compose exec hub-app python -m flask db upgrade
   ```

### 2. Wiring in GitHub (Integration)
The Hub is **GitHub-Native**. It does not store plugins; it projects the state of the main repository.

**Integration Flow**:
1. **Authentication**: The Hub uses a GitHub Personal Access Token (PAT) with `repo` scope to communicate with the API.
2. **The Sync Loop**:
   - The `worker/sync_to_pages.py` script scans the `examples/quillins/` directory in the main QUILL repo.
   - It extracts `manifest.json` files and updates the Hub's PostgreSQL registry.
   - It generates the `gallery.json` and static assets for the storefront.
3. **Static Publishing**: The sync worker commits the generated storefront to the `gh-pages` branch of the Hub Repo.

### 3. GitHub Pages Configuration
1. Navigate to **Settings $\rightarrow$ Pages** in the Hub repository.
2. Set the source branch to `gh-pages`.
3. The static storefront will now be live at the provided GitHub Pages URL.

---

## 🛡️ The Approval & Update Pipeline

To maintain a "Gold Standard" ecosystem, the Hub follows a strict GitHub-first governance model.

### The Lifecycle of a Plugin
$$\text{Pull Request} \rightarrow \text{CI (Lint + Security)} \rightarrow \text{Maintainer Review} \rightarrow \text{Merge to Main} \rightarrow \text{Hub Sync} \rightarrow \text{Live}$$

### Versioning & Protection
- **Patch/Minor Updates**: If no la lcapabilities change, updates are **Fast-Tracked** (Automatic approval upon passing CI).
- **Major/Capability Changes**: Any change to `capabilities` or a Major version bump triggers a **Full Audit** by a maintainer.
- **Ownership Protection**: The system uses **Git Commit Authority**. Only the original author (or an approved maintainer) can commit changes to a plugin's directory, preventing hijacking.

---

## 📡 Client Integration (QUILL $\rightarrow$ Hub)

The QUILL desktop app integrates with the Hub via the **Registry API**:

1. **Discovery**: The app calls `GET /api/v1/plugins` to fetch the list of verified Quillins.
2. **Installation**: The app uses the `download_url` provided by the API to fetch the plugin bundle directly from GitHub.
3. **Updates**: The app periodically checks the latest version via `/api/v1/plugins/<id>/latest` and prompts the user to update.
4. **Safety**: If an update is unstable, the app utilizes the **Safety Vault** (Registry history) to roll back to the previous stable version.
