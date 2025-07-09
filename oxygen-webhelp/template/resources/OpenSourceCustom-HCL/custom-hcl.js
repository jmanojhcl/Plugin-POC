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
 * Author: Emmanuel Palogan                                         *
 * Release Version: v.Q12023                                        *
 * Author: Siddalingayya Samshi Hiremath                            *
 * Release Version: v.Q42023                                        *
 ********************************************************************
 */

import { LANG_LIST } from './constants.js'
import { LNG_IDX, VER_IDX, LND_IDX, LANGUAGE, VERSION, PAGE_IDX_LOC, ENABLE_LANG_EN, VERSION_LIST, VERSION_LIST_URL, PROD_LANG_LIST, PDFPRINTICON, PDF_URL_PATH, CHANGE_LANG, LATEST_VERSION, URLPATH_VARY, openSourceDomain} from './config.js'
import { initMailLink } from './mail.js'
import { initTwitterLink } from './twitter.js'
import { submitRating, toggleRateCheckbox, toggleSubmitButton} from './rating.js'
import { getIndexLocation, getBaseURL, getCurrentPath, createOptionItem, msg } from './utils.js'
import {getEOSVersion, endOfSupp, closeEoSbtn} from './eos.js'
import './scCustLangSelect.js'

//export let selectedLang = "en";
export let selectedLang = CHANGE_LANG;
let requestSuccess = false;

