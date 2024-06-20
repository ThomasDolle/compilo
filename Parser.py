import lark

grammaire = """
%import common.SIGNED_NUMBER  //Importation des nombres signés depuis la bibliothèque lark.
%import common.ESCAPED_STRING  // Importation des chaînes échappées.
%import common.WS  // Importation des espaces blancs.
%ignore WS  // Ignorer les espaces blancs.

OPBINAIRE : /[+*\/&><]/|"<="|">="|"-"|">>"
VARIABLE : /(?!s)(?!struct_)[a-zA-Z_][a-zA-Z_0-9]*/ // interdit les varibles commençant par struct_ et par s
ATTRIBUT : /[a-z]+/
NOMBRE : SIGNED_NUMBER 
STRUCT : "struct_" VARIABLE "_" VARIABLE // struct_C_X
STRUCT_ATTRIBUT : STRUCT ("." ATTRIBUT)* // struct_C_X.a
TYPE : "int " ATTRIBUT | "struct " VARIABLE " " ATTRIBUT // int a | struct C y
VARIABLE_STRING : /[s][a-zA-Z0-9]*/
STRING : ESCAPED_STRING

expression : STRUCT -> exp_struct
| STRUCT_ATTRIBUT -> exp_struct_attribut
| VARIABLE_STRING -> exp_variable_string
| VARIABLE -> exp_variable
| NOMBRE -> exp_nombre
| STRING -> exp_string
| expression OPBINAIRE expression -> exp_binaire
| "len" "(" VARIABLE_STRING ")" -> exp_charlen
| "charAt" "(" VARIABLE_STRING "," (NOMBRE | VARIABLE) ")" -> exp_charat

commande : VARIABLE "=" expression ";" -> com_asgt
| STRUCT_ATTRIBUT "=" expression ";" -> com_assignation_struct_attribut // struct_C_X.a = 5;
| "printf" "(" expression ")" ";" -> com_printf
| commande+ -> com_sequence
| "while" "(" expression ")" "{" commande "}" -> com_while
| "if" "(" expression ")" "{" commande "}" "else" "{" commande "}" -> com_if
| "struct " STRUCT ";" -> com_struct_declaration
| "int " VARIABLE ";" -> com_int_declaration

liste_var : -> liste_vide
| (VARIABLE_STRING | VARIABLE) ("," (VARIABLE_STRING | VARIABLE))* -> liste_normale

liste_attribut : -> liste_attribut_vide
        | TYPE ("," TYPE)* -> liste_attribut_normale // int a, struct C y

definition_struct : "struct" VARIABLE "{" liste_attribut "}" ";" -> def_struct // struct C {int a, struct C y} ;

liste_def_struct : -> liste_def_struct_vide
        | definition_struct+ -> liste_def_struct_normale

programme : liste_def_struct "main" "(" liste_var ")" "{" commande "return" "(" expression ")" ";" "}" -> prog_main
"""

parser = lark.Lark(grammaire, start="programme")

'''
t = parser.parse("""main(x,y){
                 while(x) {
                    y = y + 1;
                    printf(y);
                 }
                 return (y);
                }
                 """)


t2 = parser.parse("""main(x, y, s1) {
                 while (x) {
                    y = y + 1;
                    printf(y);
                    s1 = s1 + "bcd";
                    printf(s1);
                 }
                 return (y);
                }
                 """)
'''

def pretty_printer_def_struct(t):
    return "struct %s { %s };" % (t.children[0].value, pretty_printer_liste_attribut(t.children[1]))

def pretty_printer_liste_def_struct(t):
    if t.data == "liste_def_struct_vide":
        return ""
    return "\n".join([pretty_printer_def_struct(child) for child in t.children])

def pretty_printer_programme(t):
    def_struct = pretty_printer_liste_def_struct(t.children[0])
    a = "main (%s) { \n %s \n return (%s);\n} " % (pretty_printer_liste_var(t.children[1]), 
                                                pretty_printer_commande(t.children[2]), 
                                                pretty_printer_expression(t.children[3]))
    return f"{def_struct} \n{a}"

def pretty_printer_liste_var(t):
    if t.data == "liste_vide":
        return ""
    return ", ".join([child.value for child in t.children])

def pretty_printer_liste_attribut(t):
    if t.data == "liste_attribut_vide":
        return ""
    return ", ".join([child.value for child in t.children])
    
def pretty_printer_commande(t):
    if t.data in ("com_assignation", "com_assignation_struct_attribut"):
        return f"{t.children[0].value} = {pretty_printer_expression(t.children[1])};"
    if t.data == "com_printf":
        return f"printf({pretty_printer_expression(t.children[0])});"
    if t.data == "com_sequence":
        return "\n ".join([pretty_printer_commande(child) for child in t.children])
    if t.data == "com_while":
        return "while (%s) { \n %s \n }" % (pretty_printer_expression(t.children[0]), pretty_printer_commande(t.children[1]))
    if t.data == "com_if":
        return "if (%s) { \n %s \n } else { \n %s \n }" % (pretty_printer_expression(t.children[0]), pretty_printer_commande(t.children[1]), pretty_printer_commande(t.children[2]))
    if t.data == "com_struct_declaration":
        return f"struct {t.children[0]};"
    if t.data == "com_int_declaration":
        return f"int {t.children[0].value};"

def pretty_printer_expression(t):
    if t.data in ("exp_variable", "exp_nombre", "exp_struct", "exp_struct_attribut"):
        return t.children[0].value
    if t.data == "exp_struct_attribut":
        return pretty_printer_expression(t.children[0]) + "." + t.children[1].value
    return f"{pretty_printer_expression(t.children[0])} {t.children[1].value} {pretty_printer_expression(t.children[2])}"



'''

parser = lark.Lark(grammaire, start="programme")
parser2 = lark.Lark(grammaire, start="expression")

final2 = parser.parse("""
                 struct C {int a, int b} ;
                 struct A {int a, struct C y} ;
                 main(X, Z) {
                    struct_C_X.a = 5;
                    X = 6; 
                    struct_A_Z.y = struct_C_X;
                    return (struct_A_Z.y.b);
                 }
                 """)

final = parser.parse("""
                    struct C {int a, int b} ;
                    struct A {int a, struct C y} ;
                    main(X, Z) {
                        struct struct_C_X;
                        struct struct_A_Z;
                        int j;
                        struct_C_X.a = 5;
                        struct_C_Z.y = struct_C_X;
                        X = 6; 
                        return (X);
                    }
                    """)

#print(pretty_print(t))
#print(t)
'''
