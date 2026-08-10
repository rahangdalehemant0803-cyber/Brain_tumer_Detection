# NeuroScan AI — Brain Tumor Detection Web App

Flask + SQLite based web application jo MRI images me brain tumor detect
karta hai using aapka trained Keras (.h5) model. Koi external API use
nahi hoti — sab kuch locally chalta hai.

## Features

- Login / Register system (Flask-Login + password hashing)
- SQLite database (Users + Scans history)
- Drag & drop MRI upload with live preview
- Local model inference (4-class: Glioma, Meningioma, No Tumor, Pituitary)
- Result page with confidence + class-wise probability breakdown
- Downloadable PDF report for every scan (reportlab)
- Scan history page
- Tumor information / education page
- Clean, custom-designed UI (no Bootstrap defaults)

## Folder Structure

```
brain_tumor_app/
├── app.py                     # main Flask app + routes
├── config.py                  # all settings (paths, image size, class labels)
├── extensions.py              # db, login_manager instances
├── models.py                  # User & Scan database models
├── requirements.txt
├── model/
│   └── brain_tumor_model.h5   # <-- put your trained model here
├── utils/
│   ├── predict.py             # model loading + prediction logic
│   └── report_generator.py    # PDF report builder
├── static/
│   ├── css/
│   │   ├── style.css          # main design system
│   │   └── auth.css           # login/register page styles
│   ├── js/
│   │   └── main.js            # dropzone + animations
│   ├── images/
│   │   └── brain-watermark.svg
│   └── uploads/                # uploaded MRI images get saved here
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── result.html
│   ├── history.html
│   ├── info.html
│   └── error.html
└── instance/
    └── database.db             # auto-created SQLite DB
```

## Setup

### 1. Virtual environment banaye (recommended)

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### 2. Dependencies install karein

```bash
pip install -r requirements.txt
```

### 3. Apna model rakhein

Apni trained `.h5` file ko is path par copy karein:

```
model/brain_tumor_model.h5
```

### 4. `config.py` check karein — YEH SABSE ZAROORI STEP HAI

```python
IMAGE_SIZE = (150, 150)   # apne model ke training input size se match karein
CLASS_LABELS = ["Glioma", "Meningioma", "No Tumor", "Pituitary"]
```

`CLASS_LABELS` ka order EXACTLY wahi hona chahiye jo order training ke
time model ne seekha tha (agar aapne `ImageDataGenerator.flow_from_directory`
use kiya tha, to yeh order usually alphabetical hota hai — jo already
upar diya gaya hai).

### 5. App run karein

```bash
python app.py
```

Browser me kholein: **http://127.0.0.1:5000**

Pehli baar register karke account banayein, phir login karke dashboard
se MRI image upload karein.

## Notes

- Database automatically create ho jayega first run par (`instance/database.db`).
- Max upload size 8 MB hai — `config.py` me `MAX_CONTENT_LENGTH` se change kar sakte ho.
- Production me deploy karte waqt `SECRET_KEY` ko environment variable se set karein
  aur `debug=True` hata dein.
- Yeh tool sirf screening-assistance ke liye hai, medical diagnosis nahi hai —
  disclaimer har report aur result page par already add hai.
