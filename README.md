# Flask Authentication Portal

A secure authentication system built using Flask. This project demonstrates implementation of modern authentication mechanisms including email verification, password hashing, session management, and brute-force protection.

## Project Overview

This web application allows users to:

- Register an account
- Verify their email address
- Log in securely
- Access a protected dashboard
- Reset forgotten passwords
- Log out safely

The project focuses on implementing secure authentication workflows suitable for real-world web applications.

## Features

- Secure user registration system
- Token-based email verification
- Password hashing using bcrypt
- Session management using Flask-Login
- Rate limiting to prevent brute-force attacks
- Password reset via email token
- Protected dashboard access

## Technology Stack

Backend:
- Python
- Flask
- Flask-Login
- Flask-Mail
- Flask-SQLAlchemy
- Flask-Limiter

Security:
- bcrypt
- itsdangerous

Database:
- SQLite

Frontend:
- HTML
- CSS

## Installation Guide

Clone the repository:

git clone <your-repo-link>

Navigate to project folder:

cd project-folder

Install dependencies:

pip install -r requirements.txt

Run the application:

python app.py

Open in browser:

http://127.0.0.1:5000

## Authentication Workflow

1. User registers with username, email, and password  
2. Verification email is sent  
3. User activates account via token link  
4. User logs in securely  
5. Dashboard access is granted  
6. User can logout or reset password  

## Security Features

- Password hashing using bcrypt
- Email verification before login
- Session-based authentication
- Rate limiting on login endpoint
- Token-based password reset

## Future Improvements

- Migration to PostgreSQL
- Deployment using Docker
- Integration with OAuth providers
- Enhanced UI/UX

## Cloud Deployment

The application is deployed using AWS Lambda with Zappa for serverless execution.

## Author

Abhishek G Nair
