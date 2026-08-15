/**
 * Celery Task Management for Video Processing
 * Handles async task submission and progress tracking
 */

class TaskManager {
    constructor() {
        this.activeTasks = new Map();
        this.pollInterval = 2000; // Poll every 2 seconds
    }

    /**
     * Submit a video processing task
     */
    async submitVideoTask(formData, operation) {
        try {
            const response = await fetch('/api/process-video-async', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.trackTask(result.task_id, operation);
                return result;
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Task submission failed:', error);
            throw error;
        }
    }

    /**
     * Submit a video merge task
     */
    async submitMergeTask(formData) {
        try {
            const response = await fetch('/api/merge-videos-async', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.trackTask(result.task_id, 'merge');
                return result;
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Merge task submission failed:', error);
            throw error;
        }
    }

    /**
     * Submit a YouTube merge task
     */
    async submitYouTubeMergeTask(formData) {
        try {
            const response = await fetch('/api/youtube-merge-async', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.trackTask(result.task_id, 'youtube_merge');
                return result;
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('YouTube merge task submission failed:', error);
            throw error;
        }
    }

    /**
     * Track a task and poll for updates
     */
    trackTask(taskId, operation) {
        const taskInfo = {
            id: taskId,
            operation: operation,
            startTime: Date.now(),
            status: 'PENDING'
        };

        this.activeTasks.set(taskId, taskInfo);
        this.pollTaskStatus(taskId);
        this.updateUI(taskId, taskInfo);
    }

    /**
     * Poll task status
     */
    async pollTaskStatus(taskId) {
        const pollTask = async () => {
            try {
                const response = await fetch(`/api/task-status/${taskId}`);
                const status = await response.json();

                const taskInfo = this.activeTasks.get(taskId);
                if (!taskInfo) return; // Task was cancelled or removed

                taskInfo.status = status.state;
                taskInfo.progress = status.current || 0;
                taskInfo.total = status.total || 100;
                taskInfo.message = status.status || 'Processing...';

                this.updateUI(taskId, taskInfo);

                if (status.state === 'SUCCESS') {
                    taskInfo.result = status.result;
                    this.onTaskComplete(taskId, taskInfo);
                    this.activeTasks.delete(taskId);
                } else if (status.state === 'FAILURE') {
                    taskInfo.error = status.error;
                    this.onTaskError(taskId, taskInfo);
                    this.activeTasks.delete(taskId);
                } else if (status.state === 'PROGRESS' || status.state === 'PENDING') {
                    // Continue polling
                    setTimeout(pollTask, this.pollInterval);
                }
            } catch (error) {
                console.error('Error polling task status:', error);
                const taskInfo = this.activeTasks.get(taskId);
                if (taskInfo) {
                    this.onTaskError(taskId, { ...taskInfo, error: error.message });
                    this.activeTasks.delete(taskId);
                }
            }
        };

        pollTask();
    }

    /**
     * Update UI with task progress
     */
    updateUI(taskId, taskInfo) {
        const progressContainer = document.getElementById('task-progress');
        if (!progressContainer) return;

        let taskElement = document.getElementById(`task-${taskId}`);
        
        if (!taskElement) {
            taskElement = document.createElement('div');
            taskElement.id = `task-${taskId}`;
            taskElement.className = 'task-progress-item';
            progressContainer.appendChild(taskElement);
        }

        const progressPercent = Math.round((taskInfo.progress / taskInfo.total) * 100);
        
        taskElement.innerHTML = `
            <div class="task-header">
                <span class="task-operation">${taskInfo.operation.toUpperCase()}</span>
                <span class="task-status">${taskInfo.status}</span>
                <button class="btn btn-sm btn-danger" onclick="taskManager.cancelTask('${taskId}')">Cancel</button>
            </div>
            <div class="progress mb-2">
                <div class="progress-bar ${this.getProgressBarClass(taskInfo.status)}" 
                     role="progressbar" 
                     style="width: ${progressPercent}%"
                     aria-valuenow="${progressPercent}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                    ${progressPercent}%
                </div>
            </div>
            <div class="task-message">${taskInfo.message || 'Processing...'}</div>
            <div class="task-time">Started: ${new Date(taskInfo.startTime).toLocaleTimeString()}</div>
        `;
    }

    /**
     * Get progress bar CSS class based on status
     */
    getProgressBarClass(status) {
        switch (status) {
            case 'SUCCESS': return 'bg-success';
            case 'FAILURE': return 'bg-danger';
            case 'PROGRESS': return 'bg-primary progress-bar-animated progress-bar-striped';
            default: return 'bg-secondary';
        }
    }

    /**
     * Handle task completion
     */
    onTaskComplete(taskId, taskInfo) {
        console.log('Task completed:', taskInfo);
        
        // Show success notification
        this.showNotification('success', `${taskInfo.operation} completed successfully!`);
        
        // Update UI with download link
        if (taskInfo.result && taskInfo.result.output_file) {
            this.showDownloadLink(taskInfo.result.output_file);
        }

        // Remove task element after delay
        setTimeout(() => {
            const taskElement = document.getElementById(`task-${taskId}`);
            if (taskElement) {
                taskElement.remove();
            }
        }, 5000);
    }

    /**
     * Handle task error
     */
    onTaskError(taskId, taskInfo) {
        console.error('Task failed:', taskInfo);
        
        // Show error notification
        this.showNotification('error', `${taskInfo.operation} failed: ${taskInfo.error}`);

        // Update UI to show error
        const taskElement = document.getElementById(`task-${taskId}`);
        if (taskElement) {
            taskElement.classList.add('task-error');
        }
    }

    /**
     * Cancel a task
     */
    async cancelTask(taskId) {
        try {
            const response = await fetch(`/api/cancel-task/${taskId}`, {
                method: 'POST'
            });

            const result = await response.json();
            
            if (result.success) {
                this.activeTasks.delete(taskId);
                const taskElement = document.getElementById(`task-${taskId}`);
                if (taskElement) {
                    taskElement.remove();
                }
                this.showNotification('info', 'Task cancelled');
            }
        } catch (error) {
            console.error('Error cancelling task:', error);
        }
    }

    /**
     * Show notification
     */
    showNotification(type, message) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to notifications container
        const container = document.getElementById('notifications') || document.body;
        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    /**
     * Show download link
     */
    showDownloadLink(filename) {
        const outputPreview = document.getElementById('output-preview');
        if (outputPreview) {
            outputPreview.innerHTML = `
                <div class="alert alert-success">
                    <h5>✅ Processing Complete!</h5>
                    <p>Your video has been processed successfully.</p>
                    <a href="/output/${filename}" class="btn btn-success" download>
                        📥 Download Processed Video
                    </a>
                </div>
            `;
        }
    }

    /**
     * Get queue status
     */
    async getQueueStatus() {
        try {
            const response = await fetch('/api/queue-status');
            return await response.json();
        } catch (error) {
            console.error('Error getting queue status:', error);
            return null;
        }
    }
}

// Initialize task manager
const taskManager = new TaskManager();

// Add progress container to page if it doesn't exist
document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('task-progress')) {
        const progressContainer = document.createElement('div');
        progressContainer.id = 'task-progress';
        progressContainer.className = 'task-progress-container mt-3';
        
        // Insert after the main form or at the beginning of main content
        const mainContent = document.querySelector('.container') || document.body;
        mainContent.insertBefore(progressContainer, mainContent.firstChild);
    }

    if (!document.getElementById('notifications')) {
        const notificationsContainer = document.createElement('div');
        notificationsContainer.id = 'notifications';
        notificationsContainer.className = 'notifications-container';
        document.body.appendChild(notificationsContainer);
    }
});

// Example usage functions
function processVideoAsync(operation) {
    const form = document.getElementById('video-form');
    const formData = new FormData(form);
    formData.append('operation', operation);
    
    taskManager.submitVideoTask(formData, operation)
        .then(result => {
            console.log('Task submitted:', result);
        })
        .catch(error => {
            taskManager.showNotification('error', `Failed to submit task: ${error.message}`);
        });
}

function mergeVideosAsync() {
    const form = document.getElementById('merge-form');
    const formData = new FormData(form);
    
    taskManager.submitMergeTask(formData)
        .then(result => {
            console.log('Merge task submitted:', result);
        })
        .catch(error => {
            taskManager.showNotification('error', `Failed to submit merge task: ${error.message}`);
        });
}

function mergeWithYouTubeAsync() {
    const form = document.getElementById('youtube-form');
    const formData = new FormData(form);
    
    taskManager.submitYouTubeMergeTask(formData)
        .then(result => {
            console.log('YouTube merge task submitted:', result);
        })
        .catch(error => {
            taskManager.showNotification('error', `Failed to submit YouTube merge task: ${error.message}`);
        });
}