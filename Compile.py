import lark

cpt = 0

op2asm = {"+": "add rax, rbx", "-": "sub rax, rbx"}

def compile(ast):
    asmString = ""
    asmString += "extern printf, atol, puts ; déclaration des fonctions externes\n"
    asmString += "global main ; déclaration main\n"
    asmString += "section .data ; section des données\n"
    asmString += "long_format: db '%lld', 10, 0 ; format pour les int64_t\n"
    asmString += "format : db '%s', 0 ; format pour les chaînes\n"
    asmString += "argc : dq 0 ; copie de argc\n"
    asmString += "argv : dq 0 ; copie de argv\n"
    asmString += "buffer: times 100 db 0 ; buffer pour la concaténation de chaînes\n\n;Declaration vars\n"
    asmVar, vars = variable_declaration(ast.children[0])
    asmString += asmVar
    asmString += "section .text ; instructions\n"
    asmString += "main :\n"
    asmString += "push rbp; Set up the stack. Save rbp\n"
    asmString += "mov rbp, rsp ; Save rbp\n"
    asmString += "mov [argc], rdi\n"
    asmString += "mov [argv], rsi\n\n;Init vars\n"
    asmString += initMainVar(ast.children[0])+ "\n;Commandes:\n"
    asmString += compilCommand(ast.children[1])+ "\n;Return:\n"
    asmString += compilReturn(ast.children[2])
    asmString += "pop rbp\n"
    asmString += "xor rax, rax\n"
    asmString += "ret\n"
    return asmString

def variable_declaration(ast):
    asmVar = ""
    vars = set()
    if ast.data != "liste_vide":
        for child in ast.children:
            if child.value.startswith('s'):
                asmVar += f"{child.value}: times 100 db 0\n"
            else:
                asmVar += f"{child.value}: dq 0\n"
            vars.add(child.value)
    print(vars)
    return asmVar, vars

def initMainVar(ast):
    asmVar = ""
    if ast.data != "liste_vide":
        index = 0
        for child in ast.children:
            asmVar += "mov rbx, [argv]\n"
            asmVar += f"mov rdi, [rbx + { 8*(index+1)}]\n"
            asmVar += f"mov [{child.value}], rdi\n"
            asmVar += "xor rax, rax\n"
            asmVar += "call atol\n"
            index += 1
    return asmVar

def compilReturn(ast):
    asm = compilExpression(ast)
    asm += "mov rsi, rax \n"
    asm += "mov rdi, long_format \n"
    asm += "xor rax, rax \n"
    asm += "call printf \n"
    return asm

def compilCommand(ast):
    asmVar = ""
    if ast.data == "com_while":
        asmVar = compilWhile(ast)
    elif ast.data == "com_if":
        asmVar = compilIf(ast)
    elif ast.data == "com_sequence":
        asmVar = compilSequence(ast)
    elif ast.data == "com_asgt":
        asmVar = compilAsgt(ast)
    elif ast.data == "com_printf":
        asmVar = compilPrintf(ast)
    elif ast.data == "com_charAt":
        asmVar = compilCharAt(ast)
    return asmVar

def compilWhile(ast):
    global cpt
    cpt += 1
    return f""" 
            loop{cpt} : {compilExpression(ast.children[0])}
                cmp rax, 0
                jz fin{cpt}
                {compilCommand(ast.children[1])}
                jmp loop{cpt}
            fin{cpt} :
        """

def compilIf(ast):
    global cpt
    cpt += 1
    return f""" 
            {compilExpression(ast.children[0])}
            cmp rax, 0
            jz fin{cpt}
            {compilCommand(ast.children[1])}
            fin{cpt} :
        """

def compilSequence(ast):
    asm = ""
    for child in ast.children:
        asm += compilCommand(child)
    return asm

def compilAsgt(ast):
    asm = compilExpression(ast.children[1])
    asm += f"mov [{ast.children[0].value}], rax \n"
    return asm

def compilPrintf(ast):
    asm = compilExpression(ast.children[0])
    asm += "xor rax, rax \n"
    asm += "call printf \n"
    return asm

def compilExpression(ast):
    if ast.data == "exp_variable_string":
        return f"mov rsi, [{ast.children[0].value}]\nmov rdi, format\n"
    elif ast.data == "exp_variable":
        return f"mov rsi, [{ast.children[0].value}]\nmov rdi, long_format\n"
    elif ast.data ==  "exp_nombre":
        return f"mov rsi, {ast.children[0].value}\nmov rdi, long_format\n"
    elif ast.data ==  "exp_string":
        return f"mov rsi, {ast.children[0].value}\nmov rdi, format\n"
    elif ast.data == "exp_binaire":
        return f"""
                {compilExpression(ast.children[2])}
                push rax
                {compilExpression(ast.children[0])}
                pop rbx
                add rax, rbx
                """
    return "; expression non reconnue\n"

# Fonction d'assembly pour `charAt`
def compilCharAt():
    return """
    ; charAt(chaine, position)
    ; Retourne le caractère ASCII à la position donnée dans la chaîne
    global charAt
    charAt:
        push rbp
        mov rbp, rsp
        mov rdi, [rbp+16] ; chaîne
        mov rsi, [rbp+24] ; position
        add rdi, rsi
        movzx rax, byte [rdi]
        pop rbp
        ret
    """

# Ajouter le code `charAt` dans le segment de texte
def compile_with_charAt(ast):
    asm = compile(ast)
    asm += charAt()
    return asm

#print(compile_with_charAt(t))
