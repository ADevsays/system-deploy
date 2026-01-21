import threading
import time
import logging
from typing import Callable, Any
from app.services.task_manager import task_manager

logger = logging.getLogger(__name__)

class ProcessWrapper:
    @staticmethod
    def run(task_id: str, target_func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta una función target mientras simula progreso en una tarea.
        """
        stop_progress = threading.Event()

        def simulate_progress():
            current_prog = 5
            # Subimos hasta 90%
            while not stop_progress.is_set() and current_prog < 90:
                time.sleep(0.5) 
                current_prog += 2
                task_manager.update_task_porcentage(task_id, current_prog)

        # Iniciar simulación en background
        progress_thread = threading.Thread(target=simulate_progress)
        progress_thread.start()

        try:
            # Ejecutar función real (bloqueante)
            result = target_func(*args, **kwargs)
            
            # Al terminar éxito
            stop_progress.set()
            progress_thread.join()
            
            task_manager.update_task_porcentage(task_id, 100)
            task_manager.update_task_status(task_id, True)
            
            return result

        except Exception as e:
            # Al fallar
            stop_progress.set()
            progress_thread.join()
            
            logger.error(f"Error in process wrapper for task {task_id}: {e}")
            task_manager.update_task_status(task_id, False)
            raise e
