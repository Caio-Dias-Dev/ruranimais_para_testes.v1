"""Pontos, conquistas e ranking (salvos no banco)."""
import db
from utils import VERDE, console, esc, linha, titulo

# Pontos ganhos por ação
PONTOS = {
    "publicar": 5,
    "comentar": 2,
    "curtir": 1,
    "criar_enquete": 5,
    "votar": 2,
    "enviar_mensagem": 1,
    "enviar_imagem": 3,
}

# (pontos necessários, nome, ícone)
CONQUISTAS = [
    (10, "Primeiros Passos", "🏆"),
    (30, "Amigo dos Animais", "🐾"),
    (50, "Protetor Ruranimais", "🌟"),
]


def adicionar_pontos(usuario, acao):
    """Soma os pontos da ação ao usuário e desbloqueia conquistas, se houver."""
    pontos = PONTOS[acao]
    with db.transacao() as con:
        con.execute("UPDATE usuarios SET pontos = pontos + ? WHERE id = ?", (pontos, usuario["id"]))
        total = con.execute("SELECT pontos FROM usuarios WHERE id = ?", (usuario["id"],)).fetchone()["pontos"]
        ja_tem = {r["nome"] for r in con.execute("SELECT nome FROM conquistas WHERE usuario_id = ?", (usuario["id"],))}
        novas = [(n, i) for minimo, n, i in CONQUISTAS if total >= minimo and n not in ja_tem]
        for nome, _ in novas:
            con.execute("INSERT INTO conquistas (usuario_id, nome) VALUES (?, ?)", (usuario["id"], nome))
    usuario["pontos"] = total
    console.print(f"[{VERDE}]+{pontos} ponto(s)![/]")
    for nome, icone in novas:
        console.print(f"\n{icone} [bold]CONQUISTA DESBLOQUEADA:[/] {nome}")


def visualizar_gamificacao(usuario):
    titulo("GAMIFICAÇÃO", "🏆")
    pontos = db.consultar_um("SELECT pontos FROM usuarios WHERE id = ?", (usuario["id"],))["pontos"]
    console.print(f"Pontuação: [bold]{pontos}[/]")

    obtidas = {r["nome"] for r in db.consultar("SELECT nome FROM conquistas WHERE usuario_id = ?", (usuario["id"],))}
    console.print("\nConquistas:")
    for minimo, nome, icone in CONQUISTAS:
        if nome in obtidas:
            console.print(f"{icone} {nome}")
        else:
            console.print(f"🔒 [dim]{nome} (faltam {max(minimo - pontos, 0)} ponto(s))[/]")


def ranking():
    titulo("RANKING", "🥇")
    linhas = db.consultar("SELECT nome, pontos FROM usuarios ORDER BY pontos DESC, nome LIMIT 10")
    for posicao, r in enumerate(linhas, start=1):
        console.print(f"{posicao}º - {esc(r['nome'])}: {r['pontos']} ponto(s)")
    linha()
