import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = dict(
    host="localhost",
    port=5432,
    dbname="polls",
    user="docker",
    password="docker"
)

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# ---------- utilitário ----------
def atualiza_estoque(id_livro, qtd, cur):
    cur.execute("""
        UPDATE livros
        SET estoque = estoque + %s
        WHERE id_livros = %s;
    """, (qtd, id_livro))

# ---------- USUÁRIOS ----------
def criar_usuario():
    nome       = input("Nome: ")
    sobrenome  = input("Sobrenome: ")
    idade      = int(input("Idade: "))
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO usuarios (nome, sobrenome, idade)
            VALUES (%s,%s,%s) RETURNING id_usuario;
        """, (nome, sobrenome, idade))
        print(f"✅ Usuário criado (ID {cur.fetchone()[0]})")

def listar_usuarios():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM usuarios;")
        for u in cur.fetchall():
            print(f"{u['id_usuario']}: {u['nome']} {u['sobrenome']} – {u['idade']} anos")

# ---------- LIVROS ----------
def criar_livro():
    titulo    = input("Título: ")
    categoria = input("Categoria: ")
    autor     = input("Autor: ")
    estoque   = int(input("Estoque inicial: "))
    with get_connection() as conn, conn.cursor() as cur:
        # 1. cria livro com estoque 0 (ajustaremos depois)
        cur.execute("""
            INSERT INTO livros (titulo,categoria,autor,estoque)
            VALUES (%s,%s,%s,0) RETURNING id_livros;
        """, (titulo, categoria, autor))
        id_livro = cur.fetchone()[0]
        # 2. gera exemplares
        cur.executemany("""
            INSERT INTO exemplares (status,id_livro)
            VALUES ('disponivel',%s);
        """, [(id_livro,)] * estoque)
        # 3. atualiza estoque
        atualiza_estoque(id_livro, estoque, cur)
        print(f"✅ Livro {id_livro} criado com {estoque} exemplares")

def listar_livros():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM livros;")
        for l in cur.fetchall():
            print(f"{l['id_livros']}: '{l['titulo']}' – Estoque disponível: {l['estoque']}")

# ---------- EXEMPLARES ----------
def adicionar_exemplares():
    id_livro = int(input("ID do Livro: "))
    qtd      = int(input("Quantos exemplares adicionar?: "))
    with get_connection() as conn, conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO exemplares (status,id_livro)
            VALUES ('disponivel',%s);
        """, [(id_livro,)] * qtd)
        atualiza_estoque(id_livro, qtd, cur)
        print(f"✅ {qtd} exemplares adicionados ao livro {id_livro}")

