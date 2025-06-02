from postgresCRUD import *

def menu():
    opcoes = {
        '1': ("Criar usuário", criar_usuario),
        '2': ("Listar usuários", listar_usuarios),
        '3': ("Editar usuário", editar_usuario),
        '4': ("Excluir usuário", excluir_usuario),
        '5': ("Criar livro", criar_livro),
        '6': ("Listar livros", listar_livros),
        '7': ("Editar livro", editar_livro),
        '8': ("Excluir livro", excluir_livro),
        '9': ("Adicionar exemplares", adicionar_exemplares),
        '10': ("Listar exemplares", listar_exemplares),
        '11': ("Excluir exemplar", excluir_exemplar),
        '12': ("Criar empréstimo", criar_emprestimo),
        '13': ("Listar empréstimos", listar_emprestimos),
        '14': ("Devolver livro", devolver_livro),
        '0': ("Sair", None)
    }

    while True:
        print("\n=== MENU BIBLIOTECA ===")
        for k, (txt, _) in opcoes.items():
            print(f"{k}. {txt}")
        escolha = input("Escolha: ")
        if escolha == '0':
            print("Até logo!")
            break
        func = opcoes.get(escolha, (None, None))[1]
        if func:
            func()
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    preparar_banco()
    menu()