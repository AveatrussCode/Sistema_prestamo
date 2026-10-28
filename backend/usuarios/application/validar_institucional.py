"""Validación contra el sistema institucional de la UNSA."""

class ValidadorInstitucional:
    def verificar(self, tipo: str, correo: str, codigo: str) -> tuple[bool, str]:
        """Devuelve (es_valido, motivo_si_no_lo_es)."""
        
        if tipo == "Estudiante":
            return True, ""  # el estudiante solo depende del PDF
            
        # Para Profesor / Administrativo
        if not correo.endswith("@unsa.edu.pe"):
            return False, "El correo no pertenece al dominio institucional @unsa.edu.pe."
            
        return True, ""

validador_institucional = ValidadorInstitucional()