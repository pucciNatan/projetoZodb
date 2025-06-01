from zodbCRUD import *

def menu():
    opcoes = {
        "1": ("Criar usuário", criar_usuario),
        "2": ("Listar usuários", listar_usuarios),
        "3": ("Criar livro", criar_livro),
        "4": ("Listar livros", listar_livros),
        "5": ("Adicionar exemplares", adicionar_exemplares),
        "6": ("Listar exemplares", listar_exemplares),
        "7": ("Criar empréstimo", criar_emprestimo),
        "8": ("Listar empréstimos", listar_emprestimos),
        "9": ("Devolver livro", devolver_livro),
        "10": ("Excluir exemplar", excluir_exemplar),
        "11": ("Excluir livro", excluir_livro),
        "0": ("Sair", None),
    }

    while True:
        print("\n=== MENU BIBLIOTECA ZODB ===")
        for k, (txt, _) in opcoes.items():
            print(f"{k}. {txt}")
        escolha = input("Escolha: ")
        if escolha == "0":
            print("👋 Até logo!")
            break
        funcao = opcoes.get(escolha, (None, None))[1]
        if funcao:
            funcao()
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    try:
        menu()
    finally:
        gravar()          # garante commit final
        conexao.close()
        db.close()