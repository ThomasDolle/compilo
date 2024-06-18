import lark

global cpt
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
            if child.type == "VARIABLE":
                asmVar += "xor rax, rax\n"
                asmVar += "call atol\n"
                asmVar += f"mov [{child.value}], rax\n"
            elif child.type == "VARIABLE_STRING":
                asmVar += f"mov [{child.value}], rdi\n"
            index += 1
    return asmVar

def compilReturn(ast):
    asm = compilExpression(ast)
    if ast.data == "exp_variable_string" or ast.data == "exp_string":
        asm += f"mov rsi, rax\nmov rdi, format\n"
    elif ast.data == "exp_variable" or ast.data == "exp_nombre":
        asm += f"mov rsi, rax\nmov rdi, long_format\n"
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
    #print le contenu de rax
    asm = compilExpression(ast.children[0])
    if ast.children[0].data == "exp_variable_string" or ast.children[0].data == "exp_string":
        asm += f"mov rsi, rax\nmov rdi, format\n"
    elif ast.children[0].data == "exp_variable" or ast.children[0].data == "exp_nombre":
        asm += f"mov rsi, rax\nmov rdi, long_format\n"
    asm += "xor rax, rax \n"
    asm += "call printf \n"
    return asm

def compilExpression(ast):
    if ast.data == "exp_variable_string":
        return f"mov rax, [{ast.children[0].value}]\n"
    elif ast.data == "exp_variable":
        return f"mov rax, [{ast.children[0].value}]\n"
    elif ast.data ==  "exp_nombre":
        return f"mov rax, {ast.children[0].value}\n"
    elif ast.data ==  "exp_string":
        return f"mov rax, {ast.children[0].value}\n"
    elif ast.data == "exp_binaire":
        asm = ""
        if ast.children[0].data == "exp_variable" and ast.children[2].data == "exp_variable":
            asm += f"""
    {compilExpression(ast.children[2])}
    push rax
    {compilExpression(ast.children[0])}
    pop rbx
    """
            asm += "add rax, rbx\n"
        else:
            asm += compilAddStrings(ast)
        return asm
    elif ast.data == "exp_charlen":
        asm = compilCharLen(ast)
        return asm
    elif ast.data == "exp_charat":
        asm = compilCharAt(ast)
        return asm
    return f"; expression non reconnue{ast.data}\n"

# Fonction d'assembly pour `charAt`
def compilCharAt(ast):
    if ast.children[1].type == "NOMBRE":
        asmVar = f"""
            mov     rdi, [{ast.children[0]}]
            mov     rsi, {ast.children[1]}
            """
    elif ast.children[1].type == "VARIABLE":
        asmVar = f"""
        mov     rdi, [{ast.children[0]}]
        mov     rsi, [{ast.children[1]}]
            """
    global cpt
    cpt+=1
    asmVar += f"""
        mov     rdx, rdi
        mov     rcx, rsi
        mov     rax, 0 ; initialise l'iterator
        loop_start{cpt}:
        cmp     byte [rdx + rax], 0 ; null terminator
        je      loop_end{cpt}
        inc     rax
        cmp     rax, rcx        ; stop si counter = n
        je      loop_end{cpt}
        jmp     loop_start{cpt}
        loop_end{cpt}:
        movzx   eax, byte [rdx + rax - 1] ; nieme char dans rax
        
        mov rsi,rax
        mov rdi, long_format
        """
    return asmVar

def compilCharLen(ast): #returns the len in rsi
    global cpt
    cpt+=1
    return f"""
        mov rdi, [{ast.children[0]}]
        mov     rdx, rdi
        mov     rcx, rsi
        mov     rax, 0 ; initialise l'iterator
        loop_start{cpt}:
        cmp     byte [rdx + rax], 0 ; null terminator
        je      loop_end{cpt}
        inc     rax
        jmp loop_start{cpt}
        loop_end{cpt}:
        mov rsi,rax
        mov rdi, long_format
    """

def compilAddStrings(ast):
    global cpt
    cpt += 3
    asm = f"""
    mov [argc], rdi
    mov [argv], rsi

    mov rbx, rsi

    ; Copy str1 to str3
    mov rsi, [{ast.children[0].children[0]}]    ; rsi pointe maintenant sur argv[1]
    mov rdi, str3         ; Destination str3
    copy_loop{cpt-2}:
        lodsb            ; Load byte from rsi into al
        stosb            ; Store byte in al to rdi
        test al, al      ; Check if the byte is 0 (end of string)
        jnz copy_loop{cpt-2}   ; If not 0, continue the loop
        
    ; Append str2 to str3
    """
    asm += f"""
    ;Calculate length
    mov rdi, [{ast.children[0].children[0]}]
    mov     rdx, rdi
    mov     rcx, rsi
    mov     rax, 0 ; initialise l'iterator
    loop_start{cpt-1}:
    cmp     byte [rdx + rax], 0 ; null terminator
    je      loop_end{cpt-1}
    inc     rax
    jmp loop_start{cpt-1}
    loop_end{cpt-1}:
    """
    asm += f"""
    ;Concatenate
    mov rsi, [{ast.children[2].children[0]}]        ; Source string 2
    mov rdi, str3       ; Destination string 3
    add rdi, rax       ; Move rdi to the end of str1 in str3
    copy_loop{cpt}:
        lodsb            ; Load byte from rsi into al
        stosb            ; Store byte in al to rdi
        test al, al      ; Check if the byte is 0 (end of string)
        jnz copy_loop{cpt}   ; If not 0, continue the loop
    
    mov rax, str3
    mov rsi, rax
    mov rdi, format
    xor rax, rax 
    call printf ;print le resultat, ne supporte pas l'assignation dans rax par ex (pas compatible avec le printf tel quel)
    """
    return asm