a = 10
b = 3
print("soma:",a +b)

x = 5
y = 8

print(x < y)

print(x)

contador = 10
print(contador)

contador += 5
print(contador)

nota = 5
if nota >=7:
    print("aprovado")
elif nota >= 5:
    print("Recuperação")
else:
    print("Reprovado")

idade = 21
tem_carteira_motorista = False

if idade>=18:
    if tem_carteira_motorista:
        print("Pode dirigir")
    else:
        print("Precisa de carteira para dirigir")
else:
    print("Não pode dirigir, é menor de idade")

experiencia = 3

if idade >=21 and experiencia >2:
    print("Elegivel para a vaga")
else:
    print("Não é elegivel para a vaga")

numeros = [1, 2, 3]
numeros.append(4)
print(numeros) # Saída: [1, 2, 3, 4]

itens = ["a", "b", "c", "d"]
removido = itens.pop(2)
print(removido)
print(itens)
itens.sort()
print(itens)

nomes = ["pedro", "lucas", "henrique"]
for nome in nomes:
    print(f"Olá, {nome}!")