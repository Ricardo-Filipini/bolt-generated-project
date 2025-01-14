document.addEventListener('DOMContentLoaded', function() {
    loadUsers();
    loadTasks();
});

// Function to load tasks from the server
function loadTasks() {
    const datePicker = document.getElementById('datePicker');
    const selectedDate = datePicker.value;
    fetch(`/get_tasks${selectedDate ? '?date=' + selectedDate : ''}`)
        .then(response => response.json())
        .then(tasks => {
            const taskList = document.getElementById('taskList');
            taskList.innerHTML = '';
            tasks.forEach(task => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `
                    <span>${task.title}</span>
                    <p>${task.description}</p>
                    <p>Usuário: ${task.userName || 'N/A'}</p>
                    <p>Criado em: ${formatDate(task.created_at)}</p>
                    ${task.completed_at ? `<p>Concluído em: ${formatDate(task.completed_at)}</p>` : ''}
                    ${task.due_date ? `<p>Data de Vencimento: ${formatDate(task.due_date)}</p>` : ''}
                    <div>
                        <button class="complete-btn" onclick="completeTask(${task.id})" ${task.completed_at ? 'disabled' : ''}>Concluir</button>
                        <button class="edit-btn" onclick="openEditModal(${task.id})">Editar</button>
                        <button class="delete-btn" onclick="deleteTask(${task.id})">Excluir</button>
                    </div>
                `;
                if (task.completed_at) {
                    listItem.classList.add('completed');
                }
                taskList.appendChild(listItem);
            });
        });
}

// Function to format date
function formatDate(isoDate) {
    const date = new Date(isoDate);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Function to add a new task
function addTask() {
    const title = document.getElementById('taskTitle').value;
    const description = document.getElementById('taskDescription').value;
    const userSelect = document.getElementById('taskUser');
    const userId = userSelect.value;
    const datePicker = document.getElementById('datePicker');
    const dueDate = datePicker.value;
    const recurrenceDays = document.getElementById('recurrenceDays').value;

    fetch('/add_task', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title: title,
            description: description,
            user_id: userId,
            due_date: dueDate,
            recurrence_days: recurrenceDays
        })
    }).then(response => {
        if (response.ok) {
            loadTasks();
            document.getElementById('taskTitle').value = '';
            document.getElementById('taskDescription').value = '';
            document.getElementById('recurrenceDays').value = '';
        }
    });
}

// Function to add a new user
function addUser() {
    const name = document.getElementById('userName').value;
    fetch('/add_user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name
        })
    }).then(response => {
        if (response.ok) {
            loadUsers();
            document.getElementById('userName').value = '';
        }
    });
}

// Function to load users from the server
function loadUsers() {
    fetch('/get_users')
        .then(response => response.json())
        .then(users => {
            const userSelect = document.getElementById('taskUser');
            const editUserSelect = document.getElementById('editTaskUser');
            userSelect.innerHTML = '<option value="">Selecione um usuário</option>';
            editUserSelect.innerHTML = '<option value="">Selecione um usuário</option>';
            users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.text = user.name;
                userSelect.appendChild(option);
                const editOption = document.createElement('option');
                editOption.value = user.id;
                editOption.text = user.name;
                editUserSelect.appendChild(editOption);
            });
        });
}

// Function to mark a task as complete
function completeTask(taskId) {
    fetch(`/complete_task/${taskId}`, {
        method: 'POST'
    }).then(response => {
        if (response.ok) {
            loadTasks();
        }
    });
}

// Function to open the edit modal
function openEditModal(taskId) {
    fetch(`/get_task/${taskId}`)
        .then(response => response.json())
        .then(task => {
            document.getElementById('editTaskId').value = task.id;
            document.getElementById('editTaskTitle').value = task.title;
            document.getElementById('editTaskDescription').value = task.description;
            document.getElementById('editTaskUser').value = task.user_id;
            document.getElementById('editTaskDueDate').value = task.due_date ? task.due_date.split('T')[0] : '';
            document.getElementById('editModal').style.display = 'block';
        });
}

// Function to save the edited task
function saveTask() {
    const taskId = document.getElementById('editTaskId').value;
    const title = document.getElementById('editTaskTitle').value;
    const description = document.getElementById('editTaskDescription').value;
    const userSelect = document.getElementById('editTaskUser');
    const userId = userSelect.value;
    const dueDate = document.getElementById('editTaskDueDate').value;

    fetch(`/edit_task/${taskId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title: title,
            description: description,
            user_id: userId,
            due_date: dueDate
        })
    }).then(response => {
        if (response.ok) {
            closeModal();
            loadTasks();
        }
    });
}

// Function to delete a task
function deleteTask(taskId) {
    fetch(`/delete_task/${taskId}`, {
        method: 'POST'
    }).then(response => {
        if (response.ok) {
            loadTasks();
        }
    });
}

// Function to close the modal
function closeModal() {
    document.getElementById('editModal').style.display = 'none';
}

// Function to set the theme
function setTheme(theme) {
    document.body.classList.remove('default-theme', 'dark-theme', 'cute-theme');
    document.body.classList.add(theme + '-theme');
    localStorage.setItem('theme', theme);
}

// Load saved theme
const savedTheme = localStorage.getItem('theme');
if (savedTheme) {
    setTheme(savedTheme);
}
