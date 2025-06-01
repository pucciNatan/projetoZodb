from datetime import date
import transaction
from ZODB import FileStorage, DB
from persistent import Persistent
from BTrees.OOBTree import OOBTree

# ---------- CLASSES PERSISTENTES ----------
class Usuario(Persistent):
    def __init__(self, id_usuario, nome, sobrenome, idade):
        self.id_usuario = id_usuario
        self.nome = nome
        self.sobrenome = sobrenome
        self.idade = idade

class Exemplar(Persistent):
    def __init__(self, id_exemplar, id_livro, status="disponivel"):
        self.id_exemplar = id_exemplar
        self.id_livro = id_livro
        self.status = status

class Livro(Persistent):
    def __init__(self, id_livro, titulo, categoria, autor):
        self.id_livro = id_livro
        self.titulo = titulo
        self.categoria = categoria
        self.autor = autor
        self.estoque = 0                 # exemplares disponíveis
        self.exemplares = OOBTree()      # id_exemplar → Exemplar

class Emprestimo(Persistent):
    def __init__(self, id_emprestimo, id_usuario, id_exemplar, data_devolucao=None):
        self.id_emprestimo = id_emprestimo
        self.id_usuario = id_usuario
        self.id_exemplar = id_exemplar
        self.data_devolucao = data_devolucao

# ---------- CONEXÃO ZODB ----------
def abrir_banco():
    armazenamento = FileStorage.FileStorage('biblioteca.fs')
    return DB(armazenamento)

db = abrir_banco()
conexao = db.open()
root = conexao.root()

# coleções principais
for balde in ("usuarios", "livros", "emprestimos"):
    if balde not in root:
        root[balde] = OOBTree()

# contadores de IDs
if "contadores" not in root:
    root["contadores"] = {"usuario": 1, "livro": 1, "exemplar": 1, "emprestimo": 1}

def novo_id(chave):
    cont = root["contadores"]
    valor = cont[chave]
    cont[chave] += 1
    return valor

# ---------- FUNÇÕES utilitárias ----------
def alterar_estoque(livro, delta):
    livro.estoque += delta
    assert livro.estoque >= 0, "Estoque negativo!"

def gravar(msg=""):
    transaction.commit()
    if msg:
        print(f"💾 {msg}")

# ---------- CRUD: USUÁRIOS ----------
def criar_usuario():
    nome = input("Nome: ")
    sobrenome = input("Sobrenome: ")
    idade = int(input("Idade: "))
    id_usuario = novo_id("usuario")
    root["usuarios"][id_usuario] = Usuario(id_usuario, nome, sobrenome, idade)
    gravar("Usuário criado")
    print(f"✅ Usuário {id_usuario}")

def listar_usuarios():
    print("\n📋 Usuários:")
    for u in root["usuarios"].values():
        print(f"{u.id_usuario}: {u.nome} {u.sobrenome} – {u.idade} anos")

# ---------- CRUD: LIVROS / EXEMPLARES ----------
def criar_livro():
    titulo = input("Título: ")
    categoria = input("Categoria: ")
    autor = input("Autor: ")
    estoque_inicial = int(input("Estoque inicial: "))

    id_livro = novo_id("livro")
    livro = Livro(id_livro, titulo, categoria, autor)
    root["livros"][id_livro] = livro

    # cria exemplares
    for _ in range(estoque_inicial):
        id_exemplar = novo_id("exemplar")
        livro.exemplares[id_exemplar] = Exemplar(id_exemplar, id_livro)
    alterar_estoque(livro, estoque_inicial)

    gravar("Livro + exemplares criados")
    print(f"✅ Livro {id_livro} com {estoque_inicial} exemplares")

def listar_livros():
    print("\n📚 Livros:")
    for l in root["livros"].values():
        print(f"{l.id_livro}: '{l.titulo}' – Estoque disponível: {l.estoque}")

