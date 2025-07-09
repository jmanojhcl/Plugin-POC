/*
 ********************************************************************
 * Licensed Materials - Property of HCL                             *
 *                                                                  *
 * Copyright HCL Software 2020. All Rights Reserved.                *
 *                                                                  *
 * Note to US Government Users Restricted Rights:                   *
 *                                                                  *
 * Use, duplication or disclosure restricted by GSA ADP Schedule    *
 *                                                                  *
 * Author: Siddalingayya Samshi Hiremath                            *
 * Release Version: v.Q42023                                        *
 ********************************************************************
 */



//Banner for the end of support versions
import {VERSION_LIST, VER_IDX, URLPATH_VARY} from "./config.js"
import {getBaseURL} from "./utils.js"
//import {VERSION_LIST} from "./constants"

export function getEOSVersion() {
		//Get the selected version from the Version dropdown, and assigns to variable selectedVer.
		//Get the keys from VERSION_LIST, and assign it with the path to a variable VER_PATH.
		//Get Div element through verID to assign the URL path to href id using setAttribute method.
		//Import the LATEST_VERSION from config.js, compares it with the selectedVer, if condition is true, then banner disappears, if false, then banner retains.
        let domain = document.location.origin;
		let base_url = getBaseURL(VER_IDX);
		
		 let selectElement = document.getElementById("versions");
		if(selectElement != null) {
         let selectedVer = selectElement.options[selectElement.selectedIndex].text;
		 let verPath = document.getElementById("vereosid");
		 const arr = Object.keys(VERSION_LIST);
		 const regEx = new RegExp('EOS', 'i');

		 if(URLPATH_VARY != "") {
			if(arr.some(isNaN) === false) {
				//const revrsArr = arr.sort().reverse();
				const revrsArr = arr.sort(function(a, b){return b-a});
				const VER_PATH = URLPATH_VARY;
				verPath.setAttribute("href", VER_PATH);
			} else {
				
				const VER_PATH = URLPATH_VARY;
				verPath.setAttribute("href", VER_PATH);
	
			}
		 } else {

			if(arr.some(isNaN) === false) {
				//const revrsArr = arr.sort().reverse();
				const revrsArr = arr.sort(function(a, b){return b-a});
				const VER_PATH = domain+base_url+"/"+revrsArr[0]+"/index.html";
				verPath.setAttribute("href", VER_PATH);
			} else {
				
				const VER_PATH = domain+base_url+"/"+arr[1]+"/index.html";
				verPath.setAttribute("href", VER_PATH);
	
			}
		 }
         
       	 	if(regEx.test(selectedVer) === true) {
			
				document.getElementById("eosvrnban").style.display='block';
			
			} else {
				document.getElementById("eosvrnban").style.display='none';

			}
		}	
	}
		
		
export function endOfSupp() {
	
		let selectElement = document.getElementById("versions");
		if(selectElement != null) {
		//Gets the header element by its class 'wh_header', and assigns it to div_id that will have just HTML collection, 
		//so to make it as a function, added [0] to div_id, it finds the header element.
		const div_id = document.getElementsByClassName("wh_header");
		//let htmlstr = '<div id=\"vrnban\" class=\"banner\"><div class=\"banner_content\"><div id=\"bnr\" class=\"banner_text\">You are not viewing the latest version.</div><a id=\"verID\" class=\"nospaces\" href=\"\"><strong>Click here to go to latest.</strong></a></div></div>';
		div_id[0].innerHTML += '<div id=\"eosvrnban\" class=\"banner\"><div class=\"banner_content\"><div id=\"eosbnr\" class=\"banner_text\">This version is no longer supported.</div><a id=\"vereosid\" href=\"\" style="font-weight: bold;">View the latest version.</a><div id="btnban" class="banner_close" type="button"></div></div></div>';
		//div_id[0].insertAdjacentHTML("afterend", htmlstr);
	}
}

export function closeEoSbtn() {
          
            const xx = document.getElementById("btnban");
            
            xx.addEventListener("click", () => {
				var xy = document.getElementById("eosvrnban");
                xy.remove();
				});
        }			