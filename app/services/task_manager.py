from typing import List

class Task:
    def __init__(self, id, porcentage, status):
        self.id = id
        self.porcentage = porcentage
        self.status = status

class TaskManager:
    def __init__(self):
        self.tasks: List[Task] = []

    def add_task(self, task):
        self.tasks.append(task)

    def remove_task(self, task):
        self.tasks.remove(task)

    def update_task_porcentage(self, id, task_porcentage):
        for task in self.tasks:
            if task.id == id:
                task.porcentage = task_porcentage
                return task
        return None

    def update_task_status(self, id, success:bool):
        for task in self.tasks:
            if task.id == id:
                task.status = "completed" if success else "failed"
                return task
        return None

    def get_tasks(self):
        return self.tasks
    
    def get_task(self, task_id):
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

task_manager = TaskManager()