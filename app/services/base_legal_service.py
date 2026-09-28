import json
from pathlib import Path
from typing import Dict

_SEED = Path(__file__).resolve().parents[1] / "seed_data" / "base_legal_art225.json"


class BaseLegalService:
    def __init__(self):
        with _SEED.open("r", encoding="utf-8") as f:
            self._dados: Dict[str, dict] = json.load(f)

    def obter_amparo(self, categoria: str) -> dict:
        return self._dados.get(
            categoria,
            {
                "artigo": "Constituição Federal, Art. 225",
                "texto": (
                    "Todos têm direito ao meio ambiente ecologicamente "
                    "equilibrado, bem de uso comum do povo e essencial à "
                    "sadia qualidade de vida, impondo-se ao Poder Público e "
                    "à coletividade o dever de defendê-lo e preservá-lo para "
                    "as presentes e futuras gerações."
                ),
                "canais": [
                    "Linha Verde (INEA-RJ): 0800 285 2828",
                    "Guarda Ambiental do Rio de Janeiro",
                ],
            },
        )
