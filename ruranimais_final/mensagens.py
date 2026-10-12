"""Bate-papo entre usuários, com conversas salvas e contagem de não lidas."""
import db
import gamificacao
from utils import aviso, console, erro, esc, ler_inteiro, ler_texto, linha, menu, sucesso, titulo

HISTORICO = 30


def contar_nao_lidas(usuario):
    return db.consultar_um(
        "SELECT COUNT(*) AS n FROM mensagens WHERE destinatario_id = ? AND lida = 0", (usuario["id"],)
    )["n"]


def _outros_usuarios(usuario):
    return db.consultar("SELECT id, nome, email FROM usuarios WHERE id != ? ORDER BY nome", (usuario["id"],))


def _enviar(usuario, destinatario_id, texto):
    with db.transacao() as con:
        con.execute(
            "INSERT INTO mensagens (remetente_id, destinatario_id, texto) VALUES (?, ?, ?)",
            (usuario["id"], destinatario_id, texto),
        )
    gamificacao.adicionar_pontos(usuario, "enviar_mensagem")


def _abrir_conversa(usuario, outro):
    """Mostra o histórico com 'outro' e permite responder até o usuário sair."""
    while True:
        titulo(f"CONVERSA COM {esc(outro['nome']).upper()}", "💬")
        with db.transacao() as con:
            con.execute(
                "UPDATE mensagens SET lida = 1 WHERE remetente_id = ? AND destinatario_id = ?",
                (outro["id"], usuario["id"]),
            )
        mensagens = db.consultar(
            "SELECT remetente_id, texto, criado_em FROM mensagens "
            "WHERE (remetente_id = ? AND destinatario_id = ?) OR (remetente_id = ? AND destinatario_id = ?) "
            f"ORDER BY id DESC LIMIT {HISTORICO}",
            (usuario["id"], outro["id"], outro["id"], usuario["id"]),
        )
        if not mensagens:
            aviso("Nenhuma mensagem ainda. Diga olá!")
        for m in reversed(mensagens):
            quem = "Você" if m["remetente_id"] == usuario["id"] else esc(outro["nome"])
            console.print(f"[dim]{m['criado_em'][5:16]}[/] [bold]{quem}:[/] {esc(m['texto'])}")
        linha()
        texto = ler_texto("Mensagem (Enter vazio volta): ", obrigatorio=False, maximo=500)
        if texto is None:
            return
        _enviar(usuario, outro["id"], texto)
        sucesso("Mensagem enviada!")


def nova_conversa(usuario):
    titulo("ENVIAR MENSAGEM", "💬")
    usuarios = _outros_usuarios(usuario)
    if not usuarios:
        aviso("Ainda não há outros usuários cadastrados.")
        return
    console.print("Usuários disponíveis:")
    for u in usuarios:
        console.print(f"{u['id']} - {esc(u['nome'])} ({esc(u['email'])})")
    escolhido = ler_inteiro("\nID do destinatário (Enter cancela): ")
    if escolhido is None:
        return
    outro = next((u for u in usuarios if u["id"] == escolhido), None)
    if outro is None:
        erro("Usuário não encontrado.")
        return
    _abrir_conversa(usuario, outro)


def caixa_de_entrada(usuario):
    titulo("MINHAS CONVERSAS", "📥")
    conversas = db.consultar(
        """
        SELECT u.id, u.nome, MAX(m.id) AS ultimo,
               SUM(CASE WHEN m.destinatario_id = :eu AND m.lida = 0 THEN 1 ELSE 0 END) AS nao_lidas
        FROM mensagens m
        JOIN usuarios u ON u.id = CASE WHEN m.remetente_id = :eu THEN m.destinatario_id ELSE m.remetente_id END
        WHERE m.remetente_id = :eu OR m.destinatario_id = :eu
        GROUP BY u.id ORDER BY ultimo DESC
        """,
        {"eu": usuario["id"]},
    )
    if not conversas:
        aviso("Nenhuma mensagem encontrada.")
        return
    for c in conversas:
        novas = f"  [bold red]({c['nao_lidas']} nova(s))[/]" if c["nao_lidas"] else ""
        console.print(f"{c['id']} - {esc(c['nome'])}{novas}")
    escolhido = ler_inteiro("\nID do contato para abrir a conversa (Enter volta): ")
    if escolhido is None:
        return
    outro = next((c for c in conversas if c["id"] == escolhido), None)
    if outro is None:
        erro("Conversa não encontrada.")
        return
    _abrir_conversa(usuario, outro)


def menu_mensagens(usuario):
    while True:
        nao_lidas = contar_nao_lidas(usuario)
        aviso_novas = f" ({nao_lidas} não lida(s))" if nao_lidas else ""
        opcao = menu(
            "MENSAGENS",
            [("1", f"Minhas conversas{aviso_novas}"), ("2", "Enviar mensagem para alguém"), ("0", "Voltar")],
            "💬",
        )
        if opcao == "1":
            caixa_de_entrada(usuario)
        elif opcao == "2":
            nova_conversa(usuario)
        elif opcao == "0":
            return
        else:
            erro("Opção inválida!")