$(function(){
	initSwitchers();
    fillLanguageItems();
    fillVersionItems();
    setTooltip();
    initMailLink();
    initTwitterLink();
	initEvents();
	endOfSupp();
	insertTags();
    initLabels();
    cleanEmptyTags();
    pdfIconURL();
    getVersionLst();
	getEOSVersion();
	closebtn();
	closeEoSbtn();

});

 function initLabels(){
	//alert(selectedLang);
	//alert(VER_PATH);
	
    // this should be called after filling the language.
    let prodDocRef = document.getElementById("brandName");
    let version = document.getElementById("versions");
    let language = document.getElementById("languages");
    let rateShow = document.getElementById("ratingFormPrereq");
    let rateStar = document.getElementById("ratingStarLabel");
    let rateComment = document.getElementById("ratingCommentLabel");
    let rateCheck = document.getElementById("rateCheckLabel");
    let rateCheckNote = document.getElementById("rateCheckNoteLabel");
    let rateCheckPrivacy = document.getElementById("rateCheckNotePrivacy");
    let LAhref = document.getElementById("learningAcademy");
	let pdfprintElem = document.getElementById("pdficon");
	let bannerElem = document.getElementById("bnr");
	let bannerlnk = document.getElementById("verID");
	let bannerEoS = document.getElementById("eosbnr");
	let fdbkgisc = document.getElementById("fdbkL");

	//Dropdown menu in header for Resources
    let resource_Ref = document.getElementById("rscdropdown");
    //let resource_Ref = document.getElementsByClassName("dropbtnmenu");
    let custSupRef = document.getElementById("customerSupport");
    let commSupRef = document.getElementById("communitySupport");
    let customerIdea = document.getElementById("customerIdea");

	let pdfIconElem = document.getElementById("pdflinkId");
	//Footer labels
    let footerEmail = document.getElementById("footerMailLink");
	let footerTwitt = document.getElementById("footerTwitterLink");
	let disclaimLab = document.getElementById("disclaimerLabel");
	let privacyLab = document.getElementById("privacyLabel");
	let termsLab = document.getElementById("termsLabel");
	let cookieLab = document.getElementById("cookieLabel");
  
    if (fdbkgisc !== null) fdbkgisc.innerText = msg(selectedLang, "feedback.icon");
	if (bannerElem !== null) bannerElem.innerText = msg(selectedLang, "banner.head.text");
    if (bannerlnk !== null) bannerlnk.innerText = msg(selectedLang, "banner.link.version");
	if (bannerEoS !== null) bannerEoS.innerText = msg(selectedLang, "banner.eos.version");
	if (prodDocRef !== null) prodDocRef.innerText = msg(selectedLang, "header.proddoc.brand");
	if (LAhref !== null) LAhref.innerText = msg(selectedLang, "header.learning.academy");
	if (resource_Ref !== null) resource_Ref.innerText = msg(selectedLang, "header.resource.dropdown");
	if (custSupRef !== null) custSupRef.innerText = msg(selectedLang, "header.customer.support");
	if (commSupRef !== null) commSupRef.innerText = msg(selectedLang, "header.community.forums");
	if (customerIdea !== null) customerIdea.innerText = msg(selectedLang, "header.customer.idea");

	//PDF print icon on the TOC of production page
	if(PDFPRINTICON === true && pdfprintElem !== null) pdfprintElem.style.removeProperty("display");
	if (pdfIconElem !== null) pdfIconElem.title = msg(selectedLang, "pdf.icon.tooltip");
    if (language !== null) language.title = msg(selectedLang, "switcher.language.tooltip");
    if (version !== null) version.title = msg(selectedLang, "switcher.version.tooltip");
	//Footer labels
	if (footerEmail !== null) footerEmail.innerText = msg(selectedLang, "footer.mail.link");
	if (footerTwitt !== null) footerTwitt.innerText = msg(selectedLang, "footer.twitt.link");
	if (disclaimLab !== null) disclaimLab.innerText = msg(selectedLang, "footer.disclaim.label");
	if (privacyLab !== null) privacyLab.innerText = msg(selectedLang, "footer.privacy.label");
	if (termsLab !== null) termsLab.innerText = msg(selectedLang, "footer.terms.label");
	if (cookieLab !== null) cookieLab.innerText = msg(selectedLang, "footer.cookie.label");
    //if (rateShow !== null) rateShow.innerHTML = msg(selectedLang, "rating.no.show");
	if (rateShow !== null) { var temp_1 = msg(selectedLang, "rating.no.show");
		rateShow.insertAdjacentHTML('beforeend', temp_1);
	}
    if (rateStar !== null) rateStar.innerText = msg(selectedLang, "rating.star.label");
    if (rateComment !== null) rateComment.innerText = msg(selectedLang, "rating.comment.label");
    //if (rateCheck !== null) rateCheck.innerHTML = msg(selectedLang, "rating.check.label");
	if (rateCheck !== null) { var temp_2 = msg(selectedLang, "rating.check.label");
		rateCheck.insertAdjacentHTML('beforeend', temp_2);
	}
    //if (rateCheckNote !== null) rateCheckNote.innerHTML = msg(selectedLang, "rating.check.note");
	if (rateCheckNote !== null) { var temp_3 = msg(selectedLang, "rating.check.note");
		rateCheckNote.insertAdjacentHTML('beforeend', temp_3);
	}
    //if (rateCheckPrivacy !== null) rateCheckPrivacy.innerHTML = msg(selectedLang, "rating.check.privacy");
	if (rateCheckPrivacy !== null) { var temp_4 = msg(selectedLang, "rating.check.privacy");
		rateCheckPrivacy.insertAdjacentHTML('beforeend', temp_4);
	}
  }

function initSwitchers() {
    if (PROD_LANG_LIST.length < 1) {
        $(".language-container").remove();
    }

    if (Object.getOwnPropertyNames(VERSION_LIST).length < 2) {
        $(".version-container").remove();
    }
}

