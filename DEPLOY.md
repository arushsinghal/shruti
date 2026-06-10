# Deployment Guide (Fastest & Easiest Way)

This guide walks you through deploying the entire application (React + FastAPI + SQLite) on **Render** using our unified, single-container setup. This approach guarantees zero-downtime rolling deployments and fully persisted database storage.

---

## 🚀 Steps to Deploy on Render

### 1. Push Code to GitHub
Ensure all changes are committed and pushed to a repository on your GitHub account.

### 2. Create a Web Service on Render
1. Log in to [Render](https://dashboard.render.com/).
2. Click **New +** and select **Web Service**.
3. Connect your GitHub repository.

### 3. Configure Service Settings
Specify the following settings in the Render creation form:
*   **Name:** `clinical-decision-support` (or any name you prefer)
*   **Region:** Select the region closest to you
*   **Branch:** `main` (or your primary branch)
*   **Runtime:** **Docker** (Render will automatically detect the root `Dockerfile` and build it)
*   **Instance Type:** Free or Starter

### 4. Configure Environment Variables
Scroll down to the **Environment** section and add the following environment variables:

| Key | Value | Description |
|---|---|---|
| `GEMINI_API_KEY` | `your_actual_unthrottled_gemini_key` | Enables cloud-based LLM NLP capabilities. |
| `SARVAM_API_KEY` | `your_actual_sarvam_asr_key` | Enables voice-to-text dictation. |
| `SQLITE_DB` | `/app/data/sessions.db` | Redirects SQLite to write to the persistent disk volume. |
| `ASR_MODE` | `cloud` | Configures Sarvam cloud-based ASR. |

### 5. Attach a Persistent Disk (Crucial for SQLite)
Since SQLite stores everything in a local file (`sessions.db`), you **must** mount a persistent disk so that patient consultation data is not deleted whenever the container is updated or restarted.

1. Go to your web service's **Disk** tab (or scroll to Disks during creation).
2. Click **Add Disk** / **Add Volume**.
3. Configure the disk settings:
    *   **Name:** `sqlite-data`
    *   **Mount Path:** `/app/data`
    *   **Size:** `1 GB` (This is more than enough for millions of text records, costing ~$1/month)

---

## 🛠️ How it Works under the Hood

*   **Multi-Stage Build:** The root `Dockerfile` compiles your React typescript code using a Node environment, then automatically copies the static bundle (`dist`) into a Python runtime containing the FastAPI app.
*   **SPA Client Routing:** When the browser requests `/dashboard` or `/sessions/xyz`, FastAPI's catch-all fallback serves the static `index.html` file, letting React Router handle the view on the client side.
*   **Zero-Downtime:** When you push updates to GitHub, Render automatically builds a new Docker image, tests it, confirms it is running and healthy by calling the `/health` endpoint, and only then switches traffic over from the old container.
