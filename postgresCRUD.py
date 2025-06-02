import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import errors

DB_CONFIG = dict(
    host="localhost",
    port=5432,
    dbname="polls",
    user="docker",
    password="docker"
)

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def preparar_banco():
    comandos_sql = """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_exemplar') THEN
            CREATE TYPE status_exemplar AS ENUM ('disponivel', 'emprestado');
        END IF;
    END$$;

    CREATE TABLE IF NOT EXISTS livros (
        id_livros  SERIAL PRIMARY KEY,
        titulo     VARCHAR(150) NOT NULL,
        categoria  VARCHAR(60)  NOT NULL,
        autor      VARCHAR(100) NOT NULL,
        estoque    INT          NOT NULL CHECK (estoque >= 0)
    );

    CREATE TABLE IF NOT EXISTS exemplares (
        id_exemplar SERIAL PRIMARY KEY,
        status      status_exemplar NOT NULL DEFAULT 'disponivel',
        id_livro    INT NOT NULL REFERENCES livros(id_livros) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario SERIAL PRIMARY KEY,
        nome       VARCHAR(60)  NOT NULL,
        sobrenome  VARCHAR(80)  NOT NULL,
        idade      INT          NOT NULL CHECK (idade >= 0)
    );

    CREATE TABLE IF NOT EXISTS emprestimos (
        id_emprestimo  SERIAL PRIMARY KEY,
        id_usuario     INT  NOT NULL REFERENCES usuarios(id_usuario)   ON DELETE CASCADE,
        id_exemplar    INT  NOT NULL REFERENCES exemplares(id_exemplar) ON DELETE CASCADE,
        data_devolucao DATE
    );

    CREATE INDEX IF NOT EXISTS idx_emprestimos_usuario  ON emprestimos (id_usuario);
    CREATE INDEX IF NOT EXISTS idx_emprestimos_exemplar ON emprestimos (id_exemplar);
    """

    with get_connection() as conn, conn.cursor() as cur:
        try:
            cur.execute("SELECT 1 FROM livros LIMIT 1;")
        except errors.UndefinedTable:
            conn.rollback()
            cur.execute(comandos_sql)
            print("Estrutura do banco criada com sucesso.")

# ---------- utilitário ----------
def atualiza_estoque(id_livro, qtd, cur):
    cur.execute("""
        UPDATE livros
        SET estoque = estoque + %s
        WHERE id_livros = %s;
    """, (qtd, id_livro))

def criar_usuario():
    nome = input("Nome: ")
    sobrenome = input("Sobrenome: ")
    idade = int(input("Idade: "))
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO usuarios (nome, sobrenome, idade)
            VALUES (%s,%s,%s) RETURNING id_usuario;
        """, (nome, sobrenome, idade))
        print(f"Usuário criado (ID {cur.fetchone()[0]})")

def listar_usuarios():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM usuarios;")
        for u in cur.fetchall():
            print(f"{u['id_usuario']}: {u['nome']} {u['sobrenome']} – {u['idade']} anos")

def criar_livro():
    titulo = input("Título: ")
    categoria = input("Categoria: ")
    autor = input("Autor: ")
    estoque = int(input("Estoque inicial: "))
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            INSERT INTO livros (titulo, categoria, autor, estoque)
            VALUES (%s,%s,%s,0) RETURNING id_livros;
        """, (titulo, categoria, autor))
        id_livro = cur.fetchone()[0]
        cur.executemany("""
            INSERT INTO exemplares (status,id_livro)
            VALUES ('disponivel',%s);
        """, [(id_livro,)] * estoque)
        atualiza_estoque(id_livro, estoque, cur)
        print(f"Livro {id_livro} criado com {estoque} exemplares")

def listar_livros():
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM livros;")
        for l in cur.fetchall():
            print(f"{l['id_livros']}: '{l['titulo']}' – Estoque disponível: {l['estoque']}")

