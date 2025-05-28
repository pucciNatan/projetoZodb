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
