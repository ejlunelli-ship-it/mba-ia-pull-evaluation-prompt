"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio
3. Salva localmente em prompts/bug_to_user_story_v1.yml

DICAS DE IMPLEMENTAÇÃO:

- O pull é feito pelo cliente do LangSmith:

      from langsmith import Client
      client = Client()
      prompt = client.pull_prompt(
          "leonanluppi/bug_to_user_story_v1",
          dangerously_pull_public_prompt=True,
      )

- O parâmetro `dangerously_pull_public_prompt=True` é obrigatório sempre que o
  identificador tem dono explícito ("owner/nome"). O LangSmith bloqueia esse pull
  por padrão porque um prompt do Hub é um objeto LangChain serializado, que pode
  vir de terceiros. Aqui o prompt é o do desafio, então o risco é conhecido.

- O retorno é um ChatPromptTemplate. Para extrair o conteúdo das mensagens,
  use a serialização nativa do LangChain (`prompt.messages`, e o atributo
  `.prompt.template` de cada mensagem).

- Use `save_yaml` de utils.py para gravar o resultado no arquivo .yml.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
PROMPT_KEY = "bug_to_user_story_v1"
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v1.yml"


def extract_messages(prompt) -> dict:
    """
    Extrai o template de texto de cada mensagem do ChatPromptTemplate,
    separando system prompt e user prompt.
    """
    system_parts, user_parts = [], []

    for message in prompt.messages:
        template = getattr(getattr(message, "prompt", None), "template", None)
        if template is None:
            continue

        role = type(message).__name__
        if role.startswith("System"):
            system_parts.append(template)
        elif role.startswith("Human"):
            user_parts.append(template)

    return {
        "system_prompt": "\n\n".join(system_parts),
        "user_prompt": "\n\n".join(user_parts),
    }


def pull_prompts_from_langsmith():
    """
    Faz pull do prompt semente no LangSmith Hub e salva em YAML.

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        client = Client()
        print(f"Puxando prompt: {SOURCE_PROMPT}")

        # O prompt semente é público e de dono conhecido (desafio), então o
        # pull com owner explícito é liberado conscientemente.
        prompt = client.pull_prompt(SOURCE_PROMPT, dangerously_pull_public_prompt=True)
        messages = extract_messages(prompt)

        if not messages["system_prompt"] and not messages["user_prompt"]:
            print("❌ Prompt sem mensagens de texto reconhecíveis")
            return False

        data = {
            PROMPT_KEY: {
                "description": "Prompt para converter relatos de bugs em User Stories",
                **messages,
                "version": "v1",
                "source": SOURCE_PROMPT,
                "input_variables": list(prompt.input_variables),
                "tags": ["bug-analysis", "user-story", "product-management"],
            }
        }

        if not save_yaml(data, str(OUTPUT_PATH)):
            return False

        print(f"✓ Prompt salvo em: {OUTPUT_PATH}")
        print(f"  Variáveis de entrada: {', '.join(prompt.input_variables)}")
        return True

    except Exception as e:
        print(f"❌ Erro ao fazer pull do prompt: {e}")
        return False


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    return 0 if pull_prompts_from_langsmith() else 1


if __name__ == "__main__":
    sys.exit(main())
