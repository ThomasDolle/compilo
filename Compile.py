import lark

global cpt
cpt = 0

def compile(ast):
    asmString = ""
    asmString = asmString + "extern printf, atoi ; declaration des fonctions externes\n"
    asmString = asmString + "global main ; declaration main\n"
    asmString = asmString + "section .data ; section des donnees\n"
    asmString = asmString + "long_format: db '%lld', 10, 0 ; format pour les int64_t\n"
    asmString += "format : db '%s', 0 ; format pour les chaînes\n" 
    asmString = asmString + "argc : dq 0 ; copie de argc\n"
    asmString = asmString + "argv : dq 0 ; copie de argv\n"
    asmString += "buffer: times 100 db 0 ; buffer pour la concaténation de chaînes\n\n;Declaration vars\n" 
    asmVar, vars = variable_declaration(ast.children[1])
    asmVarLoc, varsLoc = variable_locales_declaration(vars, ast.children[0], ast.children[2])
    asmVar = asmVar + asmVarLoc
    asmString = asmString + asmVar
    asmString = asmString + "section .text ; instructions\n"
    asmString = asmString + "main :\n"
    asmString += "push rbp; Set up the stack. Save rbp\n"
    asmString += "mov rbp, rsp ; Save rbp\n" 
    asmString += "mov [argc], rdi\n"
    asmString += "mov [argv], rsi\n"
    asmString += initMainVar(vars)+ "\n;Commandes:\n"
    vars = vars | varsLoc
    asmString += compilCommand(ast.children[2], vars) + "\n;Return:\n"
    asmString += compilReturn(ast.children[3])
    asmString += "pop rbp\n"
    asmString += "xor rax, rax\n"
    asmString += "ret\n"
    return asmString

# Ici, on s'occupe des variables dans les arguments de la fonction main
def variable_declaration(ast):
    asmVar = ""
    vars = dict()
    if ast.data != "liste_vide":
        for child in ast.children:
            asmVar += f"{child.value}: dq 0\n"
            #vars[child.value] = "int" #Dinojan
            vars[child.value] = f"{child.type}"
    return asmVar, vars

# On cherche les déclarations de variables locales dans les commandes
def cherche_variables_locales(tree):
    if tree.data in ("com_struct_declaration", "com_int_declaration"):
        return [tree]
    elif tree.data == "com_sequence":
        commands = []
        for child in tree.children:
            commands += cherche_variables_locales(child)
        return commands
    elif tree.data == "com_if":
        return cherche_variables_locales(tree.children[1]) + cherche_variables_locales(tree.children[2])
    elif tree.data == "com_while":
        return cherche_variables_locales(tree.children[1])  
    return []

# On crée les variables locales
def variable_locales_declaration(varDict, structDeclar, commandes):

    structDict = dict()
    varLocalDict = dict()

    # On stocke les attributs des structs dans un dictionnaire
    if structDeclar.data == "liste_def_struct_normale":
        for childStruct in structDeclar.children:
            structName = childStruct.children[0].value
            if childStruct.children[1].data != "liste_attribut_vide":
                attributes =  []
                for child in childStruct.children[1].children:
                    attributes.append(child.value)
                structDict[structName] = attributes

    # On crée les variables locales (int et struct)
    asmVar = ""
    commands = cherche_variables_locales(commandes)
    for command in commands:
        if command.data == "com_int_declaration":
            for child in command.children:
                if child.value in varDict:
                    raise Exception(f"Variable {child.value} already declared")
                else:  
                    asmVar += f"{child.value}: dq 0\n"
                    varLocalDict[child.value] = "int"
        elif command.data == "com_struct_declaration":
            name = command.children[0].value
            info = name.split("_")
            structName, varName = info[1], info[2]
            if structName not in structDict:
                raise Exception(f"Struct {structName} does not exist in struct {structName}")
            if varName not in varDict:
                raise Exception(f"Variable {varName} does not exist in struct {structName}")
            for attribute in structDict[structName]:
                varLocalDict[f"{name}"] = "struct"
                asmVar += creer_variables_asm(name, attribute, structDict, varLocalDict)
    return asmVar, varLocalDict

# Fonction pour créer les variables locales des structs (récursivement)
def creer_variables_asm(name, attribute, structDict, varLocalDict):
    attributeInfo = attribute.split()
    if attributeInfo[0] in ("string", "int"):
        varLocalDict[f"{name}_{attributeInfo[1]}"] = attributeInfo[0]
        return f"{name}_{attributeInfo[1]}: dq 0\n"
    else: 
        asm = ""
        varLocalDict[f"{name}_{attributeInfo[2]}"] = attributeInfo[0]
        for attributeStruct in structDict[attributeInfo[1]]:
            newName = f"{name}_{attributeInfo[2]}"
            asm += creer_variables_asm(newName, attributeStruct, structDict, varLocalDict)
        return asm

# On initialise les variables des arguments de la fonction main
def initMainVar(vars):
    asmVar = ""
    index = 0
    for key, _ in vars.items():
        asmVar += "mov rbx, [argv]\n"
        asmVar += f"mov rdi, [rbx + { 8*(index+1)}]\n"
        if vars[key] == "VARIABLE":
            asmVar += "xor rax, rax\n"
            asmVar += "call atoi\n"
            asmVar += f"mov [{key}], rax\n"
        elif vars[key] == "VARIABLE_STRING":
            asmVar += f"mov [{key}], rdi\n"
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

