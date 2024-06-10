import lark

grammaire = """
%import common.SIGNED_NUMBER  //Importation des nombres signés depuis la bibliothèque lark.
%import common.ESCAPED_STRING  // Importation des chaînes échappées.
%import common.WS  // Importation des espaces blancs.
%ignore WS  // Ignorer les espaces blancs.

VARIABLE_STRING : /[s][a-zA-Z0-9]*/
VARIABLE : /[a-zA-Z_][a-zA-Z 0-9]*/
NOMBRE : SIGNED_NUMBER
STRING : ESCAPED_STRING
OPBINAIRE: /[+*\/&><]/|">="|"-"|">>"

expression : VARIABLE_STRING -> exp_variable_string
| VARIABLE -> exp_variable
| NOMBRE -> exp_nombre
| STRING -> exp_string
| expression OPBINAIRE expression -> exp_binaire

commande : VARIABLE "=" expression ";" -> com_asgt
| "printf" "(" expression ")" ";" -> com_printf
| commande+ -> com_sequence
| "while" "(" expression ")" "{" commande "}" -> com_while
| "if" "(" expression ")" "{" commande "}" "else" "{" commande "}" -> com_if
| "charAt" "(" VARIABLE_STRING "," (NOMBRE | VARIABLE) ")" ";" -> com_charat
| "len" "(" VARIABLE_STRING ")" ";" -> com_charlen

liste_var : -> liste_vide
| (VARIABLE_STRING | VARIABLE) ("," (VARIABLE_STRING | VARIABLE))* -> liste_normale

programme : "main" "(" liste_var ")" "{" commande "return" "(" expression ")" ";" "}" -> prog_main
"""

parser = lark.Lark(grammaire, start="programme")

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

def pretty_printer_liste_var(t):
    if t.data == "liste_vide":
        return ""
    return ", ".join([u.value for u in t.children])

def pretty_printer_expression(t):
    if t.data in ("exp_variable", "exp_nombre"):
        return t.children[0].value
    elif t.data == "exp_chaine":
        return t.children[0].value
    elif t.data == "exp_charat":
        return f"charAt({t.children[0].value}, {t.children[1].value})"
    return f"{pretty_printer_expression(t.children[0])} {t.children[1].value} {pretty_printer_expression(t.children[2])}"

def pretty_printer_commande(t):
    if t.data == "com_asgt":
        return f"{t.children[0].value} = {pretty_printer_expression(t.children[1])} ;"
    if t.data == "com_printf":
        return f"printf ({pretty_printer_expression(t.children[0])}) ;"
    if t.data == "com_while":
        return "while (%s){ %s}" % (pretty_printer_expression(t.children[0]), pretty_printer_commande(t.children[1]))
    if t.data == "com_if":
        return "if (%s){ %s} else { %s}" % (pretty_printer_expression(t.children[0]), pretty_printer_commande(t.children[1]), pretty_printer_commande(t.children[2]))
    if t.data == "com_sequence":
        return "\n".join([pretty_printer_commande(u) for u in t.children])

def pretty_print(t):
    return "main (%s) { %s return (%s); }" % (
        pretty_printer_liste_var(t.children[0]), 
        pretty_printer_commande(t.children[1]),
        pretty_printer_expression(t.children[2])
    )

#print(pretty_print(t))
#print(t)
