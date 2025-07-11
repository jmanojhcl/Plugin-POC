/*To open a link in a new tab in the browser*/

const clss = document.getElementsByClassName("topic/xref");
for(let i = 0; i < clss.length; i++) {

    clss[i].addEventListener("click", function() {
            
            clss[i].setAttribute("target", "_blank");
            clss[i].setAttribute("rel", "external noopener");
    
    });
}
