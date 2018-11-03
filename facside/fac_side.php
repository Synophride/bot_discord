<!DOCTYPE PHP>
<html>
  <!-- But du fichier : 
       (a) Permettre le signal <mise à jour ip>  
       | raspi -> fac = 1x/jour. Utilisation d'une clef.
       
       (b) Permettre le signal <mise à jour bot>
       | fac -> raspi
       p-e réponses en json

       paramètres :
       - Type de requête, clef(opt.)

       contenu de la page :
       - Bouton, ou message "mise à jour faite"'
    --> 
  <head>
    <title>Mises à jour du bot</title>
  </head>
  <body>
<?php

           // Ctes & vars
$key = null;
$type = null;
$access_key="./files/key.txt";
$access_ip ="./files/ip.txt";


if (isset($_GET['type'])) {
    $type = $_GET['type'];
}

if($type === "bonjour"){
    echo("bonjour");

} else if($type === "mise_a_jour_ip"){
    if(isset($_GET['key']))
        $key = $_GET['key'];  // Donne un mauvais truc 
    // vérification de si c'est la bonne clef
    $file_key = file($access_key, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    $key_attendue = $file_key[0];
    if($key_attendue === $key){
        // Ecriture de l'IP dans un fichier en dehors de public_html
        $ip = $_SERVER["REMOTE_ADDR"]; // test
        $fd = fopen($access_ip, "w");
        $i = fwrite($fd, $ip);
        if( $i == false ){
            echo("<h3> IP : Erreur lors de l'écriture de la nouvelle ip  </h3>");
        } else {
            echo("reussite");
        }
    } else {
        echo("mauvaise clef");
    }
} else if($type === "mise_a_jour_github") {
    // envoi d'un message "màj github" vers le raspi, par http
    $ip = file($access_ip, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES)[0];
    $addr = "http://" . $ip  . "/~synophride/maj_github.php";
    file_get_contents($addr);
    // parsing du fichier
    // $ip = ... 
    echo("<h3> mise à jour gh </h3>");
} else {
    // afficher un bouton "mettre à jour gh" qui rafraîchira la page en ajoutant param "màj gh"
    echo("<form action=\"http://https://tp-ssh1.dep-informatique.u-psud.fr/~julien.guyot/fac_side.php?type=mise_a_jour_github\" >" .
         "<input type=\"submit\" value=\"Mise à jour Github!\">" .
         "</form>");
}

       ?>
  </body>
</html>

