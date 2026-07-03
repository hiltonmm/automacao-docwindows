import json
import os

CONFIG_FILE = "config.json"

def carregar_config():
    if not os.path.exists(CONFIG_FILE):
        return {"validar_xsd": True, "imprimir_relatorio": True}
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def salvar_config(chave, valor):
    config = carregar_config()
    config[chave] = valor
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)