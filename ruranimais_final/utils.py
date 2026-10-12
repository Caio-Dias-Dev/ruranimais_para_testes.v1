"""Funções de interface compartilhadas (cores, entradas validadas, menus)."""
from getpass import getpass

from rich.console import Console
from rich.markup import escape

console = Console()

AMARELO = "#EEA103"
VERMELHO = "#D74013"
VERDE = "#719029"

esc = escape  # sempre use esc() em texto digitado por usuários


def titulo(texto, emoji="🐾"):
    console.print(f"\n[{VERMELHO}]{'=' * 40}[/]")
    console.print(f"{emoji} [bold {VERDE}]{texto}[/]")
    console.print(f"[{VERMELHO}]{'=' * 40}[/]")


def sucesso(msg):
    console.print(f"\n[{VERDE}]✅ {msg}[/]")


def erro(msg):
    console.print(f"\n[{VERMELHO}]❌ {msg}[/]")


def aviso(msg):
    console.print(f"\n[{AMARELO}]{msg}[/]")


def linha():
    console.print(f"[{VERDE}]{'-' * 40}[/]")


def ler_texto(prompt, obrigatorio=True, minimo=1, maximo=500):
    """Lê um texto. Se não for obrigatório, Enter em branco devolve None."""
    while True:
        valor = input(prompt).strip()
        if not valor:
            if not obrigatorio:
                return None
            erro("Este campo não pode ficar vazio.")
            continue
        if len(valor) < minimo:
            erro(f"Digite pelo menos {minimo} caracteres.")
            continue
        if len(valor) > maximo:
            erro(f"Digite no máximo {maximo} caracteres (você digitou {len(valor)}).")
            continue
        return valor


def ler_senha(prompt):
    return getpass(prompt)


def ler_inteiro(prompt):
    """Lê um número inteiro. Enter em branco ou valor inválido devolve None."""
    valor = input(prompt).strip()
    if not valor:
        return None
    try:
        return int(valor)
    except ValueError:
        erro("Digite apenas números.")
        return None


def confirmar(prompt):
    return input(f"{prompt} (s/n): ").strip().lower() in ("s", "sim")


def menu(titulo_menu, opcoes, emoji="🐾"):
    """Mostra um menu e devolve a tecla escolhida. opcoes = [(tecla, texto), ...]"""
    titulo(titulo_menu, emoji)
    for tecla, texto in opcoes:
        console.print(f"{tecla} - {texto}")
    return input("\nEscolha uma opção: ").strip()
