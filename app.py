import sqlite3
import http.server
import socketserver
import json
from datetime import datetime, timedelta
import os
import urllib.parse

PORT = 8000

# Function to create a database connection
def create_connection():
    conn = sqlite3.connect('todo.db')
    conn.execute("PRAGMA foreign_keys = ON") # Enable foreign key support
    return conn

# Function to create tables if they don't exist
def create_tables():
    conn = create_connection()
    cursor = conn.cursor()
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)
    # Create tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            user_id INTEGER,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            due_date TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    # Create task_recurrence table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_recurrence (
            task_id INTEGER NOT NULL,
            recurrence_days INTEGER NOT NULL,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        )
    """)
    conn.commit()
    conn.close()

# Function to add a new user
def add_user(name):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name) VALUES (?)", (name,))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

# Function to get all users
def get_users():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

# Function to add a new task
def add_task(title, description, user_id, due_date, recurrence_days=None):
    conn = create_connection()
    cursor = conn.cursor()
    created_at = datetime.now().isoformat()
    cursor.execute("INSERT INTO tasks (title, description, user_id, created_at, due_date) VALUES (?, ?, ?, ?, ?)", (title, description, user_id, created_at, due_date))
    task_id = cursor.lastrowid
    if recurrence_days:
        cursor.execute("INSERT INTO task_recurrence (task_id, recurrence_days) VALUES (?, ?)", (task_id, recurrence_days))
    conn.commit()
    conn.close()
    if recurrence_days:
        add_recurring_tasks(task_id, recurrence_days, due_date)
    return task_id

# Function to add recurring tasks
def add_recurring_tasks(task_id, recurrence_days, due_date):
    conn = create_connection()
    cursor = conn.cursor()
    due_date_dt = datetime.fromisoformat(due_date)
    for i in range(1, 10):
        new_due_date = due_date_dt + timedelta(days=recurrence_days * i)
        new_due_date_str = new_due_date.isoformat()
        cursor.execute("INSERT INTO tasks (title, description, user_id, created_at, due_date) SELECT title, description, user_id, ?, ? FROM tasks WHERE id = ?", (datetime.now().isoformat(), new_due_date_str, task_id))
    conn.commit()
    conn.close()

# Function to get tasks, optionally filtered by date
def get_tasks(date=None):
    conn = create_connection()
    cursor = conn.cursor()
    if date:
        cursor.execute("""
            SELECT tasks.id, tasks.title, tasks.description, users.name, tasks.created_at, tasks.completed_at, tasks.due_date
            FROM tasks
            LEFT JOIN users ON tasks.user_id = users.id
            WHERE tasks.due_date LIKE ?
        """, (f"{date}%",))
    else:
        cursor.execute("""
            SELECT tasks.id, tasks.title, tasks.description, users.name, tasks.created_at, tasks.completed_at, tasks.due_date
            FROM tasks
            LEFT JOIN users ON tasks.user_id = users.id
        """)
    tasks = cursor.fetchall()
    conn.close()
    return tasks

# Function to mark a task as complete
def complete_task(task_id):
    conn = create_connection()
    cursor = conn.cursor()
    completed_at = datetime.now().isoformat()
    cursor.execute("UPDATE tasks SET completed_at = ? WHERE id = ?", (completed_at, task_id))
    conn.commit()
    conn.close()

# Function to edit a task
def edit_task(task_id, title, description, user_id, due_date):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET title = ?, description = ?, user_id = ?, due_date = ? WHERE id = ?", (title, description, user_id, due_date, task_id))
    conn.commit()
    conn.close()

# Function to get a single task by ID
def get_task(task_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tasks.id, tasks.title, tasks.description, users.name, tasks.created_at, tasks.completed_at, tasks.due_date, tasks.user_id
        FROM tasks
        LEFT JOIN users ON tasks.user_id = users.id
        WHERE tasks.id = ?
    """, (task_id,))
    task = cursor.fetchone()
    conn.close()
    return task

# Function to delete a task
def delete_task(task_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

# HTTP request handler
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = 'index.html'
        elif self.path.startswith('/static/'):
            pass
        elif self.path == '/get_tasks':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            date = self.get_query_param('date')
            tasks = get_tasks(date)
            tasks_list = []
            for task in tasks:
                task_dict = {
                    'id': task[0],
                    'title': task[1],
                    'description': task[2],
                    'userName': task[3],
                    'created_at': task[4],
                    'completed_at': task[5],
                    'due_date': task[6]
                }
                tasks_list.append(task_dict)
            self.wfile.write(json.dumps(tasks_list).encode())
            return
        elif self.path == '/get_users':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            users = get_users()
            users_list = []
            for user in users:
                user_dict = {
                    'id': user[0],
                    'name': user[1]
                }
                users_list.append(user_dict)
            self.wfile.write(json.dumps(users_list).encode())
            return
        elif self.path.startswith('/get_task/'):
            try:
                task_id = int(self.path.split('/')[-1])
                task = get_task(task_id)
                if task:
                    task_dict = {
                        'id': task[0],
                        'title': task[1],
                        'description': task[2],
                        'userName': task[3],
                        'created_at': task[4],
                        'completed_at': task[5],
                        'due_date': task[6],
                        'user_id': task[7]
                    }
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(task_dict).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            except ValueError:
                self.send_response(400)
                self.end_headers()
            return
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path == '/add_task':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            title = data.get('title')
            description = data.get('description')
            user_id = data.get('user_id')
            due_date = data.get('due_date')
            recurrence_days = data.get('recurrence_days')
            add_task(title, description, user_id, due_date, recurrence_days)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'message': 'Task added successfully'}).encode())
        elif self.path == '/add_user':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            name = data.get('name')
            add_user(name)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'message': 'User added successfully'}).encode())
        elif self.path.startswith('/complete_task/'):
            try:
                task_id = int(self.path.split('/')[-1])
                complete_task(task_id)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'message': 'Task completed successfully'}).encode())
            except ValueError:
                self.send_response(400)
                self.end_headers()
        elif self.path.startswith('/edit_task/'):
            try:
                task_id = int(self.path.split('/')[-1])
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(post_data)
                title = data.get('title')
                description = data.get('description')
                user_id = data.get('user_id')
                due_date = data.get('due_date')
                edit_task(task_id, title, description, user_id, due_date)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'message': 'Task edited successfully'}).encode())
            except ValueError:
                self.send_response(400)
                self.end_headers()
        elif self.path.startswith('/delete_task/'):
            try:
                task_id = int(self.path.split('/')[-1])
                delete_task(task_id)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'message': 'Task deleted successfully'}).encode())
            except ValueError:
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def get_query_param(self, param):
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        return query_params.get(param, [None])[0]

if __name__ == '__main__':
    create_tables()
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()
