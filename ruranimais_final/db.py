"""Acesso ao banco de dados SQLite do Ruranimais."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "banco.db"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    senha_hash  TEXT NOT NULL,
    pontos      INTEGER NOT NULL DEFAULT 0,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS publicacoes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    texto       TEXT NOT NULL,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS curtidas (
    publicacao_id INTEGER NOT NULL REFERENCES publicacoes(id) ON DELETE CASCADE,
    usuario_id    INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    PRIMARY KEY (publicacao_id, usuario_id)
);

CREATE TABLE IF NOT EXISTS comentarios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    publicacao_id INTEGER NOT NULL REFERENCES publicacoes(id) ON DELETE CASCADE,
    usuario_id    INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    texto         TEXT NOT NULL,
    criado_em     TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS enquetes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    pergunta    TEXT NOT NULL,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS enquete_opcoes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    enquete_id  INTEGER NOT NULL REFERENCES enquetes(id) ON DELETE CASCADE,
    texto       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS votos (
    enquete_id  INTEGER NOT NULL REFERENCES enquetes(id) ON DELETE CASCADE,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    opcao_id    INTEGER NOT NULL REFERENCES enquete_opcoes(id) ON DELETE CASCADE,
    PRIMARY KEY (enquete_id, usuario_id)
);

CREATE TABLE IF NOT EXISTS mensagens (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    remetente_id     INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    destinatario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    texto            TEXT NOT NULL,
    lida             INTEGER NOT NULL DEFAULT 0,
    criado_em        TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS imagens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    arquivo     TEXT NOT NULL,
    legenda     TEXT,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS conquistas (
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nome        TEXT NOT NULL,
    PRIMARY KEY (usuario_id, nome)
);
"""


def _conectar():
    conexao = sqlite3.connect(DB_PATH)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def iniciar_banco():
    """Cria as tabelas, se ainda não existirem."""
    with transacao() as con:
        con.executescript(ESQUEMA)


@contextmanager
def transacao():
    """Abre uma conexão, confirma (commit) ao sair e desfaz (rollback) em caso de erro."""
    conexao = _conectar()
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def consultar(sql, parametros=()):
    """Executa um SELECT e devolve a lista de linhas."""
    conexao = _conectar()
    try:
        return conexao.execute(sql, parametros).fetchall()
    finally:
        conexao.close()


def consultar_um(sql, parametros=()):
    linhas = consultar(sql, parametros)
    return linhas[0] if linhas else None
