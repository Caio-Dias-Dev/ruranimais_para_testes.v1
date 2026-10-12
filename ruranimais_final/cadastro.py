"""Identificação do usuário: cadastro, login e CRUD completo da conta."""
import hashlib
import hmac
import os
import re
import sqlite3

import db
import imagens
from utils import (
    confirmar, console, erro, esc, ler_senha, ler_texto, linha, menu, sucesso, titulo,
)

EMAIL_UFRPE = re.compile(r"^[^\s@]+@ufrpe\.br$", re.IGNORECASE)
ITERACOES = 200_000


# ---------- senhas ----------
def hash_senha(senha):
    sal = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", senha.encode(), sal, ITERACOES)
    return f"{sal.hex()}${h.hex()}"


def verificar_senha(senha, armazenado):
    try:
        sal_hex, h_hex = armazenado.split("$")
        esperado = bytes.fromhex(h_hex)
        h = hashlib.pbkdf2_hmac("sha256", senha.encode(), bytes.fromhex(sal_hex), ITERACOES)
    except ValueError:
        return False
    return hmac.compare_digest(h, esperado)


# ---------- entradas validadas ----------
def _ler_email(prompt="E-mail institucional (@ufrpe.br): "):
    while True:
        email = ler_texto(prompt, maximo=120).lower()
        if EMAIL_UFRPE.match(email):
            return email
        erro("Utilize um e-mail institucional terminado em @ufrpe.br.")


def _ler_nome(prompt="Nome: "):
    return ler_texto(prompt, minimo=3, maximo=40)


def _ler_nova_senha():
    while True:
        senha = ler_senha("Senha (mínimo 6 caracteres): ")
        if len(senha) < 6:
            erro("A senha deve ter pelo menos 6 caracteres.")
            continue
        if senha != ler_senha("Confirme a senha: "):
            erro("As senhas não coincidem.")
            continue
        return senha


# ---------- Create ----------
def cadastrar_usuario():
    titulo("CADASTRO DE USUÁRIO")
    nome = _ler_nome()
    email = _ler_email()
    senha = _ler_nova_senha()
    try:
        with db.transacao() as con:
            con.execute(
                "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                (nome, email, hash_senha(senha)),
            )
    except sqlite3.IntegrityError:
        erro("Este e-mail já possui uma conta.")
        return False
    sucesso("Usuário cadastrado com sucesso! Agora faça login.")
    return True


# ---------- Read ----------
def login():
    titulo("LOGIN", "🔐")
    email = ler_texto("E-mail: ", maximo=120).lower()
    senha = ler_senha("Senha: ")
    linha_usuario = db.consultar_um("SELECT * FROM usuarios WHERE email = ?", (email,))
    if linha_usuario is None or not verificar_senha(senha, linha_usuario["senha_hash"]):
        erro("E-mail ou senha incorretos.")
        return None
    sucesso(f"Bem-vindo(a), {esc(linha_usuario['nome'])}!")
    return {
        "id": linha_usuario["id"],
        "nome": linha_usuario["nome"],
        "email": linha_usuario["email"],
        "pontos": linha_usuario["pontos"],
    }


def ver_perfil(usuario):
    titulo("MEU PERFIL", "👤")
    dados = db.consultar_um("SELECT * FROM usuarios WHERE id = ?", (usuario["id"],))
    contagem = lambda tabela: db.consultar_um(  # noqa: E731
        f"SELECT COUNT(*) AS n FROM {tabela} WHERE usuario_id = ?", (usuario["id"],)
    )["n"]
    console.print(f"Nome: {esc(dados['nome'])}")
    console.print(f"E-mail: {esc(dados['email'])}")
    console.print(f"Pontos: {dados['pontos']}")
    console.print(f"Membro desde: {dados['criado_em'][:10]}")
    console.print(
        f"Publicações: {contagem('publicacoes')} | Enquetes: {contagem('enquetes')} | "
        f"Imagens: {contagem('imagens')}"
    )


# ---------- Update ----------
def editar_perfil(usuario):
    titulo("EDITAR PERFIL", "✏️")
    console.print("1 - Alterar nome\n2 - Alterar e-mail\n0 - Voltar")
    opcao = input("\nEscolha uma opção: ").strip()
    if opcao == "1":
        novo = _ler_nome("Novo nome: ")
        with db.transacao() as con:
            con.execute("UPDATE usuarios SET nome = ? WHERE id = ?", (novo, usuario["id"]))
        usuario["nome"] = novo
        sucesso("Nome atualizado!")
    elif opcao == "2":
        novo = _ler_email("Novo e-mail (@ufrpe.br): ")
        try:
            with db.transacao() as con:
                con.execute("UPDATE usuarios SET email = ? WHERE id = ?", (novo, usuario["id"]))
        except sqlite3.IntegrityError:
            erro("Este e-mail já está em uso por outra conta.")
            return
        usuario["email"] = novo
        sucesso("E-mail atualizado!")
    elif opcao != "0":
        erro("Opção inválida!")


def alterar_senha(usuario):
    titulo("ALTERAR SENHA", "🔑")
    atual = db.consultar_um("SELECT senha_hash FROM usuarios WHERE id = ?", (usuario["id"],))
    if not verificar_senha(ler_senha("Senha atual: "), atual["senha_hash"]):
        erro("Senha atual incorreta.")
        return
    nova = _ler_nova_senha()
    with db.transacao() as con:
        con.execute("UPDATE usuarios SET senha_hash = ? WHERE id = ?", (hash_senha(nova), usuario["id"]))
    sucesso("Senha alterada com sucesso!")


# ---------- Delete ----------
def excluir_conta(usuario):
    """Devolve True se a conta foi excluída."""
    titulo("EXCLUIR CONTA", "⚠️")
    console.print("Isso apaga sua conta, publicações, enquetes, mensagens e imagens. Não dá para desfazer.")
    if not confirmar("Tem certeza?"):
        return False
    atual = db.consultar_um("SELECT senha_hash FROM usuarios WHERE id = ?", (usuario["id"],))
    if not verificar_senha(ler_senha("Digite sua senha para confirmar: "), atual["senha_hash"]):
        erro("Senha incorreta. A conta não foi excluída.")
        return False
    imagens.apagar_arquivos_do_usuario(usuario["id"])
    with db.transacao() as con:
        con.execute("DELETE FROM usuarios WHERE id = ?", (usuario["id"],))
    sucesso("Conta excluída.")
    return True


def menu_perfil(usuario):
    """Devolve True se a conta foi excluída (para o main encerrar a sessão)."""
    while True:
        opcao = menu(
            "MEU PERFIL",
            [("1", "Ver perfil"), ("2", "Editar dados"), ("3", "Alterar senha"),
             ("4", "Excluir conta"), ("0", "Voltar")],
            "👤",
        )
        if opcao == "1":
            ver_perfil(usuario)
        elif opcao == "2":
            editar_perfil(usuario)
        elif opcao == "3":
            alterar_senha(usuario)
        elif opcao == "4":
            if excluir_conta(usuario):
                return True
        elif opcao == "0":
            return False
        else:
            erro("Opção inválida!")
