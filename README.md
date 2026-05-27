# 💪 FitStack

**AI-powered fitness programming platform** — personalized, science-backed workout generation with progressive overload tracking.

🌐 **Live:** [rajatjoshi.fit](https://rajatjoshi.fit)

---

## What is FitStack?

FitStack uses AI and exercise science principles to generate periodized training programs tailored to your goals, experience level, injuries, and available equipment. Not a generic workout randomizer — a system that understands programming logic: linear progression for beginners, undulating periodization for intermediates, and block periodization for advanced lifters.

### Key Features (Planned)
- 🏋️ Conversational workout generation powered by RAG over an exercise science knowledge base
- 📈 Progressive overload tracking with automatic load/volume adjustments
- 🔄 Periodization engine (linear, undulating, block) based on training age
- 🤕 Exercise substitution logic for injuries and equipment constraints
- 👨‍🏫 Coach mode — review and override AI-generated programs for your clients

---

## Architecture

```
User → rajatjoshi.fit (Cloudflare CDN)
        → React + Tailwind (Azure Static Web Apps)
            → FastAPI backend (Azure App Service / AKS)
                → Azure OpenAI GPT-4o mini (workout generation)
                → Azure AI Search (exercise knowledge RAG)
                → PostgreSQL (user profiles, workout logs)

CI/CD: GitHub Actions → Docker → Azure Container Registry → Deploy
IaC:   Terraform (all Azure resources)
Auth:  Entra ID B2C (email + Google sign-in)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Tailwind CSS |
| Backend | Python, FastAPI |
| AI | Azure OpenAI (GPT-4o mini), Azure AI Search (vector store) |
| Database | Azure PostgreSQL Flexible Server |
| Auth | Entra ID B2C (email + social login) |
| Containerization | Docker, Azure Container Registry |
| Hosting | Azure App Service → AKS (planned) |
| IaC | Terraform |
| CI/CD | GitHub Actions (lint → test → scan → deploy) |
| CDN & DNS | Cloudflare |
| Monitoring | Azure Application Insights |

---

## Getting Started

### Prerequisites
- Python 3.12+
- Docker
- Node.js 20+ (for frontend)
- Azure CLI
- Terraform

### Local Development

```bash
# Clone the repo
git clone https://github.com/therajatjoshi/fitstack.git
cd fitstack

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Docker (alternative)
docker-compose up --build
```

API docs available at `http://localhost:8000/docs`

---

## Project Roadmap

- [x] Project scaffolding and repo setup
- [ ] FastAPI backend with health and workout endpoints
- [ ] Docker containerization
- [ ] GitHub Actions CI/CD pipeline
- [ ] Terraform for Azure infrastructure
- [ ] Azure deployment (App Service)
- [ ] PostgreSQL integration (user profiles, workout logs)
- [ ] Azure OpenAI + RAG pipeline (exercise knowledge base)
- [ ] React frontend
- [ ] Entra ID B2C authentication
- [ ] Progressive overload tracking engine
- [ ] Periodization logic (linear → undulating → block)
- [ ] Coach mode (multi-tenant)
- [ ] Custom domain: rajatjoshi.fit

---

## Why I Built This

I've spent years training bodybuilders and coaching fitness competitors. Most fitness apps generate random workouts — they don't understand periodization, progressive overload, or how to program around injuries. FitStack combines my exercise science background with my platform engineering experience to build what I always wished existed: an AI coach that actually understands programming principles.

This project also serves as a full-stack engineering portfolio — every layer from frontend to infrastructure-as-code is built and deployed by me.

---

## License

[MIT](LICENSE)

---

*Built by [Rajat Joshi](https://linkedin.com/in/therajatjoshi) — Senior Engineering Manager, fitness enthusiast, and platform engineering leader.*
