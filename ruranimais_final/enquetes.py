"""Enquetes: criação, votação (um voto por usuário) e resultados."""
import sqlite3

import db
import gamificacao
from utils import (
    VERDE, aviso, confirmar, console, erro, esc, ler_inteiro, ler_texto, linha, menu, sucesso, titulo,
)

MIN_OPCOES, MAX_OPCOES = 2, 5


def criar_enquete(usuario):
    titulo("CRIAR ENQUETE", "📊")
    pergunta = ler_texto("Pergunta (Enter vazio cancela): ", obrigatorio=False, maximo=200)
    if pergunta is None:
        aviso("Enquete cancelada.")
        return
    opcoes = []
    while len(opcoes) < MAX_OPCOES:
        n = len(opcoes) + 1
        if n <= MIN_OPCOES:
            texto = ler_texto(f"Opção {n}: ", maximo=80)
        else:
            texto = ler_texto(f"Opção {n} (Enter para terminar): ", obrigatorio=False, maximo=80)
            if texto is None:
                break
        if texto.lower() in (o.lower() for o in opcoes):
            erro("Essa opção já foi adicionada.")
            continue
        opcoes.append(texto)
    with db.transacao() as con:
        cur = con.execute("INSERT INTO enquetes (usuario_id, pergunta) VALUES (?, ?)", (usuario["id"], pergunta))
        con.executemany(
            "INSERT INTO enquete_opcoes (enquete_id, texto) VALUES (?, ?)",
            [(cur.lastrowid, o) for o in opcoes],
        )
    sucesso("Enquete criada!")
    gamificacao.adicionar_pontos(usuario, "criar_enquete")


def _carregar_enquetes(enquete_id=None):
    sql = "SELECT e.id, e.pergunta, e.usuario_id, u.nome FROM enquetes e JOIN usuarios u ON u.id = e.usuario_id"
    parametros = ()
    if enquete_id is not None:
        sql += " WHERE e.id = ?"
        parametros = (enquete_id,)
    return db.consultar(sql + " ORDER BY e.id DESC LIMIT 20", parametros)


def listar_enquetes(usuario=None):
    titulo("ENQUETES", "📊")
    enquetes = _carregar_enquetes()
    if not enquetes:
        aviso("Nenhuma enquete encontrada.")
        return []
    for e in enquetes:
        linha()
        console.print(f"ID: {e['id']}  |  Autor: [bold]{esc(e['nome'])}[/]")
        console.print(f"Pergunta: {esc(e['pergunta'])}")
        meu_voto = None
        if usuario:
            r = db.consultar_um("SELECT opcao_id FROM votos WHERE enquete_id = ? AND usuario_id = ?",
                                (e["id"], usuario["id"]))
            meu_voto = r["opcao_id"] if r else None
        opcoes = db.consultar(
            "SELECT o.id, o.texto, (SELECT COUNT(*) FROM votos v WHERE v.opcao_id = o.id) AS votos "
            "FROM enquete_opcoes o WHERE o.enquete_id = ? ORDER BY o.id", (e["id"],))
        total = sum(o["votos"] for o in opcoes)
        for o in opcoes:
            pct = round(100 * o["votos"] / total) if total else 0
            marca = " ← seu voto" if o["id"] == meu_voto else ""
            console.print(f"- {esc(o['texto'])}: {o['votos']} voto(s) ({pct}%) [{VERDE}]{'█' * (pct // 10)}[/]{marca}")
    return enquetes


def votar_enquete(usuario):
    if not listar_enquetes(usuario):
        return
    numero = ler_inteiro("\nDigite o ID da enquete (Enter cancela): ")
    if numero is None:
        return
    enquete = _carregar_enquetes(numero)
    if not enquete:
        erro("Enquete inválida.")
        return
    if db.consultar_um("SELECT 1 FROM votos WHERE enquete_id = ? AND usuario_id = ?", (numero, usuario["id"])):
        erro("Você já votou nesta enquete.")
        return
    opcoes = db.consultar("SELECT id, texto FROM enquete_opcoes WHERE enquete_id = ? ORDER BY id", (numero,))
    for i, o in enumerate(opcoes, start=1):
        console.print(f"{i} - {esc(o['texto'])}")
    escolha = ler_inteiro("\nEscolha uma opção (Enter cancela): ")
    if escolha is None:
        return
    if not 1 <= escolha <= len(opcoes):
        erro("Opção inválida.")
        return
    try:
        with db.transacao() as con:
            con.execute("INSERT INTO votos (enquete_id, usuario_id, opcao_id) VALUES (?, ?, ?)",
                        (numero, usuario["id"], opcoes[escolha - 1]["id"]))
    except sqlite3.IntegrityError:
        erro("Você já votou nesta enquete.")
        return
    sucesso("Voto registrado!")
    gamificacao.adicionar_pontos(usuario, "votar")


def excluir_enquete(usuario):
    minhas = [e for e in _carregar_enquetes() if e["usuario_id"] == usuario["id"]]
    if not minhas:
        aviso("Você não criou nenhuma enquete.")
        return
    for e in minhas:
        console.print(f"{e['id']} - {esc(e['pergunta'])}")
    numero = ler_inteiro("\nID da enquete a excluir (Enter cancela): ")
    if numero is None:
        return
    if numero not in {e["id"] for e in minhas}:
        erro("Você só pode excluir as suas próprias enquetes.")
        return
    if not confirmar("Excluir esta enquete e seus votos?"):
        return
    with db.transacao() as con:
        con.execute("DELETE FROM enquetes WHERE id = ?", (numero,))
    sucesso("Enquete excluída.")


def menu_enquetes(usuario):
    while True:
        opcao = menu(
            "ENQUETES",
            [("1", "Ver enquetes e resultados"), ("2", "Criar enquete"), ("3", "Votar"),
             ("4", "Excluir uma enquete minha"), ("0", "Voltar")],
            "📊",
        )
        if opcao == "1":
            listar_enquetes(usuario)
        elif opcao == "2":
            criar_enquete(usuario)
        elif opcao == "3":
            votar_enquete(usuario)
        elif opcao == "4":
            excluir_enquete(usuario)
        elif opcao == "0":
            return
        else:
            erro("Opção inválida!")
