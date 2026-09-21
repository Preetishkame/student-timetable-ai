# 📚 Smart Timetable AI

An AI-powered student management website built using **Python (Flask), HTML, CSS, JavaScript, and PostgreSQL**.

Smart Timetable AI helps students organize their studies by managing their timetable, homework, assignments, exams, attendance, and study schedules in one place.

---

## 🚀 Features

* 🔐 User Registration & Login
* 📅 Smart Timetable Generator
* 📖 Homework Manager
* 📝 Assignment Tracker
* 📚 Exam Schedule & Reminders
* 📊 Attendance Calculator
* 🤖 AI Study Timetable Generator
* 📈 Dashboard Overview
* 🗄️ PostgreSQL Database
* 📱 Responsive Design

---

## 🛠️ Built With

* Python 3
* Flask
* PostgreSQL
* HTML5
* CSS3
* JavaScript
* Flask-CORS
* Werkzeug

---

## 📂 Project Structure

```text
Smart-Timetable-AI/
│
├── app.py
├── requirements.txt
├── README.md
├── write_up.md
│
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── dashboard.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       ├── app.js
│       ├── auth.js
│       └── dashboard.js
```

---

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Smart-Timetable-AI.git
```

### 2. Go to the Project Folder

```bash
cd Smart-Timetable-AI
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL

Create a PostgreSQL database and configure the database connection using environment variables.

The application uses PostgreSQL to store and manage user and academic information.

### 5. Run the Application

```bash
python app.py
```

### 6. Open in Browser

```text
http://127.0.0.1:5000
```

---

## 💻 Main Sections

The application includes:

* 🏠 Home Page
* 🔐 Login & Registration
* 📊 Dashboard
* 🤖 AI Timetable Generator
* 📅 Study Timetable
* 📖 Homework
* 📝 Assignments
* 📚 Exams
* 📊 Attendance

---

## 🤖 AI Timetable Generator

The AI Timetable Generator creates a personalized study schedule based on information provided by the student.

It can consider:

* Subjects
* Available study hours
* Wake-up time
* Study requirements

The application organizes study sessions according to the available time and creates a structured study schedule.

---

## 📚 Academic Reminders

### 📝 Homework Reminder

Students can add their homework and keep track of pending work and deadlines.

### 📋 Assignment Reminder

Students can record assignments and their due dates so they can complete them on time.

### 📖 Exam Reminder

Students can add upcoming examinations and keep track of important exam dates for better preparation.

---

## 📊 Attendance Calculator

The Attendance Calculator helps students calculate their attendance percentage.

Students can enter:

* Classes attended
* Total classes

The application calculates the attendance percentage and displays the result.

---

## 🗄️ Database

**PostgreSQL** is used as the database for the application.

It stores and manages information such as:

* Users
* Subjects
* Homework
* Assignments
* Exams
* Attendance
* Timetable

PostgreSQL provides reliable data storage and also makes the application suitable for online deployment.

---

## 🌐 Deployment

The application can be deployed online using a cloud hosting service with a PostgreSQL database.

The database connection can be configured using environment variables, making the project suitable for deployment platforms such as Render.

---

## 📌 Future Scope

Smart Timetable AI can be improved further by adding more useful features in the future.

### 🎒 Smart Bag Reminder

A future **Bag Reminder** feature could check the student's timetable for the next school day and remind them which books, notebooks, practical files and other required items they need to take to school.

For example, if the next day's timetable contains Mathematics, Science and English, the application could remind the student to pack the required books and notebooks.

Other possible improvements include:

* 🔔 Notification and reminder alerts
* 🎒 Smart Bag Reminder
* 📅 Calendar integration
* 🤖 More personalized AI study recommendations
* 📈 Study progress tracking
* 📊 Subject-wise attendance
* 📱 Mobile application
* ☁️ Cloud-based data management

---

## 📄 Project Write-up

A detailed project write-up is included in the file:

```text
write_up.md
```

The write-up contains:

* Introduction
* Objectives
* Technologies Used
* Working of the Project
* Main Features
* Advantages
* Future Scope
* Conclusion

---

## 👨‍💻 Author

**Preetish**

Class 10 Student

---

## 📄 License

This project is created for educational purposes and school projects.