function initEvents() {
    let version = document.getElementById("versions");
    let language = document.getElementById("languages");
    let rateSubmit = document.getElementById("rate-submit");
    let rateCheck = document.getElementById("rateCheck");
    let rateComment = document.getElementById('rate-comment');
    let rateStar = document.getElementsByName('rate');
	let rscbtnmenu = document.getElementById("rscdropdown");
	
    if (language !== null) language.onchange = changeLanguage;
    if (version !== null) version.onchange = changeVersion;
    if (rateSubmit !== null) {
        
        rateSubmit.addEventListener("click", submitRating);
        rateComment.addEventListener("keyup", toggleSubmitButton);
        rateStar.forEach(function(val){ 
            val.addEventListener("click", toggleSubmitButton);
        })
    }
    
    if (rateCheck !== null){
        rateCheck.addEventListener("click", toggleRateCheckbox);       
	}
	
	
}


function fillVersionItems() {
    let sel = document.getElementById("versions");
    if (sel !== null) {
        let verLoc = getIndexLocation(VER_IDX);
        let ver = VERSION_LIST[verLoc];
        for (let v in VERSION_LIST) {
            let option = createOptionItem(sel, 'v-' + v, v, VERSION_LIST[v])
            if (ver !== undefined && verLoc === v) {
                option.selected = 'true';
            }
        }
    }
}

function fillLanguageItems() {
    let sel = document.getElementById("languages");
    if (sel !== null) {
        let langLoc = getIndexLocation(LNG_IDX);
        let lng = LANG_LIST[langLoc];
        let hasSelected = false;

        PROD_LANG_LIST.forEach(function (value, index, arr) {
            let option = createOptionItem(sel, 'lang_' + value, value, LANG_LIST[value])
            if (lng !== undefined && langLoc === value) {
                option.selected = 'true';
                selectedLang = value
                hasSelected = true
            }
        });

        if (hasSelected === false) {
            document.getElementById("lang_en").selected = 'true';
        }
    }

}

function changeVersion() {
    let ver = document.getElementById("versions").value;
    if (ver !== null && ver !== undefined && ver !== '' && ver !== "0") {

        if (ver in VERSION_LIST_URL) {
            location.href = VERSION_LIST_URL[ver];
        } else {
            let domain = document.location.origin
            let currentPath = getCurrentPath(VER_IDX, VERSION_LIST)
            let currentPathLang = getCurrentPath(LNG_IDX, LANG_LIST)
            let base_url = getBaseURL(VER_IDX)
            let baseLang_url = getBaseURL(LNG_IDX)
            let currentPage = currentPath.replace(base_url, "")
            let currentPageLang = currentPathLang.replace(baseLang_url, "")
            currentPageLang = (selectedLang === 'en' && ENABLE_LANG_EN) ? currentPageLang.replace('/en', '') : '/en' + currentPageLang
            let verDir = "/" + ver
            let search = document.location.search
            let rootEnLangUrl = domain + base_url + verDir + currentPageLang + search
            let verUrl = domain + base_url + verDir + currentPage + search

            if(selectedLang === 'en') sendRequest(rootEnLangUrl, LANGUAGE, false);
            sendRequest(verUrl, VERSION, true);
        }
    } else if (ver === "0") {
        let domain = document.location.origin
        let pathnames = document.location.pathname.split('/')
        let prodLandingURL = domain + "/" 
        
        pathnames.forEach(function (value, index, arr){
            if (index <= LND_IDX && index > 0) {
                prodLandingURL += value + "/"
            }
        })
        
        prodLandingURL += PAGE_IDX_LOC

        sendRequest(prodLandingURL, VERSION, true);
    } else {
        alert("Version undefined. Please check version reference.")
    }
}

function changeLanguage() {
    let defaultLang = "en"
    let lang = document.getElementById("languages").value;
    if (lang !== null && lang !== undefined && lang !== '') {

        let domain = document.location.origin
        let currentPath = getCurrentPath(LNG_IDX, LANG_LIST)
        let base_url = getBaseURL(LNG_IDX)
        let currentPage = currentPath.replace(base_url, "")
        let langDir = (lang === defaultLang && !ENABLE_LANG_EN) ? "" : "/" + lang
		let search = document.location.search
        let langUrl = domain + base_url + langDir + currentPage + search

        sendRequest(langUrl, LANGUAGE, true);
    } else {
        alert("Language undefined. Please check language reference.")
    }
}