def adicionar_exemplares():
    id_livro = int(input("ID do Livro: "))
    quantidade = int(input("Quantos exemplares adicionar? "))
    livro = root["livros"].get(id_livro)
    if not livro:
        print("❌ Livro não existe"); return
    for _ in range(quantidade):
        id_exemplar = novo_id("exemplar")
        livro.exemplares[id_exemplar] = Exemplar(id_exemplar, id_livro)
    alterar_estoque(livro, quantidade)
    gravar("Exemplares adicionados")
    print(f"✅ +{quantidade} exemplares no livro {id_livro}")

def listar_exemplares():
    id_livro = int(input("ID do Livro (0 para todos): "))
    if id_livro == 0:
        print("\n📦 Todos os Exemplares:")
        for l in root["livros"].values():
            for ex in l.exemplares.values():
                print(f"{ex.id_exemplar}: Livro {l.id_livro} '{l.titulo}' – {ex.status}")
    else:
        livro = root["livros"].get(id_livro)
        if not livro:
            print("❌ Livro não existe"); return
        for ex in livro.exemplares.values():
            print(f"{ex.id_exemplar}: {ex.status}")

def excluir_exemplar():
    id_exemplar = int(input("ID do Exemplar: "))
    for l in root["livros"].values():
        if id_exemplar in l.exemplares:
            ex = l.exemplares.pop(id_exemplar)
            if ex.status == "disponivel":
                alterar_estoque(l, -1)
            gravar("Exemplar excluído")
            print("✅ Excluído")
            return
    print("❌ Exemplar não encontrado")

def excluir_livro():
    id_livro = int(input("ID do Livro: "))
    livro = root["livros"].pop(id_livro, None)
    if not livro:
        print("❌ Livro não existe"); return
    gravar("Livro + exemplares removidos")
    print("✅ Livro removido")

# ---------- EMPRÉSTIMOS ----------
def criar_emprestimo():
    id_usuario = int(input("ID do Usuário: "))
    id_exemplar = int(input("ID do Exemplar: "))
    data_dev = input("Data devolução (YYYY-MM-DD ou vazio): ") or None

    usuario = root["usuarios"].get(id_usuario)
    if not usuario:
        print("❌ Usuário não existe"); return

    # procura exemplar
    for livro in root["livros"].values():
        ex = livro.exemplares.get(id_exemplar)
        if ex:
            if ex.status != "disponivel":
                print("❌ Exemplar já emprestado"); return
            id_emprestimo = novo_id("emprestimo")
            root["emprestimos"][id_emprestimo] = Emprestimo(
                id_emprestimo, id_usuario, id_exemplar, data_dev
            )
            ex.status = "emprestado"
            alterar_estoque(livro, -1)
            gravar("Empréstimo criado")
            print(f"✅ Empréstimo {id_emprestimo}")
            return
    print("❌ Exemplar não encontrado")

def devolver_livro():
    id_exemplar = int(input("ID do Exemplar devolvido: "))
    for livro in root["livros"].values():
        ex = livro.exemplares.get(id_exemplar)
        if ex:
            if ex.status != "emprestado":
                print("❌ Este exemplar não está emprestado"); return
            ex.status = "disponivel"
            alterar_estoque(livro, 1)
            gravar("Devolução registrada")
            print("✅ Devolvido")
            return
    print("❌ Exemplar não existe")

def listar_emprestimos():
    print("\n📑 Empréstimos:")
    for emp in root["emprestimos"].values():
        usuario = root["usuarios"][emp.id_usuario]
        # busca título do livro
        titulo_livro = next(
            l.titulo for l in root["livros"].values() if emp.id_exemplar in l.exemplares
        )
        print(
            f"{emp.id_emprestimo}: {usuario.nome} pegou '{titulo_livro}' "
            f"(Ex {emp.id_exemplar}) – devolução {emp.data_devolucao}"
        )
