# Deployment Guide - Oracle Cloud Free Tier & Vercel

Instructions for deploying the Telecaller Call Recording, IndicConformer Transcription, and Qwen 4B Lead Extraction System.

## Architecture

- **Frontend**: React + Vite + Tailwind CSS deployed on **Vercel**.
- **Backend API & Processing**: FastAPI + FFmpeg + IndicConformer + Ollama (Qwen 4B) deployed on **Oracle Cloud Free Tier Ubuntu VM**.

---

## 1. Oracle Cloud VM Deployment

### Prerequisites
- Oracle Cloud Free Tier instance (Ubuntu 22.04 / 24.04 ARM64 Ampere or x86_64).
- Open Ports: 80 (HTTP), 443 (HTTPS), 22 (SSH) in Oracle VCN Security Rules.

### Automated Setup
1. Transfer the project files to your Oracle VM:
   ```bash
   scp -r . ubuntu@<YOUR_ORACLE_IP>:/opt/telecaller-dashboard
   ```
2. SSH into your Oracle instance:
   ```bash
   ssh ubuntu@<YOUR_ORACLE_IP>
   ```
3. Run the automated deployment script:
   ```bash
   chmod +x /opt/telecaller-dashboard/deploy/oracle-setup.sh
   sudo /opt/telecaller-dashboard/deploy/oracle-setup.sh
   ```
4. Verify backend status:
   ```bash
   curl http://localhost:8000/api/health
   ```

---

## 2. Vercel Frontend Deployment

1. Import the repository into your Vercel Dashboard.
2. Set the **Root Directory** to `frontend`.
3. Add Environment Variable:
   ```env
   VITE_API_BASE_URL=http://<YOUR_ORACLE_IP>/api
   ```
   *(or `https://api.yourdomain.com/api` if SSL is configured)*.
4. Click **Deploy**.