function sendRequest(urlDest, requestType, doAlert) {
    let request = new XMLHttpRequest()
    let versionError = msg(selectedLang, "request.version.error");
    let homePageURLError = msg(selectedLang, "request.version.homePageURL");
    let languageError = msg(selectedLang, "request.language.error");
    console.log('Sending Request for ' + urlDest)
    request.onreadystatechange = function () {
        if (this.readyState === this.DONE) {
            let msg = (requestType === VERSION) ? versionError : languageError;
            let homeURLmsg = (requestType === VERSION) ? homePageURLError : languageError;
            let isSoft404 = isPageNotFound(request.responseText)
            if (request.status === 200 && !isSoft404) {
                console.log('Destination exists!')
                requestSuccess = true
                window.location.href = urlDest
            } else {
                console.log(msg)
                if(doAlert === true && requestSuccess === false) {
					//This condition works when the page is not available. Gets the current domain path of the page and base-URL of the document based on the VER_IND which is given in the Config.js.
                    //Gets the version from the dropdown and checks it in the VERSION_LIST which is given in the COnfig.js, if it matches in the loop, it assigns the key value to verFolder.
                    //verFolder means version folder name which will be in the URL. Script will get it from the Config.js.
					let domainURL = document.location.origin;
                    let base_url = getBaseURL(VER_IDX);
                    let selectedElem = document.getElementById("versions");
                    if(selectedElem != null) {

                        let getVersion = selectedElem.options[selectedElem.selectedIndex].text;
                        let verFolder;
                            for (let prop in VERSION_LIST) {
                                if (VERSION_LIST.hasOwnProperty(prop)) {
                                    if (VERSION_LIST[prop] === getVersion)
                                        verFolder = prop;
                                }
                            }
                            var returnVal = confirm(msg);
                            if(returnVal == true) {
                                if(URLPATH_VARY != "") {
                                    window.location.href = URLPATH_VARY;
                                } else {
                                    window.location.href = domainURL+base_url+"/"+verFolder+"/index.html";
                                }
                                
                            } else {
                                location.reload();
                            }
                    } 
                    
                }
            }
        }
    }
    request.open('GET', urlDest, false);
    request.send()
}

function isPageNotFound(responseText) {
    let isSoft404 = false
    let template = new DOMParser().parseFromString(responseText, "text/html");
    let bannerTitle = ''

    if(template.getElementsByClassName('banner-title')[0] !== undefined) {
        bannerTitle = template.getElementsByClassName('banner-title')[0].innerText;
    }
    
    if (bannerTitle !== '') {
        isSoft404 = bannerTitle.includes('Ooops... Page Not Found')
    }
    return isSoft404
}

function setTooltip() {
    $('[data-toggle="tooltip"]').tooltip;
}

function cleanEmptyTags() {
let welcome = document.getElementsByClassName('wh_welcome')[0];
if (welcome !== undefined && welcome.innerText.trim() === "") {
welcome.innerHTML = ""
}
}

function pdfIconURL() {
 if (PDFPRINTICON === true) {
	let urlPath = document.getElementById("pdflinkId");
	urlPath.setAttribute("href", PDF_URL_PATH);
 }
}


