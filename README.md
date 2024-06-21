Auteurs: Dinojan David & Thomas Dollé

Utilisation du compilateur:

  1. Génération du code assembleur : python main.py code.txt output.asm
  2. Compilation du code assembleur : nasm -f elf64 -o output.o output.asm && gcc -o output output.o -no-pie && ./output <arguments>

Implémentation de structures et strings :

- Déclaration locale :
  type nom; 
  Exemple : int i; | string s1;

- Déclarer une struct avant le main :
  struct nomStruct {type1 nom1; type2 nom2;};
  Exemple : struct C {int x; struct A y;}; struct A {int a; int b;};

- Chaque variable de main peut être appelée en struct à condition de déclarer une variable locale à l'intérieur du main :
  Si main(X, Y) avec struct C, on peut déclarer localement struct_C_X et struct_C_Y avant de les utiliser :
  - struct struct_C_X; // Variable struct C associée à la variable X
  - struct struct_C_Y; // Variable struct C associée à la variable Y

- Opérations sur les struct :
  - Assignation d'un int sur les attributs int : struct_C_X.x = 5; ou struct_A_Y.a = 7; ou struct_C_X.y.b = struct_C_X.x;
  - Assignation d'un struct sur un attribut valide : struct_C_X.y = struct_A_Y; // Copie des attributs
  - Les variables X et Y restent utilisables comme des int à part entière : X = struct_A_X.x;
  - Les struct et les string ne sont pas croisables

- Opérations sur les string :
  - string s3           déclaration d'une variable_string non donnée en argument
  - n=len(s1);          longueur d'une variable_string : len
  - c=charAt(s1,n);     valeur ascii du caractère à la nieme position dans s1
  - s3=s1+s2;           concaténation des chaines de caractères
  Toutes les chaines de caractères non initialisées à 0 doivent êtres données en arguments

Particularités dans le compilateur :

- Les noms des variables liées aux structs : struct_nomStruct_nomVariableMain_attribut1_attribut2_... // pas de ., mais des struct_A_a
- Les noms des variables des string doivent commencer par s Exemple s1, sAbc et ce sont les seuls variables qui peuvent commencer par s (hormi les struct_... qui sont prioritaires)
- Vérifier l'égalité des types des 2 côtés de l'égalité // les types sont stockés dans un dictionnaire avec le nom des variables en clé
- Chercher toutes les variables locales dans le programme et stocker dans un dictionnaire les variables et leur type
- Ajout d'un argument dans la fonction main qui doit être écrit avant le main pour déclarer les struct
- Pretty_printer disponible

Gestion des exceptions :

- Faible gestion : nous nous sommes concentrés sur l'implémentation d'un maximum de features aux dépens de la gestion des exceptions

Limites du compilateur : 

- Faible développement des opérateurs binaires
- Beaucoup d'utilisation de boucles sur les éléments d'un dictionnaire (manque d'optimisation ?)


Exemple de code : 

struct C {int a, int b};
struct A {int x, struct C y};
struct B {struct A r};
main(X) {
    struct struct_C_X;
    struct struct_A_X;
    struct struct_B_X;
    int i;

    struct_C_X.a = 1;

    if (X > 7) {
        struct_A_X.y = struct_C_X;
        struct_A_X.y.b = 2;
    }
    else {
        struct_A_X.y = struct_C_X;
        struct_A_X.y.b = 4;
    }

    struct_B_X.r = struct_A_X;
    while(i < 5) {
        struct_B_X.r.x = 1 + struct_B_X.r.x;
        i = i + 1;
        printf(i);
    }

    printf(struct_B_X.r.x);
    return(struct_B_X.r.y.a + struct_B_X.r.y.b); 
}

Ou encore :

main(s1,s2,n) {
    string s3;

    printf(len(s1)+len(s2));
    if (len(s1)>n+1) {
        printf(charAt(s1,n));
    } else {
        n=n-len(s1);
        printf(charAt(s2,n));
    }

    s3=s1+s2;
    printf(len(s3));
    printf(charAt(s3,n));

    return(s3);
}