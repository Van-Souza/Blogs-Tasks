// Toast notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    container.appendChild(toast);
    document.body.appendChild(container);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        container.remove();
    });
}

// Confirm action
function confirmAction(message) {
    return confirm(message);
}

// Format date
function formatDate(date) {
    return new Date(date).toLocaleDateString('pt-BR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    });
}

// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
});
document.addEventListener('DOMContentLoaded', function() {
    // Seleciona todos os elementos <select> com a classe .status-select
    document.querySelectorAll('.status-select').forEach(select => {
        // Adiciona um event listener para o evento 'change'
        select.addEventListener('change', function() {
            const taskId = this.dataset.taskId; // Obtém o ID da tarefa
            const status = this.value; // Obtém o novo status selecionado

            // Encontra o <td> pai que contém o <select>
            const td = this.closest('td');

            if (td) {
                // Remove todas as classes de status
                td.classList.remove('status-pending', 'status-in-progress', 'status-completed');

                // Adiciona a nova classe com base no status selecionado
                if (status === 'pending') {
                    td.classList.add('status-pending');
                } else if (status === 'in_progress') {
                    td.classList.add('status-in-progress');
                } else if (status === 'completed') {
                    td.classList.add('status-completed');
                }
            }

            // Envia a atualização para o servidor
            fetch(`/task/update/${taskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ status: status })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    showToast('Falha ao atualizar o status da tarefa', 'danger');
                    location.reload(); // Recarrega a página em caso de erro
                } else {
                    showToast('Status da tarefa atualizado com sucesso', 'success');
                }
            });
        });
    });
});

// Código do chat
document.querySelectorAll('.btn-chat').forEach(button => {
    button.addEventListener('click', function() {
        const taskId = this.dataset.taskId;
        
        // Marca como lido no servidor
        fetch(`/task/mark_chat_read/${taskId}`, {
            method: 'POST'
        }).then(response => response.json())
          .then(data => {
              // Remove o indicador apenas se não houver novas mensagens
              if (data.success && !data.hasNewMessages) {
                  const indicator = this.querySelector('.position-absolute');
                  if (indicator) {
                      indicator.remove();
                  }
              }
          });

        // Carrega os comentários
        fetch(`/task/comments/${taskId}`)
            .then(response => response.json())
            .then(comments => {
                const commentsHtml = comments.map(comment => `
                    <div class="comment mb-2">
                        <strong>${comment.user}</strong>
                        <small class="text-muted">${comment.created_at}</small>
                        <div>${comment.message}</div>
                    </div>
                `).join('');

                // Mostra o modal com os comentários
                const modal = new bootstrap.Modal(document.getElementById('chatModal'));
                document.getElementById('chatComments').innerHTML = commentsHtml;
                document.getElementById('commentTaskId').value = taskId;
                modal.show();
            });
    });
});

// Adicionar novo comentário
document.getElementById('addComment').addEventListener('click', function() {
    const taskId = document.getElementById('commentTaskId').value;
    const message = document.getElementById('commentMessage').value;

    if (!message.trim()) {
        alert('Por favor, digite uma mensagem');
        return;
    }

    fetch(`/task/comment/${taskId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: message })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const comment = data.comment;
            const commentHtml = `
                <div class="comment mb-2">
                    <strong>${comment.user}</strong>
                    <small class="text-muted">${comment.created_at}</small>
                    <div>${comment.message}</div>
                </div>
            `;
            document.getElementById('chatComments').insertAdjacentHTML('beforeend', commentHtml);
            document.getElementById('commentMessage').value = '';
        } else {
            alert('Erro ao adicionar comentário');
        }
    });
});