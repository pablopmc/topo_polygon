from __future__ import annotations

from typing import Iterable, List, Tuple

from core.calculations.engine import compensacao_angular, decimal_para_dms, dms_para_graus as dms_para_decimal, soma_angular

DMS = Tuple[int, int, float]