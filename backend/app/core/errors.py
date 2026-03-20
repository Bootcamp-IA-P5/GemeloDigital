class AppError(Exception):
    """
    Excepción personalizada para errores controlados de la aplicación.
    Será capturada por el manejador global de excepciones en main.py.
    """
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
