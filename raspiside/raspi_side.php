<!DOCTYPE PHP>
<html>
 <head>
  <title> Màj raspi </title>
 </head>
 <body>
<?php
$chemin_acces_script_maj = "mise_a_jour.py";
$str_returned = shell_exec("python3 " . $chemin_acces_script_maj);
if ($str_returned === "0"){
    echo ("mise à jour ok");
} else
    echo("merde");
?> 
 </body>
</html>