def listar_exemplares():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT ex.id_exemplar, ex.status, l.titulo
            FROM exemplares ex JOIN livros l ON l.id_livros = ex.id_livro
            ORDER BY ex.id_exemplar;
        """)
        for e in cur.fetchall():
            print(f"{e['id_exemplar']}: {e['titulo']} – {e['status']}")

def excluir_exemplar():
    id_exemplar = int(input("ID do Exemplar a excluir: "))
    with get_connection() as conn, conn.cursor() as cur:
        # recuperar livro + status antes de deletar
        cur.execute("""
            SELECT id_livro, status FROM exemplares
            WHERE id_exemplar = %s;
        """, (id_exemplar,))
        row = cur.fetchone()
        if not row:
            print("❌ Exemplar não encontrado.")
            return
        id_livro, status = row
        # deletar exemplar
        cur.execute("DELETE FROM exemplares WHERE id_exemplar = %s;", (id_exemplar,))
        # estoque só cai se exemplar estava disponível
        if status == 'disponivel':
            atualiza_estoque(id_livro, -1, cur)
        print(f"✅ Exemplar {id_exemplar} excluído.")

def excluir_livro():
    id_livro = int(input("ID do Livro a excluir: "))
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM livros WHERE id_livros = %s;", (id_livro,))
        print(f"✅ Livro {id_livro} + exemplares removidos.")

# ---------- EMPRÉSTIMOS ----------
def criar_emprestimo():
    id_usuario = int(input("ID do Usuário: "))
    id_exemplar = int(input("ID do Exemplar (disponível): "))
    data_dev   = input("Data devolução (YYYY-MM-DD, opcional): ") or None
    with get_connection() as conn, conn.cursor() as cur:
        # 1) verifica disponibilidade
        cur.execute("""
            SELECT id_livro, status FROM exemplares
            WHERE id_exemplar=%s;
        """, (id_exemplar,))
        row = cur.fetchone()
        if not row:
            print("❌ Exemplar inexistente.")
            return
        id_livro, status = row
        if status != 'disponivel':
            print("❌ Exemplar já emprestado!")
            return
        # 2) grava empréstimo
        cur.execute("""
            INSERT INTO emprestimos (id_usuario,id_exemplar,data_devolucao)
            VALUES (%s,%s,%s) RETURNING id_emprestimo;
        """, (id_usuario, id_exemplar, data_dev))
        id_emp = cur.fetchone()[0]
        # 3) muda status exemplar + estoque -1
        cur.execute("""
            UPDATE exemplares SET status='emprestado'
            WHERE id_exemplar=%s;
        """, (id_exemplar,))
        atualiza_estoque(id_livro, -1, cur)
        print(f"✅ Empréstimo {id_emp} registrado.")

def devolver_livro():
    id_exemplar = int(input("ID do Exemplar devolvido: "))
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id_livro, status FROM exemplares
            WHERE id_exemplar=%s;
        """, (id_exemplar,))
        row = cur.fetchone()
        if not row:
            print("❌ Exemplar inexistente.")
            return
        id_livro, status = row
        if status != 'emprestado':
            print("❌ Este exemplar não está emprestado.")
            return
        # atualizar status + estoque +1
        cur.execute("""
            UPDATE exemplares SET status='disponivel'
            WHERE id_exemplar=%s;
        """, (id_exemplar,))
        atualiza_estoque(id_livro, 1, cur)
        print("✅ Exemplar devolvido e estoque ajustado.")

def listar_emprestimos():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT e.id_emprestimo,u.nome,l.titulo,ex.id_exemplar,e.data_devolucao
            FROM emprestimos e
            JOIN usuarios   u ON u.id_usuario = e.id_usuario
            JOIN exemplares ex ON ex.id_exemplar = e.id_exemplar
            JOIN livros     l ON l.id_livros   = ex.id_livro
            ORDER BY e.id_emprestimo;
        """)
        for e in cur.fetchall():
            print(f"{e['id_emprestimo']}: {e['nome']} pegou '{e['titulo']}' (Ex {e['id_exemplar']}) – devolução {e['data_devolucao']}")

# ---------- MENU ----------
def menu():
    opcoes = {
        '1': ("Criar usuário", criar_usuario),
        '2': ("Listar usuários", listar_usuarios),
        '3': ("Criar livro", criar_livro),
        '4': ("Listar livros", listar_livros),
        '5': ("Adicionar exemplares", adicionar_exemplares),
        '6': ("Listar exemplares", listar_exemplares),
        '7': ("Criar empréstimo", criar_emprestimo),
        '8': ("Listar empréstimos", listar_emprestimos),
        '9': ("Devolver livro", devolver_livro),
        '10':("Excluir exemplar", excluir_exemplar),
        '11':("Excluir livro", excluir_livro),
        '0': ("Sair", None)
    }

    while True:
        print("\n=== MENU BIBLIOTECA ===")
        for k,(txt,_) in opcoes.items():
            print(f"{k}. {txt}")
        escolha = input("Escolha: ")

        if escolha == '0':
            print("👋 Até logo!")
            break
        func = opcoes.get(escolha, (None,None))[1]
        if func:
            func()
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    menu()
