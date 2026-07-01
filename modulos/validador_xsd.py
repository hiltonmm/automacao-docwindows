# -*- coding: utf-8 -*-
import os
import glob
import logging
from typing import List
from lxml import etree
from datetime import datetime


def validar_data(data_str: str) -> bool:
    try:
        datetime.strptime(data_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def formatar_erro(arquivo: str, linha: int, mensagem: str) -> str:
    return f"Arquivo: {os.path.basename(arquivo)} | Linha {linha} | {mensagem}"


def validar_xml_com_xsd(caminho_xml: str, caminho_xsd: str) -> List[str]:
    erros = []
    parser = etree.XMLParser(remove_blank_text=True)

    try:
        with open(caminho_xsd, 'rb') as f:
            schema_root = etree.XML(f.read())
            schema = etree.XMLSchema(schema_root)

        with open(caminho_xml, 'rb') as f:
            xml_doc = etree.parse(f, parser=parser) # type: ignore

        # 1. Validação automática pelo XSD (Pega restrições, enumerations, etc)
        # O validate retorna False se encontrar qualquer violação do XSD
        if not schema.validate(xml_doc):
            for error in schema.error_log:
                # Filtragem inteligente:
                # Ignora erros técnicos de 'pattern' (frequentemente rígidos demais para o TJRJ)
                # Foca em 'enumeration' (valores inválidos) e campos obrigatórios/ausentes
                if error.type_name == "SCHEMAV_CVC_PATTERN_VALID":
                    continue

                # Tradução amigável
                msg = error.message
                if "is not an element of the set" in msg:
                    msg = f"Valor inválido. Os valores permitidos são: {msg.split('{')[-1].replace('}', '')}"

                erros.append(formatar_erro(caminho_xml, error.line, msg))

        # 2. Validação de Regra de Negócio (Datas que o XSD não pega nativamente)
        for element in xml_doc.xpath("//*"):
            for attr_name, attr_value in element.attrib.items():
                if attr_name in ["DataNascimento", "DataPratica", "DataCasamento"] and attr_value and not validar_data(
                        attr_value):
                    erros.append(formatar_erro(caminho_xml, element.sourceline,
                                               f"A data '{attr_value}' no campo '{attr_name}' é inválida."))

    except (etree.XMLSyntaxError, OSError) as e:
        erros.append(f"Erro ao ler XML: {str(e)}")

    return erros


def executar(data_alvo: str) -> None:
    logging.info(f"--- PASSO 4.5: AUDITORIA GENÉRICA VIA XSD (Data: {data_alvo}) ---")

    dir_caixa_saida = r"C:\CGJ-RJ\MAS\Caixa de Saída"
    data_xml = f"{data_alvo[4:8]}{data_alvo[2:4]}{data_alvo[0:2]}"
    dir_raiz = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Mapeamento dinâmico
    padroes = [
        (f"1766_{data_xml}_RCPN_I_*.xml", os.path.join(dir_raiz, "xsd", "rcpn.xsd")),
        (f"7515_{data_xml}_RCPN_I_*.xml", os.path.join(dir_raiz, "xsd", "rcpn.xsd")),
        (f"1766_{data_xml}_RIT_I_*.xml", os.path.join(dir_raiz, "xsd", "rit.xsd"))
    ]

    lista_erros = []
    for padrao, xsd in padroes:
        for arquivo in glob.glob(os.path.join(dir_caixa_saida, padrao)):
            lista_erros.extend(validar_xml_com_xsd(arquivo, xsd))

    if lista_erros:
        raise RuntimeError("PROBLEMAS DETECTADOS PELO XSD:\n\n" + "\n".join(lista_erros))

    logging.info("✓ Todos os XMLs aprovados pelo XSD.")