def adicionar_exemplares():
    id_livro = int(input("ID do Livro: "))
    qtd = int(input("Quantos exemplares adicionar?: "))
    with get_connection() as conn, conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO exemplares (status,id_livro)
            VALUES ('disponivel',%s);
        """, [(id_livro,)] * qtd)
        atualiza_estoque(id_livro, qtd, cur)
        print(f"{qtd} exemplares adicionados ao livro {id_livro}")

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
        cur.execute("""
            SELECT id_livro, status FROM exemplares
            WHERE id_exemplar = %s;
        """, (id_exemplar,))
        row = cur.fetchone()
        if not row:
            print("Exemplar não encontrado.")
            return
        id_livro, status = row
        cur.execute("DELETE FROM exemplares WHERE id_exemplar = %s;", (id_exemplar,))
        if status == 'disponivel':
            atualiza_estoque(id_livro, -1, cur)
        print(f"Exemplar {id_exemplar} excluído.")

def excluir_livro():
    id_livro = int(input("ID do Livro a excluir: "))
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM livros WHERE id_livros = %s;", (id_livro,))
        print(f"Livro {id_livro} + exemplares removidos.")

def criar_emprestimo():
    id_usuario = int(input("ID do Usuário: "))
    id_exemplar = int(input("ID do Exemplar (disponível): "))
    data_dev = input("Data devolução (YYYY-MM-DD, opcional): ") or None
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id_livro, status FROM exemplares
            WHERE id_exemplar=%s;
        """, (id_exemplar,))
        row = cur.fetchone()
        if not row:
            print("Exemplar inexistente.")
            return
        id_livro, status = row
        if status != 'disponivel':
            print("Exemplar já emprestado!")
            return
        cur.execute("""
            INSERT INTO emprestimos (id_usuario,id_exemplar,data_devolucao)
            VALUES (%s,%s,%s) RETURNING id_emprestimo;
        """, (id_usuario, id_exemplar, data_dev))
        id_emp = cur.fetchone()[0]
        cur.execute("""
            UPDATE exemplares SET status='emprestado'
            WHERE id_exemplar=%s;
        """, (id_exemplar,))
        atualiza_estoque(id_livro, -1, cur)
        print(f"Empréstimo {id_emp} registrado.")

def devolver_livro():
    id_exemplar = int(input("ID do Exemplar devolvido: "))
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id_livro, status FROM exemplares
            WHERE id_exemplar=%s;
        """, (id_exemplar,))
        row = cur.fetchone()
        if not row:
            print("Exemplar inexistente.")
            return
        id_livro, status = row
        if status != 'emprestado':
            print("Este exemplar não está emprestado.")
            return

        cur.execute("""
            DELETE FROM emprestimos
            WHERE id_exemplar = %s;
        """, (id_exemplar,))

        cur.execute("""
            UPDATE exemplares SET status='disponivel'
            WHERE id_exemplar=%s;
        """, (id_exemplar,))
        atualiza_estoque(id_livro, 1, cur)
        print("Exemplar devolvido, empréstimo removido e estoque ajustado.")

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

def editar_usuario():
    id_usuario = int(input("ID do usuário a editar: "))
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
        usuario = cur.fetchone()
        if not usuario:
            print("Usuário não encontrado.")
            return

        print(f"Editando: {usuario['nome']} {usuario['sobrenome']} – {usuario['idade']} anos")
        novo_nome = input(f"Novo nome ({usuario['nome']}): ") or usuario['nome']
        novo_sobrenome = input(f"Novo sobrenome ({usuario['sobrenome']}): ") or usuario['sobrenome']
        nova_idade = input(f"Nova idade ({usuario['idade']}): ") or usuario['idade']

        cur.execute("""
            UPDATE usuarios
            SET nome = %s, sobrenome = %s, idade = %s
            WHERE id_usuario = %s;
        """, (novo_nome, novo_sobrenome, int(nova_idade), id_usuario))
        print("Usuário atualizado com sucesso.")

def editar_livro():
    id_livro = int(input("ID do livro a editar: "))
    with get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM livros WHERE id_livros = %s;", (id_livro,))
        livro = cur.fetchone()
        if not livro:
            print("Livro não encontrado.")
            return

        print(f"Editando: '{livro['titulo']}' – {livro['categoria']} – {livro['autor']}")
        novo_titulo = input(f"Novo título ({livro['titulo']}): ") or livro['titulo']
        nova_categoria = input(f"Nova categoria ({livro['categoria']}): ") or livro['categoria']
        novo_autor = input(f"Novo autor ({livro['autor']}): ") or livro['autor']

        cur.execute("""
            UPDATE livros
            SET titulo = %s, categoria = %s, autor = %s
            WHERE id_livros = %s;
        """, (novo_titulo, nova_categoria, novo_autor, id_livro))
        print("Livro atualizado com sucesso.")

def excluir_usuario():
    id_usuario = int(input("ID do usuário a excluir: "))
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
        if not cur.fetchone():
            print("Usuário não encontrado.")
            return

        cur.execute("""
            SELECT COUNT(*) FROM emprestimos
            WHERE id_usuario = %s;
        """, (id_usuario,))
        emprestimos = cur.fetchone()[0]
        if emprestimos > 0:
            print(f"Não é possível excluir: o usuário possui {emprestimos} empréstimo(s) registrado(s).")
            return

        cur.execute("DELETE FROM usuarios WHERE id_usuario = %s;", (id_usuario,))
        print(f"Usuário {id_usuario} excluído com sucesso.")
