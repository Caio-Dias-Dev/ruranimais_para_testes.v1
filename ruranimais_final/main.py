"""Ruranimais - a rede social de quem cuida (versão console).

Execute com:  python main.py
"""
import time

import db
from cadastro import cadastrar_usuario, login, menu_perfil
from enquetes import menu_enquetes
from gamificacao import ranking, visualizar_gamificacao
from imagens import menu_imagens
from mensagens import contar_nao_lidas, menu_mensagens
from publicacoes import menu_publicacoes
from utils import AMARELO, VERDE, console, erro, esc, menu


def menu_gamificacao(usuario):
    while True:
        opcao = menu("GAMIFICAÇÃO", [("1", "Meus pontos e conquistas"), ("2", "Ranking"), ("0", "Voltar")], "🏆")
        if opcao == "1":
            visualizar_gamificacao(usuario)
        elif opcao == "2":
            ranking()
        elif opcao == "0":
            return
        else:
            erro("Opção inválida!")


def menu_principal(usuario):
    """Menu após o login. Termina quando o usuário sai da conta (ou a exclui)."""
    while True:
        nao_lidas = contar_nao_lidas(usuario)
        novas = f" ({nao_lidas} não lida(s))" if nao_lidas else ""
        opcao = menu(
            f"OLÁ, {esc(usuario['nome'].split()[0].upper())}!",
            [("1", "Publicações"), ("2", "Enquetes"), ("3", f"Mensagens{novas}"),
             ("4", "Imagens"), ("5", "Gamificação"), ("6", "Meu perfil"), ("0", "Sair da conta")],
        )
        if opcao == "1":
            menu_publicacoes(usuario)
        elif opcao == "2":
            menu_enquetes(usuario)
        elif opcao == "3":
            menu_mensagens(usuario)
        elif opcao == "4":
            menu_imagens(usuario)
        elif opcao == "5":
            menu_gamificacao(usuario)
        elif opcao == "6":
            if menu_perfil(usuario):  # conta excluída
                return
        elif opcao == "0":
            console.print(f"\n[{AMARELO}]Você saiu da sua conta.[/]")
            return
        else:
            erro("Opção inválida!")


def menu_inicial():
    while True:
        console.print(f"\n🐾 [bold {VERDE}]RURANIMAIS[/] 💚")
        console.print("A rede social de quem cuida.")
        opcao = menu("MENU INICIAL", [("1", "Cadastrar usuário"), ("2", "Login"), ("3", "Sair")])
        if opcao == "1":
            cadastrar_usuario()
        elif opcao == "2":
            usuario = login()
            if usuario:
                menu_principal(usuario)
        elif opcao == "3":
            console.print("Fechando programa...")
            time.sleep(1)
            console.print(f"[{AMARELO}]Você encerrou sua sessão no Ruranimais. Até logo![/]")
            return
        else:
            erro("Opção inválida!")


def main():
    db.iniciar_banco()
    try:
        menu_inicial()
    except (KeyboardInterrupt, EOFError):
        console.print(f"\n\n[{AMARELO}]Programa encerrado. Até logo![/]")


if __name__ == "__main__":
    main()
