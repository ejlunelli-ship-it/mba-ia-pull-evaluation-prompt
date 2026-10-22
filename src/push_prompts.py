"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

DICAS DE IMPLEMENTAÇÃO:

- O push é feito pelo cliente do LangSmith:

      from langsmith import Client
      from langchain_core.prompts import ChatPromptTemplate

      client = Client()
      prompt = ChatPromptTemplate.from_messages([
          ("system", system_prompt),
          ("user", user_prompt),
      ])
      url = client.push_prompt(
          f"{username}/bug_to_user_story_v2",
          object=prompt,
          is_public=True,
          description="...",
          tags=[...],
      )

- `username` vem de USERNAME_LANGSMITH_HUB no .env e precisa ser o seu handle
  do Hub. Se você ainda não tem um handle, veja as instruções no .env.example.

- A variável do template precisa ser {bug_report}, que é a chave de entrada
  usada no dataset de avaliação.

- Use `load_yaml` de utils.py para ler o arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()


PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def build_readme(prompt_data: dict) -> str:
    """Monta o README exibido no Hub com descrição e técnicas aplicadas."""
    techniques = "\n".join(f"- {t}" for t in prompt_data.get("techniques_applied", []))
    return (
        f"# {PROMPT_KEY}\n\n"
        f"{prompt_data.get('description', '')}\n\n"
        f"**Versão:** {prompt_data.get('version', '')}\n\n"
        f"## Técnicas aplicadas\n{techniques}\n"
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        client = Client()
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt_data["system_prompt"]),
            ("user", prompt_data["user_prompt"]),
        ])

        techniques = prompt_data.get("techniques_applied", [])
        tags = list(dict.fromkeys(
            [*prompt_data.get("tags", []), prompt_data.get("version", "")] + techniques
        ))

        url = client.push_prompt(
            prompt_name,
            object=prompt,
            is_public=True,
            description=prompt_data.get("description", ""),
            readme=build_readme(prompt_data),
            tags=[t for t in tags if t],
        )

        print(f"✓ Push realizado: {prompt_name}")
        print(f"  {url}")
        return True

    except Exception as e:
        message = str(e)
        # O Hub recusa commits idênticos ao último: o prompt publicado já está atualizado
        if "Nothing to commit" in message:
            print(f"✓ {prompt_name} já está atualizado no Hub (nada a commitar)")
            return True
        print(f"❌ Erro ao fazer push de {prompt_name}: {message}")
        return False


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    is_valid, errors = validate_prompt_structure(prompt_data)

    user_prompt = (prompt_data.get("user_prompt") or "").strip()
    system_prompt = (prompt_data.get("system_prompt") or "").strip()

    if not user_prompt:
        errors.append("user_prompt está vazio")
    elif "{bug_report}" not in user_prompt:
        errors.append("user_prompt deve conter a variável {bug_report}")

    if "{bug_report}" in system_prompt:
        errors.append("{bug_report} deve ficar apenas no user_prompt")

    # O template precisa ter apenas {bug_report} como variável de entrada
    if not errors:
        try:
            variables = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", user_prompt),
            ]).input_variables
            if variables != ["bug_report"]:
                errors.append(f"Variáveis inesperadas no template: {variables}")
        except Exception as e:
            errors.append(f"Template inválido: {e}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(str(PROMPT_FILE))
    if not data or PROMPT_KEY not in data:
        print(f"❌ Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE}")
        return 1

    prompt_data = data[PROMPT_KEY]
    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1
    print("✓ Prompt validado")

    username = os.getenv("USERNAME_LANGSMITH_HUB")
    prompt_name = f"{username}/{PROMPT_KEY}"

    return 0 if push_prompt_to_langsmith(prompt_name, prompt_data) else 1


if __name__ == "__main__":
    sys.exit(main())
