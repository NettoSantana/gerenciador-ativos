from gerenciador_ativos.models import Ativo


def calcular_horas_motor(ativo: Ativo) -> float:
    """
    Fonte única da verdade para horas de uso do motor.
    """
    horas_offset = ativo.horas_offset or 0.0
    horas_sistema = ativo.horas_sistema or 0.0
    return round(horas_offset + horas_sistema, 1)
