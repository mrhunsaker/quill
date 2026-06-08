# PRD: The Quillin Hub (Plugin Store & Registry)

## 1. Overview
The Quillin Hub is a community-driven discovery, submission, and registry system for QUILL plugins (Quillins). It is designed to bridge the gap between a high-performance static showcase for discovery and a dynamic backend for community interaction and software distribution.

### 1.1 Goals
- **Discoverability**: Provide a fast, accessible way for users to find verified plugins.
- **Quality Control**: Automate validation via the `quillin_lint` tool and enforce the Author Covenant.
- **Trust**: Implement a verification system and community-driven ratings.
- **Interoperability**: Provide a JSON Registry API that the QUILL desktop app can use for in-app browsing and installation.

---

## 2. Architecture: The Hybrid Hub

### 2.1 The Showcase (Static Layer)
- **Hosting**: GitHub Pages.
- **Nature**: Static HTML/CSS/JS.
- **Function**: High-SEO "storefront" featuring top-rated and trending plugins.
- **Sychronization**: Periodically updated by the Engine via a sync script that commits `gallery.json` to the repository.

### 2.2 The Engine (Dynamic Layer)
- **Hosting**: Dockerized Flask application on a subdomain.
- **Database**: PostgreSQL for persistence of plugins, users, votes, and reviews.
- **Core Components**:
    - **Submission Forge**: Multi-step upload portal with real-time linting.
    - **Community Pulse**: Dynamic voting, threaded reviews, and user profiles.
    - **Registry API**: The authoritative JSON source for the QUILL client.
    - **Reviewer's Sanctum**: Admin dashboard for manual audits.

---

## 3. Functional Specifications

### 3.1 The Submission Forge
A "Guided Path" for developers:
1. **Covenant Attestation**: Digital signature of the Author Covenant and Code of Conduct.
2. **The Upload**: File upload of the Quillin bundle.
3. **The Instant Audit**: 
    - Backend triggers `python -m quill.tools.quillin_lint --strict`.
    - Pass $\rightarrow$ Proceed to metadata.
    - Fail $\rightarrow$ Display detailed error report and a "How to Fix" guide.
4. **Metadata Capture**: Fields for categorization, versioning, and "Quick Start" guides.
5. **Review State**: Submissions enter a `Pending` state until approved by a maintainer.

### 3.2 Community & Trust Features
- **Verification Badges**: 
    - `Verified`: Manually audited for A11Y and security.
    - `Community`: Lint-passed but not manually reviewed.
- **Interaction**: weighted upvoting and accessibility-specific reviews.
- **Safety Vault**: Version tracking allowing the QUILL client to perform rollbacks.

### 3.3 Magical Experiences
- **Snippet Simulator**: Web-based emulator for Layer 1 (declarative) plugins.
- **Action Replays**: Video/GIF previews for Layer 2 (Python) plugins.
- **AI Compatibility Assistant**: AI-driven guidance during submission to improve plugin A11Y.
- **Developer Hall of Fame**: Gamified profiles with `A11Y Champion` badges.

---

## 4. Technical Specification

### 4.1 Project Structure
```text
quillin-hub/
├── app/
│   ├── api/          # Registry API (JSON)
│   ├── web/          # Jinja2 Templates & Routes
│   ├── forge/        # Linter Bridge & Submission Logic
│   └── models/       # SQLAlchemy / Postgres
├── static/           # CSS/JS (Simulator)
├── worker/           # GitHub Pages sync script
├── Dockerfile        # Multi-stage (Flask + Quill Tools)
└── docker-compose.yml
```

### 4.2 API Contracts
- `GET /api/v1/plugins`: Returns a list of all verified plugins.
- `GET /api/v1/plugins/<id>/latest`: Returns the latest manifest and download URL.
- `POST /api/v1/votes`: Submits a user vote.

### 4.3 The Linter Bridge
The Docker container must include the `quill` source tree to execute `quillin_lint` against uploaded bundles in a temporary sandbox.

---

## 4. Life Cycle & Updates

### 4.1 Versioning Strategy
The Hub uses a tiered update model based on Semantic Versioning (SemVer):
- **Patch/Minor Updates (`0.0.X` or `0.X.0`)**: If no new capabilities are added, updates that pass the automated Security/Lint gate are **Fast-Tracked** (Automatically Approved).
- **Major Updates (`X.0.0`) or Capability Changes**: Bumping the major version or adding new capabilities (e.g., adding `net` to a snippet plugin) triggers a **Full Audit**, requiring manual maintainer approval.

### 4.2 The Update Loop
1. **Push**: Developer pushes a new version to the GitHub repository.
2. **CI Validation**: GitHub Actions runs the `quillin_lint` and `SecurityWatchdog` suite.
3. **Registry Sync**: The Hub's sync worker detects the change and updates the plugin's version and download URL in the Registry API.
4. **Client Notification**: The QUILL desktop app detects the version mismatch and prompts the user for an update.

### 4.3 Safety Vault (Rollbacks)
The Registry API maintains a history of `Verified` versions. If an update causes instability, the QUILL client can perform a "Magic Rollback" to the previous stable version.

---

## 5. Security & Governance

### 5.1 Ownership & Protection (The "Anti-Hijack" Guard)
To prevent unauthorized users from updating others' plugins, the system implements a strict **Proof-of-Ownership** model:
- **GitHub-Backed Identity**: Since the Hub is now GitHub-native, the **Git Commit Authority** is the primary lock. Only users with `push` access to the specific plugin directory (or those who pass a PR review) can trigger a version change.
- **Identity Mapping**: The `Plugin` model maps the `manifest_id` to the original author's GitHub ID. 
- **PR-Gated Updates**: All updates MUST occur via Pull Request. This ensures a maintainer audits the change request, preventing "shadow updates" where a malicious actor attempts to overwrite a popular plugin's logic.

### 5.2 Automated Security Gate
...existing code...
