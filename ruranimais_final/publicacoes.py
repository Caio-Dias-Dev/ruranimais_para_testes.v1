"""Postagens de texto, curtidas e comentários."""
import sqlite3

import db
import gamificacao
from utils import (
    VERDE, aviso, confirmar, console, erro, esc, ler_inteiro, ler_texto, linha, menu, sucesso, titulo,
)

LIMITE_FEED = 20


def criar_publicacao(usuario):
    titulo("NOVA PUBLICAÇÃO", "📝")
    texto = ler_texto("Digite sua publicação (Enter vazio cancela): ", obrigatorio=False, maximo=500)
    if texto is None:
        aviso("Publicação cancelada.")
        return
    with db.transacao() as con:
        con.execute("INSERT INTO publicacoes (usuario_id, texto) VALUES (?, ?)", (usuario["id"], texto))
    sucesso("Publicação criada!")
    gamificacao.adicionar_pontos(usuario, "publicar")


def listar_publicacoes(somente_do_usuario=None):
    titulo("PUBLICAÇÕES", "📰")
    sql = """
        SELECT p.id, p.texto, p.criado_em, u.nome,
               (SELECT COUNT(*) FROM curtidas c WHERE c.publicacao_id = p.id) AS curtidas,
               (SELECT COUNT(*) FROM comentarios m WHERE m.publicacao_id = p.id) AS comentarios
        FROM publicacoes p JOIN usuarios u ON u.id = p.usuario_id
    """
    parametros = ()
    if somente_do_usuario is not None:
        sql += " WHERE p.usuario_id = ?"
        parametros = (somente_do_usuario,)
    sql += f" ORDER BY p.id DESC LIMIT {LIMITE_FEED}"
    publicacoes = db.consultar(sql, parametros)
    if not publicacoes:
        aviso("Nenhuma publicação encontrada.")
        return []
    for p in publicacoes:
        linha()
        console.print(f"ID: {p['id']}  |  [bold]{esc(p['nome'])}[/]  |  {p['criado_em'][:16]}")
        console.print(esc(p["texto"]))
        console.print(f"[{VERDE}]❤️ {p['curtidas']}   💬 {p['comentarios']}[/]")
    return publicacoes


def _existe(publicacao_id):
    return db.consultar_um("SELECT id FROM publicacoes WHERE id = ?", (publicacao_id,)) is not None


def _pedir_id(prompt="\nDigite o ID da publicação (Enter cancela): "):
    numero = ler_inteiro(prompt)
    if numero is None:
        return None
    if not _existe(numero):
        erro("Publicação inválida.")
        return None
    return numero


def curtir_publicacao(usuario):
    if not listar_publicacoes():
        return
    pub_id = _pedir_id()
    if pub_id is None:
        return
    try:
        with db.transacao() as con:
            con.execute("INSERT INTO curtidas (publicacao_id, usuario_id) VALUES (?, ?)", (pub_id, usuario["id"]))
    except sqlite3.IntegrityError:
        erro("Você já curtiu essa publicação.")
        return
    sucesso("Publicação curtida! ❤️")
    gamificacao.adicionar_pontos(usuario, "curtir")


def comentar_publicacao(usuario):
    if not listar_publicacoes():
        return
    pub_id = _pedir_id()
    if pub_id is None:
        return
    for c in db.consultar(
        "SELECT c.texto, c.criado_em, u.nome FROM comentarios c JOIN usuarios u ON u.id = c.usuario_id "
        "WHERE c.publicacao_id = ? ORDER BY c.id",
        (pub_id,),
    ):
        console.print(f"  💬 [bold]{esc(c['nome'])}[/] ({c['criado_em'][:16]}): {esc(c['texto'])}")
    texto = ler_texto("Seu comentário (Enter vazio só visualiza): ", obrigatorio=False, maximo=300)
    if texto is None:
        return
    with db.transacao() as con:
        con.execute(
            "INSERT INTO comentarios (publicacao_id, usuario_id, texto) VALUES (?, ?, ?)",
            (pub_id, usuario["id"], texto),
        )
    sucesso("Comentário enviado!")
    gamificacao.adicionar_pontos(usuario, "comentar")


def excluir_publicacao(usuario):
    if not listar_publicacoes(somente_do_usuario=usuario["id"]):
        return
    pub_id = ler_inteiro("\nID da publicação a excluir (Enter cancela): ")
    if pub_id is None:
        return
    dono = db.consultar_um("SELECT usuario_id FROM publicacoes WHERE id = ?", (pub_id,))
    if dono is None or dono["usuario_id"] != usuario["id"]:
        erro("Você só pode excluir as suas próprias publicações.")
        return
    if not confirmar("Excluir esta publicação?"):
        return
    with db.transacao() as con:
        con.execute("DELETE FROM publicacoes WHERE id = ?", (pub_id,))
    sucesso("Publicação excluída.")


def menu_publicacoes(usuario):
    while True:
        opcao = menu(
            "PUBLICAÇÕES",
            [("1", "Ver publicações"), ("2", "Criar publicação"), ("3", "Curtir"),
             ("4", "Comentar / ver comentários"), ("5", "Excluir uma publicação minha"), ("0", "Voltar")],
            "📰",
        )
        if opcao == "1":
            listar_publicacoes()
        elif opcao == "2":
            criar_publicacao(usuario)
        elif opcao == "3":
            curtir_publicacao(usuario)
        elif opcao == "4":
            comentar_publicacao(usuario)
        elif opcao == "5":
            excluir_publicacao(usuario)
        elif opcao == "0":
            return
        else:
            erro("Opção inválida!")
