# 🏦 FedCredit Score — AI Financial Intelligence Engine

> A federated credit-scoring prototype that analyzes company financial documents, enriches them with external intelligence signals, and produces a unified risk score via a simulated multi-bank federation.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

| Capability | Details |
|---|---|
| **Document Processing** | Scanned PDF (OCR), digital PDF, DOCX, XLSX |
| **Financial Extraction** | Turnover, debt ratio, profit margin, capacity utilization, audit notes |
| **External Intelligence** | News sentiment, MCA compliance, court-case risk, satellite NDVI activity |
| **Federated Scoring** | Three simulated bank models aggregated into a single 0–1000 score |
| **Risk Dashboard** | Glassmorphism UI with animated score card, Chart.js breakdown, loan recommendation |
| **PDF Report** | Branded, downloadable credit report generated with ReportLab |

---

## 🏗️ Architecture

```
User uploads docs ──► FastAPI backend
                        ├─ Document Processing (PyMuPDF / pdfplumber / OCR / python-docx / pandas)
                        ├─ Intelligence Layer  (simulated news, compliance, courts, satellite)
                        ├─ Scoring Engine      (3 bank models → federated average)
                        └─ Report Generation   (ReportLab PDF)
                      ──► Frontend dashboard (Three.js + Alpine.js + Chart.js + GSAP)
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Tesseract OCR** (optional — needed only for scanned-PDF processing)
  - Windows: [installer](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`

### Install & Run

```bash
# 1. Clone the repo
git clone https://github.com/your-org/FedCredit-Score.git
cd FedCredit-Score

# 2. Create a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
uvicorn backend.main:app --reload --port 8000

# 5. Open the app
# Navigate to http://localhost:8000
```

---

## 🎮 Demo

1. Open **http://localhost:8000**
2. Upload files from `sample_documents/` (or drag-and-drop your own)
3. Enter a GSTIN/CIN and company location
4. Click **"Analyze Company"**
5. View the **results dashboard** — credit score, risk breakdown chart, loan recommendation
6. Click **"Download Credit Report"** to get the PDF

---

## 📁 Project Structure

```
FedCredit-Score/
├── backend/
│   ├── main.py                       # FastAPI app
│   ├── routes/
│   │   ├── upload.py                 # Upload & analysis endpoint
│   │   └── analysis.py              # Report download endpoint
│   ├── document_processing/
│   │   ├── pdf_processor.py
│   │   ├── ocr_processor.py
│   │   ├── excel_processor.py
│   │   └── doc_processor.py
│   ├── intelligence_layer/
│   │   ├── news_service.py
│   │   ├── compliance_service.py
│   │   ├── satellite_service.py
│   │   └── courts_service.py
│   ├── scoring_engine/
│   │   ├── bank_models.py
│   │   └── federated_scoring.py
│   └── report_generation/
│       └── report_builder.py
├── frontend/
│   ├── index.html                    # Upload page
│   ├── dashboard.html                # Results dashboard
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       ├── dashboard.js
│       └── three-bg.js
├── sample_documents/
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

**Backend** — Python · FastAPI · PyMuPDF · pdfplumber · python-docx · pandas · pytesseract · OpenCV · NumPy · scikit-learn · ReportLab

**Frontend** — HTML5 · Tailwind CSS · Alpine.js · Three.js · GSAP · Chart.js

---

## 📄 License

MIT — built for hackathon / prototype purposes.