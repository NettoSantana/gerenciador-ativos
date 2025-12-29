from gerenciador_ativos.models import Ativo


def calcular_horas_motor(ativo: Ativo) -> float:
    """
    Cálculo oficial de horas de uso do motor.

    Regra:
    horas_motor = horas_offset + horas_sistema

    Essa função é a FONTE ÚNICA da verdade.
    """
    horas_offset = ativo.horas_offset or 0.0
    horas_sistema = ativo.horas_sistema or 0.0
    return round(horas_offset + horas_sistema, 1)
