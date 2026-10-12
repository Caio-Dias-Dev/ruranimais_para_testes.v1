# 🐾 Ruranimais — A rede social de quem cuida (Release 1.0, versão console)

Rede social de terminal para a comunidade da **UFRPE** acompanhar e cuidar dos animais do campus.
Tudo é salvo em um banco SQLite (`banco.db`), então os dados continuam depois de fechar o programa.

## Funcionalidades do Release 1.0

| Funcionalidade | O que faz |
|---|---|
| **Identificação (CRUD)** | Cadastrar (somente e-mail `@ufrpe.br`), login, ver perfil, editar nome/e-mail, alterar senha e excluir conta. Senhas guardadas com hash (PBKDF2). |
| **Postagens de texto** | Criar, listar, curtir (uma vez por pessoa), comentar e excluir as próprias. |
| **Enquetes** | Criar com 2 a 5 opções, votar (um voto por pessoa), ver resultados com percentual e excluir as próprias. |
| **Bate-papo** | Conversas entre usuários, com histórico, aviso de mensagens não lidas e resposta direta. |
| **Envio de imagens** | Valida formato (png, jpg, jpeg, gif, webp) e tamanho (até 5 MB), copia para `imagens_repositorio/`, com legenda e galeria da comunidade. |
| **Gamificação** | Pontos por ações, conquistas (Primeiros Passos, Amigo dos Animais, Protetor Ruranimais) e ranking. |

## Como rodar

Requer Python 3.10+.

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate      Linux/macOS:  source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes simulam um usuário digitando no terminal e usam um banco temporário (não mexem no seu `banco.db`).

## Estrutura

```
main.py          menus e ponto de entrada
db.py            esquema SQLite e funções de acesso
utils.py         cores, entradas validadas e menus
cadastro.py      identificação / CRUD de usuário
publicacoes.py   postagens, curtidas, comentários
enquetes.py      enquetes e votos
mensagens.py     bate-papo
imagens.py       envio e galeria de imagens
gamificacao.py   pontos, conquistas e ranking
tests/           testes automatizados
```

## Pontos por ação

Publicar +5 · Criar enquete +5 · Enviar imagem +3 · Comentar +2 · Votar +2 · Curtir +1 · Enviar mensagem +1

## Ideias para versões futuras

Mapeamento dos animais (cadastro de animais e locais), notificações e moderação de conteúdo.
