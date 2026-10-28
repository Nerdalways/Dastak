 Project Dastak (दस्तक)

> **"Shor band, sewa shuru"** • CPCB 55 dB Compliant Silent Neighborhood Transit & Civic Hyperlocal Infrastructure Platform

Project Dastak is a unified single-domain civic technology platform designed to bridge street vendors (*pheriwalas*), skilled micro-artisans, gated residential communities (RWAs), and city administration. By replacing acoustic friction (shouting and loudspeakers) with digital spatial awareness, zero-commission direct economic empowerment, and cryptographic gate passes, Dastak enables seamless, zero-noise neighborhood commerce.

🌐 **Live Deployment**: [https://dastak.fly.dev](https://dastak.fly.dev)

---

## 🌟 Key Architecture & Portals

Dastak operates under a **Unified Single-Domain Routing System** (`FastAPI` ASGI Core) serving tailored progressive interfaces for each stakeholder:

* 🏠 **Resident PWA (`/`)**: Real-time product search bar, doorstep cart arrival feed, interactive Leaflet.js stall route distance tracker, and 1-tap technician booking with smartphone verification QRs.
* 🛒 **Vendor Partner Portal (`/partner`)**: Multi-category vendor onboarding (Fresh Produce, Street Food, Apparel, Kabadi/Scrap), 1-tap trade presets, and time-windowed shift entry pass generation.
* 🛠️ **Technician Console (`/technician`)**: Skilled gig worker availability broadcaster backed by mandatory Skill India / e-Shram DPI credential verification.
* 🛡️ **RWA Guard Terminal (`/guard`)**: Camera-based QR code scanner (`html5-qrcode`) for 1-second cryptographic gate clearance, manual token verification, and pre-cleared roster management.

---

## 🚀 Core Features & Technical Stack

### 🛠️ Tech Stack
* **Backend**: FastAPI, `msgspec` (sub-millisecond JSON parsing), SQLAlchemy, HMAC-SHA256 Cryptography.
* **Spatial & Cache**: Uber H3 Res-9 spatial discretization, Redis L1 transition cache.
* **Frontend**: HTML5, Tailwind CSS, Leaflet.js (OpenStreetMap), Web Audio API (soft chime earcons).
* **Security & DPI**: DigiLocker / e-Shram UAN / Skill India verification sandboxes.
* **DevOps**: Docker, Docker Compose, Fly.io Cloud Platform.

---

## 📦 Docker Containerization & Local Development

### Prerequisites
* [Docker Desktop](https://www.docker.com/) installed and running.
* Python 3.11+ (for non-containerized local execution).

### Running with Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone [https://github.com/nerdalways/Dastak.git](https://github.com/nerdalways/Dastak.git)
   cd Dastak
