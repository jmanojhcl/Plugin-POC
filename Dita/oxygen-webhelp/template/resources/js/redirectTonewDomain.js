/*This will redirect from help.hcltechsw.com to help.hcl-software.com */

export function redirectNewdomain() {

return window.location.href = window.location.href.replace("help.hcltechsw.com", "help.hcl-software.com")

}
