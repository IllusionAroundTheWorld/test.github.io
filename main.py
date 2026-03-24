import email
from datetime import datetime, timedelta
import pyodbc
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
import os
import smtplib
from email.mime.text import MIMEText
from flask import jsonify
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this

@app.route('/send_notification', methods=['POST'])
def send_notification():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    student_email = data.get('student_email')  # Fixed key
    student_name = data.get('student_name')
    book_name = data.get('book_name')
    issue_date = data.get('issue_date')
    return_date = data.get('return_date')

    # Validate required fields
    if not all([student_email, student_name, book_name, issue_date, return_date]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Email configuration
    sender_email = "narainjkans@gmail.com"
    sender_password = "hefh vudq kkly wfsd"  # Ensure this is an App Password
    subject = "Library Book Return Reminder - Student"
    body = f"""
    Dear {student_name},

    This is a reminder to return the book "{book_name}" issued on {issue_date}.
    Please return it by {return_date} to avoid any penalties.

    Regards,
    Library Management
    """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = student_email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return jsonify({'message': 'Notification sent successfully'}), 200
    except smtplib.SMTPAuthenticationError:
        return jsonify({'error': 'Authentication failed. Check your email and password.'}), 500
    except smtplib.SMTPException as e:
        return jsonify({'error': f'SMTP error occurred: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/send_staff_notification', methods=['POST'])
def send_staff_notification():
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    staff_email = data.get('staff_email')
    staff_name = data.get('staff_name')
    book_name = data.get('book_name')
    issue_date = data.get('issue_date')
    return_date = data.get('return_date')

    # Email configuration (update with your SMTP settings)
    sender_email = "narainjkans@gmail.com"
    sender_password = "hefh vudq kkly wfsd"
    subject = "Library Book Return Reminder - Staff"
    body = f"""
    Dear {staff_name},

    This is a reminder to return the book "{book_name}" issued on {issue_date}.
    Please return it by {return_date} to avoid any penalties.

    Regards,
    Library Management
    """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = staff_email

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:  # Example for Gmail
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return jsonify({'message': 'Notification sent successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_db_connection():
    """Establish and return a SQL Server database connection."""
    try:
        connection = pyodbc.connect(
            "DRIVER={SQL Server};"
            "SERVER=LAPTOP-SBLEMHDL\\SQLEXPRESS;"  # Update with your SQL Server name
            "DATABASE=LibraryDB;"  # Your database name
            "Trusted_Connection=yes;"  # Use Windows Authentication
        )
        return connection
    except pyodbc.Error as e:
        print(f"❌ Error connecting to SQL Server: {e}")
        return None


@app.route('/')
def home():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        if conn is None:
            return render_template('Login.html', error='Database connection failed')
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM Users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('Login.html', error='Invalid username or password')

    return render_template('Login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']

        if password != confirm_password:
            return render_template('Create.html', error='Passwords do not match')

        conn = get_db_connection()
        if conn is None:
            return render_template('Create.html', error='Database connection failed')
        cursor = conn.cursor()

        # Check if username exists
        cursor.execute("SELECT username FROM Users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return render_template('Create.html', error='Username already exists')

        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO Users (name, email, username, password_hash) VALUES (?, ?, ?, ?)",
            (name, email, username, password_hash)
        )
        conn.commit()
        conn.close()

        return redirect(url_for('login'))

    return render_template('Create.html')


@app.route('/new_student', methods=['GET', 'POST'])
def new_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        batch = request.form['batch']
        course = request.form['course']
        dob = request.form['dob']
        gender = request.form['gender']
        email = request.form['email']  # Add this line
        phone = request.form['phone']

        if not all([student_id, name, batch, course, dob, gender, email, phone]):  # Add email to validation
            flash('All fields are required.', 'error')
            return redirect(url_for('new_student'))

        try:
            dob = datetime.strptime(dob, '%Y-%m-%d').date().strftime('%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            return redirect(url_for('new_student'))

        conn = get_db_connection()
        if conn is None:
            flash('Database connection failed.', 'error')
            return redirect(url_for('new_student'))

        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Students (student_id, name, batch, course, dob, gender, email, phone) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (student_id, name, batch, course, dob, gender, email, phone))  # Add email to insert
            conn.commit()
            flash('Student registered successfully!', 'success')
        except pyodbc.Error as e:
            flash(f'Error registering student: {e}', 'error')
        finally:
            conn.close()

        return redirect(url_for('new_student'))

    return render_template('Student.html')


@app.route('/new_book', methods=['GET', 'POST'])
def new_book():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed.', 'error')
        return render_template('new_book.html')

    cursor = conn.cursor()

    if request.method == 'POST':
        book_id = request.form['book_id']
        book_name = request.form['book_name']
        author_name = request.form['author_name']  # Changed from 'edition' to 'author_name'
        publisher = request.form['publisher']

        # Validate form data
        if not book_id or not book_name or not author_name:  # Added author_name to validation
            flash('Book ID, Book Name, and Author Name are required.', 'error')
            return render_template('new_book.html')

        try:
            # Check if book_id already exists
            cursor.execute("SELECT book_id FROM Books WHERE book_id = ?", (book_id,))
            if cursor.fetchone():
                flash('Book ID already exists.', 'error')
            else:
                # Insert new book with author_name instead of edition
                cursor.execute("""
                    INSERT INTO Books (book_id, book_name, author_name, publisher)
                    VALUES (?, ?, ?, ?)
                """, (book_id, book_name, author_name, publisher))
                conn.commit()
                flash('Book added successfully!', 'success')
        except pyodbc.Error as e:
            flash(f'Error adding book: {e}', 'error')

    conn.close()
    return render_template('new_book.html')


@app.route('/new_staff', methods=['GET', 'POST'])
def new_staff():
    if request.method == 'POST':
        staff_register = request.form['staff_register']
        staff_name = request.form['staff_name']
        designation = request.form['designation']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']  # This is causing the error because 'gender' is not in the form
        email = request.form['email']  # This is also missing from the form
        phone_number = request.form['phone_number']

        if not all([staff_register, staff_name, designation, date_of_birth, gender, email, phone_number]):  # Add gender and email to validation
            flash('All fields are required.', 'error')
            return redirect(url_for('new_staff'))

        try:
            date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date().strftime('%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            return redirect(url_for('new_staff'))

        conn = get_db_connection()
        if conn is None:
            flash('Database connection failed.', 'error')
            return redirect(url_for('new_staff'))

        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO Staff (staff_register, staff_name, designation, date_of_birth, gender, email, phone_number)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (staff_register, staff_name, designation, date_of_birth, gender, email, phone_number))  # Add gender and email to insert
            conn.commit()
            flash('Staff registered successfully!', 'success')
        except pyodbc.Error as e:
            flash(f'Error registering staff: {e}', 'error')
        finally:
            conn.close()

        return redirect(url_for('new_staff'))

    return render_template('new_staff.html')


@app.route('/new_user')
def new_user():
    return "New User Page (Under Construction)"


@app.route('/staff_issue_book', methods=['GET', 'POST'])
def staff_issue_book():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed.', 'error')
        return render_template('staff_issue_book.html')

    cursor = conn.cursor()

    # Fetch available books (not issued to students or staff yet)
    cursor.execute("""
        SELECT book_id, book_name, author_name, publisher
        FROM Books 
        WHERE book_id NOT IN (
            SELECT book_id FROM IssuedBooks WHERE return_date IS NULL
            UNION
            SELECT book_id FROM Staff_IssuedBooks WHERE return_date IS NULL
        )
    """)
    books = cursor.fetchall()

    if request.method == 'POST':
        book_id = request.form['book_id']
        staff_register = request.form['staff_register']
        issue_date = datetime.now().strftime('%Y-%m-%d')

        # Fetch staff details including email
        cursor.execute("""
            SELECT staff_name, designation, phone_number, email
            FROM Staff 
            WHERE staff_register = ?
        """, (staff_register,))
        staff = cursor.fetchone()

        if not staff:
            flash('Staff not found.', 'error')
        else:
            try:
                # Insert into Staff_IssuedBooks table
                cursor.execute("""
                    INSERT INTO Staff_IssuedBooks (book_id, staff_register, issue_date) 
                    VALUES (?, ?, ?)
                """, (book_id, staff_register, issue_date))
                conn.commit()

                # Extract staff details
                staff_name = staff[0]
                staff_email = staff[3]  # Email is at index 3
                book_name = next((book[1] for book in books if book[0] == book_id), "Unknown Book")
                return_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')  # 14-day return period

                # Send notification email
                sender_email = "narainjkans@gmail.com"
                sender_password = "hefh vudq kkly wfsd"  # Use App Password for Gmail
                subject = "Library Book Issued - Return Reminder (Staff)"
                body = f"""
                Dear {staff_name},

                The book "{book_name}" has been issued to you on {issue_date}.
                Please return it by {return_date} to avoid any penalties.

                Regards,
                Library Management
                """

                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = sender_email
                msg['To'] = staff_email

                try:
                    with smtplib.SMTP('smtp.gmail.com', 587) as server:
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.send_message(msg)
                    flash(f'Book issued successfully to {staff_name}! Notification sent to {staff_email}.', 'success')
                except smtplib.SMTPException as e:
                    flash(f'Book issued successfully to {staff_name}, but notification failed: {str(e)}', 'error')

            except pyodbc.Error as e:
                flash(f'Error issuing book: {e}', 'error')

    conn.close()
    return render_template('staff_issue_book.html', books=books, today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/get_staff', methods=['GET'])
def get_staff():
    staff_register = request.args.get('staff_register')
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'})

    cursor = conn.cursor()
    cursor.execute("SELECT staff_name, designation, phone_number, email FROM Staff WHERE staff_register = ?",
                   (staff_register,))
    staff = cursor.fetchone()
    conn.close()

    if staff:
        return jsonify({
            'staff_name': staff[0],
            'designation': staff[1],
            'phone_number': staff[2],
            'staff_email': staff[3]  # Added staff_email
        })
    return jsonify({'error': 'Staff not found'})


@app.route('/staff_return_book', methods=['GET', 'POST'])
def staff_return_book():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed.', 'error')
        return render_template('staff_return_book.html')

    cursor = conn.cursor()

    if request.method == 'POST':
        issue_id = request.form['issue_id']
        return_date = datetime.now().strftime('%Y-%m-%d')  # Actual return date is today’s date

        # Fetch issue details
        cursor.execute("""
            SELECT staff_register, book_id, issue_date 
            FROM Staff_IssuedBooks 
            WHERE issue_id = ? AND return_date IS NULL
        """, (issue_id,))
        issue = cursor.fetchone()

        if not issue:
            flash('Book already returned or invalid Issue ID.', 'error')
        else:
            try:
                # Insert into Staff_Return_book table
                cursor.execute("""
                    INSERT INTO Staff_Return_book (issue_id, staff_register, book_id, issue_date, return_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (issue_id, issue[0], issue[1], issue[2], return_date))

                # Update Staff_IssuedBooks to mark as returned
                cursor.execute("""
                    UPDATE Staff_IssuedBooks 
                    SET return_date = ? 
                    WHERE issue_id = ?
                """, (return_date, issue_id))

                conn.commit()
                flash('Book returned and details saved successfully!', 'success')
            except pyodbc.Error as e:
                flash(f'Error processing return: {e}', 'error')

    # Fetch all issued books for staff that haven't been returned, including email
    cursor.execute("""
        SELECT sib.issue_id, sib.staff_register, sib.book_id, sib.issue_date, s.staff_name, b.book_name, s.email 
        FROM Staff_IssuedBooks sib
        JOIN Staff s ON sib.staff_register = s.staff_register
        JOIN Books b ON sib.book_id = b.book_id
        WHERE sib.return_date IS NULL
    """)
    issued_books_raw = cursor.fetchall()
    conn.close()

    # Process issued_books to include default return date (issue_date + 7 days)
    issued_books = []
    for book in issued_books_raw:
        issue_date = datetime.strptime(book[3], '%Y-%m-%d')  # Convert string to datetime
        default_return_date = (issue_date + timedelta(days=7)).strftime('%Y-%m-%d')  # Add 7 days
        issued_books.append(list(book) + [default_return_date])  # Append default return date

    return render_template('staff_return_book.html', issued_books=issued_books, today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed.', 'error')
        return render_template('issue_book.html')

    cursor = conn.cursor()

    # Fetch available books
    cursor.execute("""
        SELECT book_id, book_name, author_name, publisher
        FROM Books 
        WHERE book_id NOT IN (SELECT book_id FROM IssuedBooks WHERE return_date IS NULL)
    """)
    books = cursor.fetchall()

    if request.method == 'POST':
        book_id = request.form['book_id']
        student_roll = request.form['student_roll']
        issue_date = datetime.now().strftime('%Y-%m-%d')

        # Fetch student details including email
        cursor.execute("""
            SELECT name, course, batch, phone, email 
            FROM Students 
            WHERE student_id = ?
        """, (student_roll,))
        student = cursor.fetchone()

        if not student:
            flash('Student not found.', 'error')
        else:
            try:
                # Insert into IssuedBooks table
                cursor.execute("""
                    INSERT INTO IssuedBooks (book_id, student_id, issue_date) 
                    VALUES (?, ?, ?)
                """, (book_id, student_roll, issue_date))
                conn.commit()

                # Extract student details
                student_name = student[0]
                student_email = student[4]
                book_name = next((book[1] for book in books if book[0] == book_id), "Unknown Book")
                return_date = (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d')

                # Send notification email directly
                sender_email = "narainjkans@gmail.com"
                sender_password = "hefh vudq kkly wfsd"
                subject = "Library Book Issued - Return Reminder"
                body = f"""
                Dear {student_name},

                The book "{book_name}" has been issued to you on {issue_date}.
                Please return it by {return_date} to avoid any penalties.

                Regards,
                Library Management
                """

                msg = MIMEText(body)
                msg['Subject'] = subject
                msg['From'] = sender_email
                msg['To'] = student_email

                try:
                    with smtplib.SMTP('smtp.gmail.com', 587) as server:
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.send_message(msg)
                    flash(f'Book issued successfully to {student_name}! Notification sent.', 'success')
                except smtplib.SMTPException as e:
                    flash(f'Book issued successfully to {student_name}, but notification failed: {str(e)}', 'error')

            except pyodbc.Error as e:
                flash(f'Error issuing book: {e}', 'error')

    conn.close()
    return render_template('issue_book.html', books=books, today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/get_student')
def get_student():
    roll = request.args.get('roll')
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'})

    cursor = conn.cursor()
    cursor.execute("""
        SELECT name, course, batch, phone, email 
        FROM Students 
        WHERE student_id = ?
    """, (roll,))
    student = cursor.fetchone()
    conn.close()

    if student:
        return jsonify({
            'name': student[0],
            'course': student[1],
            'batch': student[2],
            'phone': student[3],
            'email': student[4]  # Add email to the response
        })
    else:
        return jsonify({'error': 'Student not found'})


@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed.', 'error')
        return render_template('return_book.html')

    cursor = conn.cursor()

    if request.method == 'POST':
        issue_id = request.form['issue_id']
        return_date = datetime.now().strftime('%Y-%m-%d')  # Actual return date is today's date

        # Fetch issue details
        cursor.execute("""
            SELECT student_id, book_id, issue_date 
            FROM IssuedBooks 
            WHERE issue_id = ? AND return_date IS NULL
        """, (issue_id,))
        issue = cursor.fetchone()

        if not issue:
            flash('Book already returned or invalid Issue ID.', 'error')
        else:
            try:
                # Insert into Return_book table
                cursor.execute("""
                    INSERT INTO Return_book (issue_id, student_id, book_id, issue_date, return_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (issue_id, issue[0], issue[1], issue[2], return_date))

                # Update IssuedBooks to mark as returned
                cursor.execute("""
                    UPDATE IssuedBooks 
                    SET return_date = ? 
                    WHERE issue_id = ?
                """, (return_date, issue_id))

                conn.commit()
                flash('Book returned and details saved successfully!', 'success')
            except pyodbc.Error as e:
                flash(f'Error processing return: {e}', 'error')

    # Fetch all issued books that haven't been returned, including email
    cursor.execute("""
        SELECT ib.issue_id, ib.student_id, ib.book_id, ib.issue_date, s.name, b.book_name, s.email 
        FROM IssuedBooks ib
        JOIN Students s ON ib.student_id = s.student_id
        JOIN Books b ON ib.book_id = b.book_id
        WHERE ib.return_date IS NULL
    """)
    issued_books_raw = cursor.fetchall()
    conn.close()

    # Process issued_books to include default return date (issue_date + 7 days)
    issued_books = []
    for book in issued_books_raw:
        issue_date = datetime.strptime(book[3], '%Y-%m-%d')  # Convert string to datetime
        default_return_date = (issue_date + timedelta(days=7)).strftime('%Y-%m-%d')  # Add 7 days
        issued_books.append(list(book) + [default_return_date])  # Append default return date

    return render_template('return_book.html', issued_books=issued_books, today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/edit_book', methods=['GET', 'POST'])
def edit_book():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed.', 'error')
        return render_template('edit_book.html')

    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        book_id = request.form.get('book_id')

        if action == 'delete':
            try:
                # Check if the book is currently issued
                cursor.execute("""
                    SELECT book_id FROM IssuedBooks WHERE book_id = ? AND return_date IS NULL
                    UNION
                    SELECT book_id FROM Staff_IssuedBooks WHERE book_id = ? AND return_date IS NULL
                """, (book_id, book_id))
                if cursor.fetchone():
                    flash('Cannot delete book: it is currently issued.', 'error')
                else:
                    cursor.execute("DELETE FROM Books WHERE book_id = ?", (book_id,))
                    conn.commit()
                    flash('Book deleted successfully!', 'success')
            except pyodbc.Error as e:
                flash(f'Error deleting book: {e}', 'error')

        elif action == 'edit':
            book_name = request.form['book_name']
            author_name = request.form['author_name']  # Changed from 'edition' to 'author_name'
            publisher = request.form['publisher']

            try:
                cursor.execute("""
                    UPDATE Books 
                    SET book_name = ?, author_name = ?, publisher = ?  -- Changed edition to author_name
                    WHERE book_id = ?
                """, (book_name, author_name, publisher, book_id))
                conn.commit()
                flash('Book updated successfully!', 'success')
            except pyodbc.Error as e:
                flash(f'Error updating book: {e}', 'error')

    # Fetch all books for display
    cursor.execute("SELECT book_id, book_name, author_name, publisher FROM Books")  # Changed edition to author_name
    books = cursor.fetchall()
    conn.close()

    return render_template('edit_book.html', books=books)


@app.route('/edit_staff', methods=['GET', 'POST'])
def edit_staff():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed.', 'error')
        return render_template('edit_staff.html')

    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        staff_register = request.form.get('staff_register')

        if action == 'delete':
            try:
                cursor.execute("""
                    SELECT staff_register 
                    FROM Staff_IssuedBooks 
                    WHERE staff_register = ?
                """, (staff_register,))
                if cursor.fetchone():
                    flash('Cannot delete staff: they have issued book records.', 'error')
                else:
                    cursor.execute("DELETE FROM Staff WHERE staff_register = ?", (staff_register,))
                    conn.commit()
                    flash('Staff deleted successfully!', 'success')
            except pyodbc.Error as e:
                flash(f'Error deleting staff: {e}', 'error')

        elif action == 'edit':
            staff_name = request.form['staff_name']
            designation = request.form['designation']
            date_of_birth = request.form['date_of_birth']
            gender = request.form['gender']  # Add gender
            email = request.form['email']    # Add email
            phone_number = request.form['phone_number']

            try:
                date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date().strftime('%Y-%m-%d')
                cursor.execute("""
                    UPDATE Staff 
                    SET staff_name = ?, designation = ?, date_of_birth = ?, gender = ?, email = ?, phone_number = ?
                    WHERE staff_register = ?
                """, (staff_name, designation, date_of_birth, gender, email, phone_number, staff_register))  # Add gender and email to update
                conn.commit()
                flash('Staff updated successfully!', 'success')
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            except pyodbc.Error as e:
                flash(f'Error updating staff: {e}', 'error')

    # Fetch all staff with gender and email
    cursor.execute("SELECT staff_register, staff_name, designation, date_of_birth, gender, email, phone_number FROM Staff")
    staff = cursor.fetchall()
    conn.close()

    return render_template('edit_staff.html', staff=staff)


@app.route('/edit_student', methods=['GET', 'POST'])
def edit_student():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed.', 'error')
        return render_template('edit_student.html')

    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        student_id = request.form.get('student_id')

        if action == 'delete':
            try:
                cursor.execute("""
                    SELECT student_id 
                    FROM IssuedBooks 
                    WHERE student_id = ?
                """, (student_id,))
                if cursor.fetchone():
                    flash('Cannot delete student: they have issued book records.', 'error')
                else:
                    cursor.execute("DELETE FROM Students WHERE student_id = ?", (student_id,))
                    conn.commit()
                    flash('Student deleted successfully!', 'success')
            except pyodbc.Error as e:
                flash(f'Error deleting student: {e}', 'error')

        elif action == 'edit':
            name = request.form['name']
            batch = request.form['batch']
            course = request.form['course']
            dob = request.form['dob']
            gender = request.form['gender']
            email = request.form['email']  # Add email
            phone = request.form['phone']

            try:
                dob = datetime.strptime(dob, '%Y-%m-%d').date().strftime('%Y-%m-%d')
                cursor.execute("""
                    UPDATE Students 
                    SET name = ?, batch = ?, course = ?, dob = ?, gender = ?, email = ?, phone = ?
                    WHERE student_id = ?
                """, (name, batch, course, dob, gender, email, phone, student_id))  # Add email to update
                conn.commit()
                flash('Student updated successfully!', 'success')
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            except pyodbc.Error as e:
                flash(f'Error updating student: {e}', 'error')

    # Fetch all students with email
    cursor.execute("SELECT student_id, name, batch, course, dob, gender, email, phone FROM Students")
    students = cursor.fetchall()
    conn.close()

    return render_template('edit_student.html', students=students)


@app.route('/view_details', methods=['GET', 'POST'])
def view_details():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if conn is None:
        flash('Database connection failed.', 'error')
        return render_template('view_details.html')

    cursor = conn.cursor()

    # Fetch Student Details (unchanged)
    cursor.execute("SELECT student_id, name, batch, course, dob, gender, email, phone FROM Students")
    students = cursor.fetchall()

    # Fetch Student Issued Books (unchanged)
    cursor.execute("""
        SELECT ib.issue_id, ib.student_id, ib.book_id, ib.issue_date, ib.return_date, s.name, b.book_name
        FROM IssuedBooks ib
        JOIN Students s ON ib.student_id = s.student_id
        JOIN Books b ON ib.book_id = b.book_id
    """)
    student_issued = cursor.fetchall()

    # Fetch Student Returned Books (unchanged)
    cursor.execute("""
        SELECT rb.return_id, rb.issue_id, rb.student_id, rb.book_id, rb.issue_date, rb.return_date, s.name, b.book_name
        FROM Return_book rb
        JOIN Students s ON rb.student_id = s.student_id
        JOIN Books b ON rb.book_id = b.book_id
    """)
    student_returned = cursor.fetchall()

    # Fetch Staff Details with gender and email
    cursor.execute("SELECT staff_register, staff_name, designation, date_of_birth, gender, email, phone_number FROM Staff")
    staff = cursor.fetchall()

    # Fetch Staff Issued Books (unchanged)
    cursor.execute("""
        SELECT sib.issue_id, sib.staff_register, sib.book_id, sib.issue_date, sib.return_date, s.staff_name, b.book_name
        FROM Staff_IssuedBooks sib
        JOIN Staff s ON sib.staff_register = s.staff_register
        JOIN Books b ON sib.book_id = b.book_id
    """)
    staff_issued = cursor.fetchall()

    # Fetch Staff Returned Books (unchanged)
    cursor.execute("""
        SELECT srb.return_id, srb.issue_id, srb.staff_register, srb.book_id, srb.issue_date, srb.return_date, s.staff_name, b.book_name
        FROM Staff_Return_book srb
        JOIN Staff s ON srb.staff_register = s.staff_register
        JOIN Books b ON srb.book_id = b.book_id
    """)
    staff_returned = cursor.fetchall()

    conn.close()

    # Handle PDF download (update staff_headers)
    if request.method == 'POST' and request.form.get('action') == 'download':
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, leftMargin=0.5 * inch, rightMargin=0.5 * inch,
                                topMargin=0.75 * inch, bottomMargin=0.5 * inch)
        elements = []
        styles = getSampleStyleSheet()

        # Custom styles (unchanged)
        header_style = ParagraphStyle('Header', parent=styles['Heading1'], fontSize=16,
                                      textColor=colors.HexColor('#FFA000'))
        subheader_style = ParagraphStyle('Subheader', parent=styles['Heading2'], fontSize=12,
                                         textColor=colors.HexColor('#333333'))

        # Logo (unchanged)
        logo_path = os.path.join(app.static_folder, 'Logo.jpg')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=2 * inch, height=2 * inch)
            elements.append(logo)
        elements.append(Paragraph("Library Management Report", header_style))
        elements.append(Spacer(1, 0.2 * inch))

        # Helper function to create styled table (unchanged)
        def create_table(data, headers, title):
            table_data = [headers] + [[str(cell) if cell is not None else 'N/A' for cell in row] for row in data]
            col_widths = [0] * len(headers)
            for row in table_data:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)) * 0.1 * inch)
            total_width = sum(col_widths)
            if total_width > 7.5 * inch:
                scale_factor = 7.5 * inch / total_width
                col_widths = [w * scale_factor for w in col_widths]
            else:
                col_widths = [max(w, 0.8 * inch) for w in col_widths]
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFA000')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F4F4F4')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#333333')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
            ]))
            return [Paragraph(title, subheader_style), Spacer(1, 0.1 * inch), table, Spacer(1, 0.2 * inch)]

        # Student Details (unchanged)
        student_headers = ['Student ID', 'Name', 'Batch', 'Course', 'DOB', 'Gender', 'Email', 'Phone']
        elements.extend(create_table(students, student_headers, "Student Details"))

        # Student Issued Books (unchanged)
        issued_headers = ['Issue ID', 'Student ID', 'Book ID', 'Issue Date', 'Return Date', 'Student Name', 'Book Name']
        elements.extend(create_table(student_issued, issued_headers, "Student Issued Books"))

        # Student Returned Books (unchanged)
        returned_headers = ['Return ID', 'Issue ID', 'Student ID', 'Book ID', 'Issue Date', 'Return Date', 'Student Name', 'Book Name']
        elements.extend(create_table(student_returned, returned_headers, "Student Returned Books"))

        # Staff Details (updated with gender and email)
        staff_headers = ['Staff Register', 'Name', 'Designation', 'DOB', 'Gender', 'Email', 'Phone']
        elements.extend(create_table(staff, staff_headers, "Staff Details"))

        # Staff Issued Books (unchanged)
        staff_issued_headers = ['Issue ID', 'Staff Register', 'Book ID', 'Issue Date', 'Return Date', 'Staff Name', 'Book Name']
        elements.extend(create_table(staff_issued, staff_issued_headers, "Staff Issued Books"))

        # Staff Returned Books (unchanged)
        staff_returned_headers = ['Return ID', 'Issue ID', 'Staff Register', 'Book ID', 'Issue Date', 'Return Date', 'Staff Name', 'Book Name']
        elements.extend(create_table(staff_returned, staff_returned_headers, "Staff Returned Books"))

        # Build PDF (unchanged)
        def add_header_footer(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(colors.HexColor('#FFA000'))
            canvas.rect(0, letter[1] - 0.5 * inch, letter[0], 0.5 * inch, fill=1)
            canvas.setFillColor(colors.white)
            canvas.setFont("Helvetica-Bold", 12)
            canvas.drawCentredString(letter[0] / 2, letter[1] - 0.35 * inch, "Library Management Report")
            canvas.setFillColor(colors.HexColor('#333333'))
            canvas.setFont("Helvetica", 8)
            canvas.drawString(0.5 * inch, 0.25 * inch, f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            canvas.drawRightString(letter[0] - 0.5 * inch, 0.25 * inch, f"Page {doc.page}")
            canvas.restoreState()

        doc.build(elements, onFirstPage=add_header_footer, onLaterPages=add_header_footer)
        pdf_buffer.seek(0)
        return Response(pdf_buffer, mimetype='application/pdf',
                        headers={'Content-Disposition': 'attachment;filename=library_report.pdf'})

    return render_template('view_details.html',
                           students=students,
                           student_issued=student_issued,
                           student_returned=student_returned,
                           staff=staff,
                           staff_issued=staff_issued,
                           staff_returned=staff_returned)


@app.route('/delete_book/<book_id>', methods=['POST'])
def delete_book(book_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed', 'error')
        return redirect(url_for('edit_book'))

    cursor = conn.cursor()
    try:
        # Check if book is in IssuedBooks
        cursor.execute("""
            SELECT COUNT(*) 
            FROM IssuedBooks 
            WHERE book_id = ? AND return_date IS NULL
        """, (book_id,))
        active_issues = cursor.fetchone()[0]

        if active_issues > 0:
            flash('Cannot delete: Book is currently issued to students', 'error')
        else:
            # Delete from IssuedBooks (returned books history)
            cursor.execute("DELETE FROM IssuedBooks WHERE book_id = ?", (book_id,))
            # Delete from Books
            cursor.execute("DELETE FROM Books WHERE book_id = ?", (book_id,))
            conn.commit()
            flash('Book deleted successfully!', 'success')
    except pyodbc.Error as e:
        flash(f'Error deleting book: {e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('edit_book'))

if __name__ == '__main__':
    app.run(debug=True)