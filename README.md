# 🌱 Crop Prediction & Disease Detection System

An AI-powered smart agriculture web application that helps farmers and users make better farming decisions by recommending suitable crops and detecting plant diseases using machine learning.

---

## 🚀 Features

* 🌾 **Crop Recommendation**

  * Suggests best crops based on:

    * Nitrogen (N)
    * Phosphorus (P)
    * Potassium (K)
    * Temperature
    * Humidity
    * pH
    * Rainfall

* 🍃 **Disease Detection**

  * Upload plant leaf images
  * Detect diseases using ML / Deep Learning
  * Provides results instantly

* 🌐 **User-Friendly UI**

  * Simple and responsive design
  * Easy input and output display

---

## 🛠️ Tech Stack

* **Frontend:** HTML, CSS, JavaScript
* **Backend:** Django (Python)
* **Machine Learning:** Scikit-learn / TensorFlow
* **Database:** SQLite
* **Libraries:** NumPy, Pandas, OpenCV

---


## ⚙️ Installation & Setup

### 1. Clone the repo

git clone https://github.com/your-username/cropPrediction_diseases_detection.git
cd cropPrediction_diseases_detection

### 2. Create virtual environment

python -m venv venv
venv\Scripts\activate

### 3. Install dependencies

pip install -r requirements.txt

### 4. Run server

python manage.py runserver

### 5. Open in browser

http://127.0.0.1:8000/

---

## 🧠 How It Works

### 🌾 Crop Prediction

* Takes soil + environmental data
* ML model predicts best crop

### 🍃 Disease Detection

* User uploads leaf image
* Model classifies disease

---

## 📊 Sample Input

| Parameter   | Value |
| ----------- | ----- |
| Nitrogen    | 90    |
| Phosphorus  | 42    |
| Potassium   | 43    |
| Temperature | 25°C  |
| Humidity    | 80%   |
| pH          | 6.5   |
| Rainfall    | 200   |

---

## 📌 Future Improvements

* 🌦️ Weather API integration
* 📱 Mobile app version
* 🤖 Better deep learning models
* 🌱 Fertilizer recommendation

---

## 🤝 Contributing

Feel free to fork this repo and contribute.

---

## ⭐ Support

If you like this project:

* ⭐ Star the repo
* 🍴 Fork it
