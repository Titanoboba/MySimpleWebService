document.addEventListener('DOMContentLoaded', function() {
    const todoList = document.getElementById('todo-list');
    const inProgressList = document.getElementById('in-progress-list');
    const doneList = document.getElementById('done-list');
    const addBtn = document.getElementById('add-task-btn');
    const titleInput = document.getElementById('task-title');

    if (!todoList || !inProgressList || !doneList) {
        console.error('Контейнеры не найдены');
        return;
    }

    let draggedCard = null;

    function loadTasks() {
        todoList.innerHTML = '';
        inProgressList.innerHTML = '';
        doneList.innerHTML = '';

        fetch('/api/tasks')
            .then(res => res.json())
            .then(tasks => {
                tasks.forEach(task => {
                    const card = createCard(task);
                    const status = (task.status || '').toLowerCase();
                    if (status === 'todo') todoList.appendChild(card);
                    else if (status === 'in_progress') inProgressList.appendChild(card);
                    else if (status === 'done') doneList.appendChild(card);
                    else todoList.appendChild(card); // fallback
                });
            })
            .catch(err => console.error('Ошибка загрузки:', err));
    }

    function createCard(task) {
        const card = document.createElement('div');
        card.className = 'task-card';
        card.draggable = true;
        card.dataset.id = task.id;
        card.dataset.status = (task.status || '').toLowerCase();

        const text = document.createElement('span');
        text.textContent = task.title || 'Без названия';

        const deleteBtn = document.createElement('span');
        deleteBtn.className = 'task-delete';
        deleteBtn.textContent = '×';
        deleteBtn.title = 'Удалить задачу';
        deleteBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // чтобы не вызвать перетаскивание
            deleteTask(task.id, card);
        });

        card.appendChild(text);
        card.appendChild(deleteBtn);

        card.addEventListener('dragstart', handleDragStart);
        card.addEventListener('dragend', handleDragEnd);

        return card;
    }

    function deleteTask(taskId, cardElement) {
        fetch(`/api/tasks/${taskId}`, {
            method: 'DELETE'
        })
        .then(response => {
            if (!response.ok) throw new Error('Ошибка удаления');
            // Удаляем карточку из DOM
            cardElement.remove();
            console.log(`Задача ${taskId} удалена`);
        })
        .catch(err => {
            console.error('Ошибка удаления задачи:', err);
            alert('Не удалось удалить задачу');
        });
    }

    function handleDragStart(e) {
        draggedCard = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', this.dataset.id);
    }

    function handleDragEnd(e) {
        this.classList.remove('dragging');
    }

    function setupDropZone(listElement, targetStatus) {
        listElement.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'move';
        });

        listElement.addEventListener('drop', (e) => {
            e.preventDefault();
            if (!draggedCard) return;
            if (draggedCard.parentElement === listElement) {
                draggedCard = null;
                return;
            }

            const taskId = draggedCard.dataset.id;
            fetch(`/api/tasks/${taskId}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: targetStatus })
            })
            .then(response => {
                if (!response.ok) throw new Error('Ошибка обновления статуса');
                return response.json();
            })
            .then(() => {
                listElement.appendChild(draggedCard);
                draggedCard.dataset.status = targetStatus;
                draggedCard = null;
            })
            .catch(err => {
                console.error(err);
                loadTasks();
                draggedCard = null;
            });
        });
    }

    setupDropZone(todoList, 'todo');
    setupDropZone(inProgressList, 'in_progress');
    setupDropZone(doneList, 'done');

    addBtn.addEventListener('click', function() {
        const title = titleInput.value.trim();
        if (!title) {
            alert('Введите название задачи');
            return;
        }
        fetch('/api/tasks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: title })
        })
        .then(response => response.json())
        .then(task => {
            titleInput.value = '';
            const card = createCard(task);
            todoList.appendChild(card);
        })
        .catch(err => console.error(err));
    });

    loadTasks();
});