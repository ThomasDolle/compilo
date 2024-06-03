import lark

cpt = 0

def compile(ast):
    asmString = ""
    asmString = asmString + "extern printf, atoi ;déclaration des fonctions externes\n"
    asmString = asmString + "global main ; declaration main\n"
    asmString = asmString + "section .data ; section des données\n"
    asmString = asmString + "long_format: db '%lld',10, 0 ; format pour les int64_t\n"
    asmString = asmString + "argc : dq 0 ; copie de argc\n"
    asmString = asmString + "argv : dq 0 ; copie de argv\n"
    asmVar, vars = variable_declaration(ast.children[0])
    asmString = asmString + asmVar
    asmString = asmString + "section .text ; instructions\n"
    asmString = asmString + "main :\n"
    asmString += "push rbp; Set up the stack. Save rbp\n"
    asmString += "mov [argc], rdi\n"
    asmString += "mov [argv], rsi\n"
    asmString += initMainVar(ast.children[0])
    asmString += compilCommand(ast.children[1])
    asmString += compilReturn(ast.children[2])
    asmString += "pop rbp\n"
    asmString += "xor rax, rax\n"
    asmString += "ret\n"
    return asmString

def variable_declaration(ast) :
    asmVar = ""
    vars = set()
    if ast.data != "liste_vide":
        for child in ast.children:
            asmVar += f"{child.value}: dq 0\n"
            vars.add(child.value)
    return asmVar, vars

def initMainVar(ast):
    asmVar = ""
    if ast.data != "liste_vide":
        index = 0
        for child in ast.children:
            asmVar += "mov rbx, [argv]\n"
            asmVar += f"mov rdi, [rbx + { 8*(index+1)}]\n"
            asmVar += "xor rax, rax\n"
            asmVar += "call atoi\n"
            asmVar += f"mov [{child.value}], rax\n"
            index += 1
    return asmVar

def compilReturn(ast):
    return compilPrintf(ast)

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
    for child in ast.children :
        asm +=compilCommand(child)
    return asm

def compilAsgt(ast):
    asm = compilExpression(ast.children[1])
    asm += f"mov [{ast.children[0].value}], rax \n"
    return asm

def compilPrintf(ast):
    asm = compilExpression(ast.children[0])
    asm += "mov rsi, rax \n"
    asm += "mov rdi, long_format \n"
    asm += "xor rax, rax \n"
    asm += "call printf \n"
    return asm

def compilExpression(ast):
    if ast == "VARIABLE":
        return f"mov rax, [{ast.children[0].value}]\n"
    elif ast ==  "NOMBRE":
        return f"mov rax, {ast.children[0].value}\n"
    elif ast == "OPBINAIRE":
        return f"""
                {compilExpression(ast.children[2])}
                push rax
                {compilExpression(ast.children[0])}
                pop rbx
                add rax, rbx
                """
    return ""