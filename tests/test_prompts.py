"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


@pytest.fixture(scope="module")
def prompt_data():
    data = load_prompts(str(PROMPT_FILE))
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE.name}"
    return data[PROMPT_KEY]


@pytest.fixture(scope="module")
def system_prompt(prompt_data):
    return prompt_data.get("system_prompt") or ""


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data
        assert prompt_data["system_prompt"].strip()

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert re.search(r"Você é (um|uma) .+", system_prompt), "Persona não definida"
        assert re.search(r"Product (Owner|Manager)", system_prompt)

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        text = system_prompt.lower()
        assert "markdown" in text or "user story" in text
        for part in ("como um", "eu quero", "para que"):
            assert part in text, f"Formato de User Story sem '{part}'"
        for part in ("dado que", "quando", "então"):
            assert part in text, f"Critérios de aceitação sem '{part}'"

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        examples = re.findall(r"^## Exemplo \d", system_prompt, flags=re.MULTILINE)
        assert len(examples) >= 2, "São esperados pelo menos 2 exemplos"
        assert system_prompt.count("Relato de bug:") >= len(examples)
        assert system_prompt.count("Resposta:") >= len(examples)

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        content = PROMPT_FILE.read_text(encoding="utf-8")
        assert "[TODO]" not in content
        assert "TODO" not in prompt_data.get("system_prompt", "")
        assert "TODO" not in prompt_data.get("user_prompt", "")

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt_data.get("techniques_applied", [])
        assert len(techniques) >= 2
        assert "Few-shot Learning" in techniques, "Few-shot é obrigatório"

    def test_prompt_structure_is_valid(self, prompt_data):
        """Valida a estrutura com o helper do projeto e a variável {bug_report}."""
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, errors
        assert "{bug_report}" in prompt_data["user_prompt"]
        assert "{bug_report}" not in prompt_data["system_prompt"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])