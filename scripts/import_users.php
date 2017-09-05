<?php
/* USAGE:
     php import_users.php FILENAME WP_LOAD_PATH
   EXAMPLE:
     php import_users.php users.json /var/www/mysite/wp-load.php
*/
function _log($msg) {
    echo "[".date('r')."] ".$msg."\n";
}

if(count($argv) != 3) {
    _log('Usage: php import_users.php FILENAME WP_LOAD_PATH');
    exit(1);
}

$filename = $argv[1];
$wp_load_path = $argv[2];
require_once($wp_load_path);

$site_name = get_bloginfo('name');

$json = file_get_contents($filename);
$users = json_decode($json);
foreach($users as $user) {
    list($username,$first_name,$last_name, $email) = $user;
    $pass = wp_generate_password($length=32);
    $userdata = array(
        'user_login' => $username,
        'user_pass' => $pass,
        'user_email' => $email,
        'first_name' => $first_name,
        'last_name' => $last_name);
    $wp_user = get_user_by('login', $username);
    if ( !$wp_user ) {
        $user_id = wp_insert_user($userdata);
        if ( is_wp_error($user_id) ) {
            _log("[$site_name][error] ".$user_id->get_error_message()."(username: $username)");
            continue;
        }
        _log("[$site_name][new] $user_id : $username,$first_name,$last_name,$email");
        /* LDAP login flag */
        $flagged = add_user_meta( $user_id, "wpDirAuthFlag", "1");
        if( !$flagged ) {
            _log("$user_id not flagged");
        }
    } else {
        if($wp_user->user_email != $email) {
            _log("[$site_name][update] $wp_user->ID : replaced $wp_user->user_email with $email");
            $wp_user->user_email = $email;
            $user_id = wp_insert_user($wp_user);
            if ( is_wp_error($user_id) ) {
                _log("[$site_name][error] ".$user_id->get_error_message()."(username: $username)");
            }
        }
    }
}