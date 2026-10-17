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

PROMPT_FILE = str(Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml")
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt():
    """Conteúdo da chave raiz do prompt v2."""
    return load_prompts(PROMPT_FILE)[PROMPT_KEY]


def full_text(prompt: dict) -> str:
    return prompt.get("system_prompt", "") + "\n" + prompt.get("user_prompt", "")


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt
        assert prompt["system_prompt"].strip(), "system_prompt está vazio"

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system = prompt["system_prompt"]
        assert re.search(r"Você é (um|uma)\s+\w+", system), "Nenhuma persona ('Você é um ...') encontrada"
        assert "Product Manager" in system

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system = prompt["system_prompt"]
        assert "Como um" in system and "eu quero" in system and "para que" in system, \
            "Formato 'Como um ... eu quero ... para que ...' não encontrado"
        assert "Critérios de Aceitação" in system
        assert "Markdown" in system

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system = prompt["system_prompt"]
        assert len(re.findall(r"Exemplo \d", system)) >= 2, "Menos de 2 exemplos few-shot"
        assert len(re.findall(r"^\s*Entrada:", system, re.MULTILINE)) >= 2, "Faltam blocos 'Entrada:'"
        assert len(re.findall(r"^\s*Saída:", system, re.MULTILINE)) >= 2, "Faltam blocos 'Saída:'"

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        assert "[TODO]" not in full_text(prompt).upper()
        assert not re.search(r"\bTODO\b", full_text(prompt))

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied", [])
        assert len(techniques) >= 2, f"Mínimo de 2 técnicas, encontradas: {len(techniques)}"

    def test_prompt_structure_is_valid(self, prompt):
        """Extra: a estrutura passa na validação do projeto e a variável fica só no user prompt."""
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, errors
        assert "{bug_report}" in prompt["user_prompt"]
        assert "{bug_report}" not in prompt["system_prompt"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
