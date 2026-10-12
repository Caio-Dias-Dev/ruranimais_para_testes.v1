"""Envio de imagens: o arquivo é validado e copiado para a pasta imagens_repositorio."""
import shutil
import uuid
from pathlib import Path

import db
import gamificacao
from utils import aviso, confirmar, console, erro, esc, ler_inteiro, ler_texto, linha, menu, sucesso, titulo

PASTA = db.BASE_DIR / "imagens_repositorio"
EXTENSOES = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
TAMANHO_MAXIMO = 5 * 1024 * 1024  # 5 MB


def enviar_imagem(usuario):
    titulo("ENVIO DE IMAGEM", "🖼️")
    caminho = ler_texto("Caminho da imagem (Enter vazio cancela): ", obrigatorio=False, maximo=500)
    if caminho is None:
        aviso("Envio cancelado.")
        return
    origem = Path(caminho.strip("\"'")).expanduser()
    if not origem.is_file():
        erro("Arquivo não encontrado.")
        return
    extensao = origem.suffix.lower()
    if extensao not in EXTENSOES:
        erro(f"Formato não aceito. Use: {', '.join(sorted(EXTENSOES))}.")
        return
    if origem.stat().st_size > TAMANHO_MAXIMO:
        erro("A imagem é maior que 5 MB.")
        return
    legenda = ler_texto("Legenda (opcional): ", obrigatorio=False, maximo=100)
    PASTA.mkdir(exist_ok=True)
    nome_salvo = f"{uuid.uuid4().hex}{extensao}"
    shutil.copy2(origem, PASTA / nome_salvo)
    with db.transacao() as con:
        con.execute(
            "INSERT INTO imagens (usuario_id, arquivo, legenda) VALUES (?, ?, ?)",
            (usuario["id"], nome_salvo, legenda),
        )
    sucesso("Imagem enviada com sucesso!")
    gamificacao.adicionar_pontos(usuario, "enviar_imagem")


def _mostrar(imagens, com_autor=False):
    for i in imagens:
        linha()
        autor = f" | por {esc(i['nome'])}" if com_autor else ""
        console.print(f"ID: {i['id']}{autor} | {i['criado_em'][:16]}")
        console.print(f"Arquivo: imagens_repositorio/{i['arquivo']}")
        if i["legenda"]:
            console.print(f"Legenda: {esc(i['legenda'])}")


def visualizar_imagens(usuario):
    titulo("MINHAS IMAGENS", "🖼️")
    imagens = db.consultar(
        "SELECT i.*, u.nome FROM imagens i JOIN usuarios u ON u.id = i.usuario_id "
        "WHERE i.usuario_id = ? ORDER BY i.id DESC", (usuario["id"],))
    if not imagens:
        aviso("Nenhuma imagem encontrada.")
        return []
    _mostrar(imagens)
    return imagens


def galeria():
    titulo("GALERIA DA COMUNIDADE", "🖼️")
    imagens = db.consultar(
        "SELECT i.*, u.nome FROM imagens i JOIN usuarios u ON u.id = i.usuario_id ORDER BY i.id DESC LIMIT 20")
    if not imagens:
        aviso("Nenhuma imagem encontrada.")
        return
    _mostrar(imagens, com_autor=True)


def _remover_arquivo(nome):
    try:
        (PASTA / nome).unlink()
    except FileNotFoundError:
        pass


def excluir_imagem(usuario):
    minhas = visualizar_imagens(usuario)
    if not minhas:
        return
    numero = ler_inteiro("\nID da imagem a excluir (Enter cancela): ")
    if numero is None:
        return
    escolhida = next((i for i in minhas if i["id"] == numero), None)
    if escolhida is None:
        erro("Você só pode excluir as suas próprias imagens.")
        return
    if not confirmar("Excluir esta imagem?"):
        return
    with db.transacao() as con:
        con.execute("DELETE FROM imagens WHERE id = ?", (numero,))
    _remover_arquivo(escolhida["arquivo"])
    sucesso("Imagem excluída.")


def apagar_arquivos_do_usuario(usuario_id):
    """Remove do disco os arquivos do usuário (chamado antes de excluir a conta)."""
    for i in db.consultar("SELECT arquivo FROM imagens WHERE usuario_id = ?", (usuario_id,)):
        _remover_arquivo(i["arquivo"])


def menu_imagens(usuario):
    while True:
        opcao = menu(
            "IMAGENS",
            [("1", "Enviar imagem"), ("2", "Minhas imagens"), ("3", "Galeria da comunidade"),
             ("4", "Excluir uma imagem minha"), ("0", "Voltar")],
            "🖼️",
        )
        if opcao == "1":
            enviar_imagem(usuario)
        elif opcao == "2":
            visualizar_imagens(usuario)
        elif opcao == "3":
            galeria()
        elif opcao == "4":
            excluir_imagem(usuario)
        elif opcao == "0":
            return
        else:
            erro("Opção inválida!")
