from datetime import date
import transaction
from ZODB import FileStorage, DB
from persistent import Persistent
from BTrees.OOBTree import OOBTree

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
        self.estoque = 0
        self.exemplares = OOBTree()

class Emprestimo(Persistent):
    def __init__(self, id_emprestimo, id_usuario, id_exemplar, data_devolucao=None):
        self.id_emprestimo = id_emprestimo
        self.id_usuario = id_usuario
        self.id_exemplar = id_exemplar
        self.data_devolucao = data_devolucao

def abrir_banco():
    armazenamento = FileStorage.FileStorage('biblioteca.fs')
    return DB(armazenamento)

db = abrir_banco()
conexao = db.open()
root = conexao.root()

for balde in ("usuarios", "livros", "emprestimos"):
    if balde not in root:
        root[balde] = OOBTree()

if "contadores" not in root:
    root["contadores"] = {"usuario": 1, "livro": 1, "exemplar": 1, "emprestimo": 1}

def novo_id(chave):
    cont = root["contadores"]
    valor = cont[chave]
    cont[chave] += 1
    return valor

def alterar_estoque(livro, delta):
    livro.estoque += delta
    assert livro.estoque >= 0, "Estoque negativo!"

def gravar(msg=""):
    transaction.commit()
    if msg:
        print(msg)

def criar_usuario():
    nome = input("Nome: ")
    sobrenome = input("Sobrenome: ")
    idade = int(input("Idade: "))
    id_usuario = novo_id("usuario")
    root["usuarios"][id_usuario] = Usuario(id_usuario, nome, sobrenome, idade)
    gravar("Usuário criado")

def listar_usuarios():
    print("\nUsuários:")
    for u in root["usuarios"].values():
        print(f"{u.id_usuario}: {u.nome} {u.sobrenome} – {u.idade} anos")

def editar_usuario():
    id_usuario = int(input("ID do usuário a editar: "))
    usuario = root["usuarios"].get(id_usuario)
    if not usuario:
        print("Usuário não encontrado")
        return
    usuario.nome = input(f"Novo nome [{usuario.nome}]: ") or usuario.nome
    usuario.sobrenome = input(f"Novo sobrenome [{usuario.sobrenome}]: ") or usuario.sobrenome
    idade_nova = input(f"Nova idade [{usuario.idade}]: ")
    if idade_nova:
        usuario.idade = int(idade_nova)
    gravar("Usuário editado")

def excluir_usuario():
    id_usuario = int(input("ID do usuário a excluir: "))

    if id_usuario not in root["usuarios"]:
        print("Usuário não encontrado")
        return

    for emp in root["emprestimos"].values():
        if emp.id_usuario == id_usuario:
            print("Usuário possui empréstimos ativos e não pode ser excluído.")
            return

    del root["usuarios"][id_usuario]
    gravar("Usuário excluído")

def criar_livro():
    titulo = input("Título: ")
    categoria = input("Categoria: ")
    autor = input("Autor: ")
    estoque_inicial = int(input("Estoque inicial: "))
    id_livro = novo_id("livro")
    livro = Livro(id_livro, titulo, categoria, autor)
    root["livros"][id_livro] = livro
    for _ in range(estoque_inicial):
        id_exemplar = novo_id("exemplar")
        livro.exemplares[id_exemplar] = Exemplar(id_exemplar, id_livro)
    alterar_estoque(livro, estoque_inicial)
    gravar("Livro + exemplares criados")

def listar_livros():
    print("\nLivros:")
    for l in root["livros"].values():
        print(f"{l.id_livro}: '{l.titulo}' – Estoque: {l.estoque}")

def editar_livro():
    id_livro = int(input("ID do livro a editar: "))
    livro = root["livros"].get(id_livro)
    if not livro:
        print("Livro não encontrado")
        return
    livro.titulo = input(f"Novo título [{livro.titulo}]: ") or livro.titulo
    livro.categoria = input(f"Nova categoria [{livro.categoria}]: ") or livro.categoria
    livro.autor = input(f"Novo autor [{livro.autor}]: ") or livro.autor
    gravar("Livro editado")

def excluir_livro():
    id_livro = int(input("ID do Livro: "))
    if root["livros"].pop(id_livro, None):
        gravar("Livro + exemplares removidos")
    else:
        print("Livro não existe")

def adicionar_exemplares():
    id_livro = int(input("ID do Livro: "))
    qtd = int(input("Quantos exemplares adicionar?: "))
    livro = root["livros"].get(id_livro)
    if not livro:
        print("Livro não existe")
        return
    for _ in range(qtd):
        id_exemplar = novo_id("exemplar")
        livro.exemplares[id_exemplar] = Exemplar(id_exemplar, id_livro)
    alterar_estoque(livro, qtd)
    gravar("Exemplares adicionados")

def listar_exemplares():
    id_livro = int(input("ID do Livro (0 para todos): "))
    if id_livro == 0:
        for l in root["livros"].values():
            for ex in l.exemplares.values():
                print(f"{ex.id_exemplar}: Livro {l.id_livro} '{l.titulo}' – {ex.status}")
    else:
        livro = root["livros"].get(id_livro)
        if not livro:
            print("Livro não existe")
            return
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
            return
    print("Exemplar não encontrado")

def criar_emprestimo():
    id_usuario = int(input("ID do Usuário: "))
    id_exemplar = int(input("ID do Exemplar: "))
    data_dev = input("Data devolução (YYYY-MM-DD ou vazio): ") or None
    usuario = root["usuarios"].get(id_usuario)
    if not usuario:
        print("Usuário não existe")
        return
    for livro in root["livros"].values():
        ex = livro.exemplares.get(id_exemplar)
        if ex:
            if ex.status != "disponivel":
                print("Exemplar já emprestado")
                return
            id_emp = novo_id("emprestimo")
            root["emprestimos"][id_emp] = Emprestimo(id_emp, id_usuario, id_exemplar, data_dev)
            ex.status = "emprestado"
            alterar_estoque(livro, -1)
            gravar("Empréstimo criado")
            return
    print("Exemplar não encontrado")

def devolver_livro():
    id_exemplar = int(input("ID do Exemplar devolvido: "))

    for livro in root["livros"].values():
        ex = livro.exemplares.get(id_exemplar)
        if ex:
            if ex.status != "emprestado":
                print("Este exemplar não está emprestado")
                return

            for id_emp, emp in list(root["emprestimos"].items()):
                if emp.id_exemplar == id_exemplar:
                    del root["emprestimos"][id_emp]
                    break

            ex.status = "disponivel"
            alterar_estoque(livro, 1)
            gravar("Devolução registrada e empréstimo removido")
            return

    print("Exemplar não encontrado")

def listar_emprestimos():
    emprestimos = root["emprestimos"]
    if not emprestimos:
        print("Não existem empréstimos registrados.")
        return

    print("\nLista de empréstimos:")
    for emp in emprestimos.values():
        usuario = root["usuarios"][emp.id_usuario]
        titulo_livro = next(
            l.titulo for l in root["livros"].values() if emp.id_exemplar in l.exemplares
        )
        print(
            f"{emp.id_emprestimo}: {usuario.nome} pegou '{titulo_livro}' "
            f"(Ex {emp.id_exemplar}) – devolução {emp.data_devolucao}"
        )