def compilCommand(ast, vars):
    asmVar = ""
    if ast.data == "com_while":
        asmVar = compilWhile(ast, vars)
    elif ast.data == "com_if":
        asmVar = compilIf(ast, vars)
    elif ast.data == "com_sequence":
        asmVar = compilSequence(ast, vars)
    elif ast.data == "com_assignation":
        asmVar = compilAsgt(ast)
    elif ast.data == "com_printf":
        asmVar = compilPrintf(ast)
    elif ast.data == "com_assignation_struct_attribut":
        asmVar = compilAssignationStructAttribut(ast, vars)
    return asmVar

def compilWhile(ast, vars):
    global cpt
    cpt += 1
    return f""" 
            loop{cpt} : {compilExpression(ast.children[0])}
                cmp rax, 0
                jz fin{cpt}
                {compilCommand(ast.children[1], vars)}
                jmp loop{cpt}
            fin{cpt} :
        """

def compilIf(ast, vars):
    global cpt
    cpt += 1
    return f""" 
            {compilExpression(ast.children[0])}
            cmp rax, 0
            jz else{cpt}
            {compilCommand(ast.children[1], vars)}
            jmp fin{cpt}
            else{cpt} :
            {compilCommand(ast.children[2], vars)}
            fin{cpt} :
        """

def compilSequence(ast, vars):
    asm = ""
    for child in ast.children :
        asm += compilCommand(child, vars)
    return asm

def compilAsgt(ast):
    asm = compilExpression(ast.children[1])
    asm += f"mov [{ast.children[0].value}], rax \n"
    return asm

# On compile les assignations de variables de structs en vérifiant le type des variables
def compilAssignationStructAttribut(ast, vars):
    transform = ast.children[0].value.replace(".", "_")
    asm = ""
    if vars[transform] == "int" and ast.children[1].data != "exp_struct":
        asm = compilExpression(ast.children[1])
        asm += f"mov [{transform}], rax \n"
    elif vars[transform] == "int" and vars[ast.children[1].children[0].value] == "int":
        asm = compilExpression(ast.children[1])
        asm += f"mov [{transform}], rax \n"
    elif vars[transform] == "struct" and vars[ast.children[1].children[0].value] == "struct":
        for key, value in vars.items():
            if key.startswith(transform) and value == "int":
                suffix = key[len(transform):]
                asm += f"mov rax, [{ast.children[1].children[0].value + suffix}]\n"
                asm += f"mov [{key}], rax\n"
    return asm

def compilPrintf(ast):
    if ast.data == "exp_struct_attribut":
        transform = ast.children[0].value.replace(".", "_")
        ast.children[0].value = transform
    asm = compilExpression(ast.children[0])
    asm += "mov rsi, rax \n"
    if ast.children[0].data == "exp_variable_string" or ast.children[0].data == "exp_string":
        asm += f"mov rdi, format\n"
    elif ast.children[0].data == "exp_variable" or ast.children[0].data == "exp_nombre":
        asm += f"mov rdi, long_format\n"
    asm += "xor rax, rax \n"
    asm += "call printf \n"
    return asm

def compilExpression(ast):
    if ast.data == "exp_variable_string":
        return f"mov rax, [{ast.children[0].value}]\n"
    elif ast.data == "exp_variable":
        return f"mov rax, [{ast.children[0].value}]\n"
    elif ast.data ==  "exp_string":
        return f"mov rax, {ast.children[0].value}\n"
    elif ast.data ==  "exp_nombre":
        return f"mov rax, {ast.children[0].value}\n"
    elif ast.data == "exp_struct":
        ast.children[0].value = ast.children[0].value.replace(".", "_")
        return f"mov rax, [{ast.children[0].value}]\n"
    elif ast.data == "exp_struct_attribut":
        ast.children[0].value = ast.children[0].value.replace(".", "_")
        print(f"mov rax, [{ast.children[0].value}]\n")
        return f"mov rax, [{ast.children[0].value}]\n"
    elif ast.data == "exp_binaire":
        if ast.children[1].value == "+":
            return f"""
                    {compilExpression(ast.children[2])}
                    push rax
                    {compilExpression(ast.children[0])}
                    pop rbx
                    add rax, rbx
                    """
        elif ast.children[1].value == "-":
            return f"""
                    {compilExpression(ast.children[2])}
                    push rax
                    {compilExpression(ast.children[0])}
                    pop rbx
                    sub rax, rbx
                    """
        elif ast.children[1].value == "*":
            return f"""
                    {compilExpression(ast.children[2])}
                    push rax
                    {compilExpression(ast.children[0])}
                    pop rbx
                    imul rax, rbx
                    """
        elif ast.children[1].value == ">":
            return f"""
                    {compilExpression(ast.children[2])}
                    push rax
                    {compilExpression(ast.children[0])}
                    pop rbx
                    cmp rax, rbx
                    setg al
                    movzx rax, al
                    """
        elif ast.children[1].value == "<":
            return f"""
                    {compilExpression(ast.children[2])}
                    push rax
                    {compilExpression(ast.children[0])}
                    pop rbx
                    cmp rax, rbx
                    setl al
                    movzx rax, al
                    """
    else: 
        return f";expression inconnue {ast}"
    return ""