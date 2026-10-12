"""Teste de ponta a ponta: simula um usuário digitando no terminal.

Rode com:  python -m unittest discover -s tests -v
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cadastro  # noqa: E402
import db  # noqa: E402
import enquetes  # noqa: E402
import gamificacao  # noqa: E402
import imagens  # noqa: E402
import mensagens  # noqa: E402
import publicacoes  # noqa: E402
import utils  # noqa: E402

cadastro.ITERACOES = 1_000  # acelera os testes


def digitar(*entradas):
    """Simula input() e getpass() com a mesma fila de entradas."""
    fila = iter(entradas)
    return (
        mock.patch("builtins.input", lambda *_: next(fila)),
        mock.patch.object(utils, "getpass", lambda *_: next(fila)),
    )


def executar(funcao, *entradas, args=()):
    p_input, p_senha = digitar(*entradas)
    with p_input, p_senha:
        return funcao(*args)


class FluxoCompleto(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        db.DB_PATH = Path(self.tmp.name) / "teste.db"
        imagens.PASTA = Path(self.tmp.name) / "imgs"
        db.iniciar_banco()

    def tearDown(self):
        self.tmp.cleanup()

    def criar(self, nome, email, senha="segredo1"):
        self.assertTrue(executar(cadastro.cadastrar_usuario, nome, email, senha, senha))
        return executar(cadastro.login, email, senha)

    # ---------- identificação ----------
    def test_cadastro_login_e_validacoes(self):
        ana = self.criar("Ana Souza", "ana@ufrpe.br")
        self.assertEqual(ana["nome"], "Ana Souza")
        # e-mail repetido é recusado
        self.assertFalse(executar(cadastro.cadastrar_usuario, "Outra Ana", "ANA@ufrpe.br", "abcdef", "abcdef"))
        # e-mail não institucional é pedido de novo; senha curta e divergente também
        self.assertTrue(executar(
            cadastro.cadastrar_usuario, "Bia Lima", "bia@gmail.com", "bia@ufrpe.br", "123", "abcdef", "xxxxxx", "abcdef", "abcdef"))
        # login errado
        self.assertIsNone(executar(cadastro.login, "ana@ufrpe.br", "errada"))
        self.assertIsNone(executar(cadastro.login, "naoexiste@ufrpe.br", "x"))

    def test_senha_nao_fica_em_texto_puro(self):
        self.criar("Ana Souza", "ana@ufrpe.br", "minhasenha")
        salvo = db.consultar_um("SELECT senha_hash FROM usuarios")["senha_hash"]
        self.assertNotIn("minhasenha", salvo)

    def test_mesma_senha_para_dois_usuarios(self):
        self.criar("Ana Souza", "ana@ufrpe.br", "igual123")
        self.assertIsNotNone(self.criar("Caio Dias", "caio@ufrpe.br", "igual123"))

    def test_editar_trocar_senha_e_excluir(self):
        ana = self.criar("Ana Souza", "ana@ufrpe.br")
        self.criar("Bia Lima", "bia@ufrpe.br")
        executar(cadastro.editar_perfil, "1", "Ana Maria", args=(ana,))
        self.assertEqual(ana["nome"], "Ana Maria")
        executar(cadastro.editar_perfil, "2", "ana.m@ufrpe.br", args=(ana,))
        self.assertEqual(ana["email"], "ana.m@ufrpe.br")
        executar(cadastro.editar_perfil, "2", "bia@ufrpe.br", args=(ana,))  # já em uso
        self.assertEqual(ana["email"], "ana.m@ufrpe.br")
        executar(cadastro.alterar_senha, "segredo1", "novasenha", "novasenha", args=(ana,))
        self.assertIsNotNone(executar(cadastro.login, "ana.m@ufrpe.br", "novasenha"))
        self.assertIsNone(executar(cadastro.login, "ana.m@ufrpe.br", "segredo1"))
        # exclusão: senha errada não exclui; certa exclui
        self.assertFalse(executar(cadastro.excluir_conta, "s", "errada", args=(ana,)))
        self.assertTrue(executar(cadastro.excluir_conta, "s", "novasenha", args=(ana,)))
        self.assertIsNone(db.consultar_um("SELECT id FROM usuarios WHERE id = ?", (ana["id"],)))

    # ---------- publicações ----------
    def test_publicacoes_curtidas_comentarios(self):
        ana = self.criar("Ana Souza", "ana@ufrpe.br")
        bia = self.criar("Bia Lima", "bia@ufrpe.br")
        executar(publicacoes.criar_publicacao, "Gato machucado perto do bloco A [urgente]", args=(ana,))
        executar(publicacoes.criar_publicacao, "", args=(ana,))  # vazio cancela
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM publicacoes")["n"], 1)
        executar(publicacoes.curtir_publicacao, "1", args=(bia,))
        executar(publicacoes.curtir_publicacao, "1", args=(bia,))  # duplicada
        executar(publicacoes.curtir_publicacao, "99", args=(bia,))  # inexistente
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM curtidas")["n"], 1)
        executar(publicacoes.comentar_publicacao, "1", "Vou levar ao veterinário", args=(bia,))
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM comentarios")["n"], 1)
        # só o dono exclui
        executar(publicacoes.excluir_publicacao, "1", args=(bia,))
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM publicacoes")["n"], 1)
        executar(publicacoes.excluir_publicacao, "1", "s", args=(ana,))
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM publicacoes")["n"], 0)
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM comentarios")["n"], 0)  # cascade

    # ---------- enquetes ----------
    def test_enquetes_um_voto_por_usuario(self):
        ana = self.criar("Ana Souza", "ana@ufrpe.br")
        bia = self.criar("Bia Lima", "bia@ufrpe.br")
        executar(enquetes.criar_enquete, "Castração no campus?", "Sim", "sim", "Não", "Talvez", "", args=(ana,))
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM enquete_opcoes")["n"], 3)  # duplicada recusada
        executar(enquetes.votar_enquete, "1", "1", args=(bia,))
        executar(enquetes.votar_enquete, "1", "2", args=(bia,))  # segundo voto recusado
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM votos")["n"], 1)
        executar(enquetes.votar_enquete, "1", "9", args=(ana,))  # opção inválida
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM votos")["n"], 1)
        executar(enquetes.listar_enquetes, args=(bia,))

    # ---------- mensagens ----------
    def test_mensagens_e_nao_lidas(self):
        ana = self.criar("Ana Souza", "ana@ufrpe.br")
        bia = self.criar("Bia Lima", "bia@ufrpe.br")
        executar(mensagens.nova_conversa, str(bia["id"]), "Oi, Bia!", "", args=(ana,))
        self.assertEqual(mensagens.contar_nao_lidas(bia), 1)
        executar(mensagens.caixa_de_entrada, str(ana["id"]), "Oi, Ana!", "", args=(bia,))
        self.assertEqual(mensagens.contar_nao_lidas(bia), 0)
        self.assertEqual(mensagens.contar_nao_lidas(ana), 1)
        executar(mensagens.nova_conversa, "999", args=(ana,))  # inexistente
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM mensagens")["n"], 2)

    # ---------- imagens ----------
    def test_imagens(self):
        ana = self.criar("Ana Souza", "ana@ufrpe.br")
        origem = Path(self.tmp.name) / "gato.png"
        origem.write_bytes(b"\x89PNG fake")
        texto = Path(self.tmp.name) / "nota.txt"
        texto.write_text("oi")
        executar(imagens.enviar_imagem, str(texto), args=(ana,))  # formato inválido
        executar(imagens.enviar_imagem, str(Path(self.tmp.name) / "nao.png"), args=(ana,))  # inexistente
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM imagens")["n"], 0)
        executar(imagens.enviar_imagem, f'"{origem}"', "Gatinho do bloco B", args=(ana,))
        registro = db.consultar_um("SELECT * FROM imagens")
        self.assertTrue((imagens.PASTA / registro["arquivo"]).is_file())
        executar(imagens.galeria)
        executar(imagens.excluir_imagem, str(registro["id"]), "s", args=(ana,))
        self.assertFalse((imagens.PASTA / registro["arquivo"]).exists())
        # excluir a conta apaga os arquivos
        executar(imagens.enviar_imagem, str(origem), "", args=(ana,))
        arquivo = db.consultar_um("SELECT arquivo FROM imagens")["arquivo"]
        executar(cadastro.excluir_conta, "s", "segredo1", args=(ana,))
        self.assertFalse((imagens.PASTA / arquivo).exists())

    # ---------- gamificação ----------
    def test_pontos_e_conquistas(self):
        ana = self.criar("Ana Souza", "ana@ufrpe.br")
        executar(publicacoes.criar_publicacao, "um", args=(ana,))
        executar(publicacoes.criar_publicacao, "dois", args=(ana,))  # 10 pontos
        self.assertEqual(ana["pontos"], 10)
        nomes = [r["nome"] for r in db.consultar("SELECT nome FROM conquistas")]
        self.assertEqual(nomes, ["Primeiros Passos"])
        for _ in range(4):
            executar(publicacoes.criar_publicacao, "mais", args=(ana,))  # 30 pontos
        self.assertEqual(ana["pontos"], 30)
        self.assertEqual(db.consultar_um("SELECT COUNT(*) n FROM conquistas")["n"], 2)
        executar(gamificacao.visualizar_gamificacao, args=(ana,))
        executar(gamificacao.ranking)

    # ---------- menus ----------
    def test_main_navega_pelos_menus(self):
        import main
        entradas = [
            "1", "Ana Souza", "ana@ufrpe.br", "segredo1", "segredo1",  # cadastro
            "2", "ana@ufrpe.br", "segredo1",                            # login
            "1", "2", "Olá, campus!", "1", "0",                         # publicações
            "2", "0", "3", "0", "4", "0", "5", "1", "2", "0", "6", "1", "0",  # demais menus
            "9", "0",                                                   # opção inválida, sair da conta
            "3",                                                        # sair
        ]
        with mock.patch("main.time.sleep"):
            executar(main.menu_inicial, *entradas)


if __name__ == "__main__":
    unittest.main()