function getVersionLst() {
		//Gets the selected version from the Version dropdown, and assigns to varible selectedVer.
		//Gets the keys from VERSION_LIST, and assign it with the path to a variable VER_PATH.
		//Gets Div element through verID to assign the URL path to href id using setAttribute method.
		//Imports the LATEST_VERSION from config.js, compares it with the selectedVer, if condition is true, then banner disappears, if false, then banner retains.
		 let domain = document.location.origin;
		 let base_url = getBaseURL(VER_IDX);
		 
		 let selectElement = document.getElementById("versions");
		if(selectElement != null) {
			let selectedVer = selectElement.options[selectElement.selectedIndex].text;
                let verPath = document.getElementById("verID");
                const arr = Object.keys(VERSION_LIST);
                const regEx = new RegExp('EOS', 'i');
                if (openSourceDomain != "") {

                    if(URLPATH_VARY != "") {
                        
                        if(arr.some(isNaN) === false){
                            //const revrsArr = arr.sort().reverse();
                            const revrsArr = arr.sort(function(a, b){return b-a});
                            const VER_PATH = openSourceDomain+"/"+revrsArr[0]+"/"+URLPATH_VARY;
                            verPath.setAttribute("href", VER_PATH);
                        } else {
                            
                            const VER_PATH = openSourceDomain+"/"+arr[1]+"/"+URLPATH_VARY;
                            verPath.setAttribute("href", VER_PATH);
                        }
                    } else {
    
                        if(arr.some(isNaN) === false) {
                            //const revrsArr = arr.sort().reverse();
                            const revrsArr = arr.sort(function(a, b){return b-a});
                            const VER_PATH = openSourceDomain+"/"+revrsArr[0]+"/index.html";
    
                            verPath.setAttribute("href", VER_PATH);
                        } else {
                    
                            const VER_PATH = openSourceDomain+"/"+arr[1]+"/index.html";
                            verPath.setAttribute("href", VER_PATH);
    
                        }
                    }
            
                } else {
    
                    if(URLPATH_VARY != "") {
                        
                        if(arr.some(isNaN) === false){
                            //const revrsArr = arr.sort().reverse();
                            const revrsArr = arr.sort(function(a, b){return b-a});
                            const VER_PATH = domain+base_url+"/"+revrsArr[0]+"/"+URLPATH_VARY;
                            verPath.setAttribute("href", VER_PATH);
                        } else {
                            
                            const VER_PATH = domain+base_url+"/"+arr[1]+"/"+URLPATH_VARY;
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
            
    
                } 
        
			if (regEx.test(selectedVer) === false && LATEST_VERSION != selectedVer) {
									
				document.getElementById("vrnban").style.display='block';
			
			}
		}			
    }
		
function insertTags() {

		let selectElement = document.getElementById("versions");

        if(selectElement != null) {
            
            //Gets the header element by its class 'wh_header', and assigns it to div_id that will have just HTML collection, 
			//so to make it as a function, added [0] to div_id, it finds the header element.
			const div_id = document.getElementsByClassName("wh_header");
            //let htmlstr = '<div id=\"vrnban\" class=\"banner\"><div class=\"banner_content\"><div id=\"bnr\" class=\"banner_text\">Reminder: You are not viewing the latest version.</div><a id=\"verID\" class=\"nospaces\" href=\"\"><strong>Click here to go to latest.</strong></a></div></div>';
            div_id[0].innerHTML += '<div id=\"vrnban\" class=\"banner\"><div class=\"banner_content\"><div id=\"bnr\" class=\"banner_text\">A newer version of this product documentation is available.</div><a id=\"verID\" href=\"\" style="font-weight: bold;">View the latest version.</a><div id="btnbaner" class="banner_close" type="button"></div></div></div>';
            //div_id[0].insertAdjacentHTML("afterend", htmlstr);
		}
}

//Close button function for the latest version banner		
function closebtn() {
          
           const x = document.getElementById("btnbaner");
            if(x != null) {
				x.addEventListener("click", () => {
				   var y = document.getElementById('vrnban');
					y.remove();
				});
				
			}
}

		
//Hide and show the dropdown menu of resources
/*function dropdown_click() {
    
    let rscCont = document.getElementsByClassName("dropdnmenu-content");
	var display = "undefined";
	if (display !== "undefined"){
		for (let i=0; i<rscCont.length; i++){
			if (rscCont.style.display === "none") {
				rscCont.style.display = "block";
			}
			else {
				rscCont.style.display = "none";
			}
		}
	}
}*/
