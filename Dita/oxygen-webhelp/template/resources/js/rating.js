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
import { getIndexLocation, msg } from './utils.js';
import { LNG_IDX } from './config.js'
import { LANG_LIST } from './constants.js'

const defaultStarRate = 999;
const defaultCommentRate = "no comment - ";

export function submitRating() {
    let userFeedback = document.getElementById('rate-comment').value;
    let userRate = getStarRating();
    let selectedLang = getIndexLocation(LNG_IDX)
    if (LANG_LIST[selectedLang] === undefined) selectedLang = "en"
//User has to enter feedback in comment box, if he/she has selected both checkbox and star rating  
    let rateCheck = document.getElementById("rateCheck");
    if(userRate !== "" && rateCheck.checked !=false && userFeedback == ""){

       alert(msg(selectedLang, "feedback.comment.alert"));
    } else if (userRate !== "" || userFeedback !== "") {
//Alerts user to remove personal information from user feedback
        const emailRegEx = new RegExp(/\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+/, "gm");
        let contact_num = /([0-9-+:]{7,32})/gm;
		let IPaddressRegEx = /[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}/gm;
        if(emailRegEx.test(userFeedback) || contact_num.test(userFeedback) || IPaddressRegEx.test(userFeedback)){
            alert(msg(selectedLang, "feedback.comment.PII.messagealert"));
         } else{
        if (userRate === "") userRate = defaultStarRate;
        if (userFeedback === "") userFeedback += defaultCommentRate + Math.random().toString(36).substr(2, 9);
        gtag('event', 'User Feedback', {'event_category': 'rating', 'event_label':userFeedback, 'value':userRate});
        console.log("Star rating: " + userRate + "\nComment: " + userFeedback);
        alert(msg(selectedLang, "rating.success.alert"));
        clearRating();
        location.reload();
        }

    } else {
        alert(msg(selectedLang, "rating.error.alert"));
    }
}

export function toggleRateCheckbox() {
	
    let rateCheck = document.getElementById("rateCheck");
    let giscfdbk = document.getElementById('giscfdbk');
	
	document.addEventListener('click', () => {
    
    sessionStorage.setItem("checkboxState", rateCheck.checked);

	});
   
   if(rateCheck.checked != true) {
       
       document.getElementById("giscfdbk").classList.add("disabledbutton");

   } else {
        
      document.getElementById("giscfdbk").classList.remove("disabledbutton");
    }
    
}

document.addEventListener("DOMContentLoaded", function() {
    // Retrieve the checkbox state from local storage
    let rateCheck = document.getElementById("rateCheck");
    let giscfdbk = document.getElementById('giscfdbk');

    const checkboxState = sessionStorage.getItem("checkboxState");

    // If there is a stored state, set the checkbox accordingly
    if (checkboxState === "true") {
        document.getElementById("rateCheck").checked = true;
    }

    // Add an event listener to the checkbox to update its state in local storage
    document.getElementById("rateCheck").addEventListener("change", function() {
        sessionStorage.setItem("checkboxState", this.checked);
    });

    window.onload = onPageload();

    function onPageload() {
      let rateCheck = document.getElementById("rateCheck");

      let giscfdbk = document.getElementById('giscfdbk');
      if(rateCheck.checked == true) {

        document.getElementById("giscfdbk").classList.remove("disabledbutton");

      } else {
		  sessionStorage.clear();
	  }

    }

});


export function toggleSubmitButton() {
    let userFeedback = document.getElementById('rate-comment');
    let starRating = getStarRating();
    let submitBtn = document.getElementById('rate-submit');
    
    if (starRating !== "" || userFeedback !== "") {
   
        submitBtn.removeAttribute("disabled")
        
    } else {
        submitBtn.setAttribute("disabled", true)
    }

}

function clearRating() {
    let userFeedback = document.getElementById('rate-comment');
    let starRating = document.getElementsByName('rate');
    let rateCheck = document.getElementById("rateCheck");

    rateCheck.checked = false;
    userFeedback.value = "";
    userFeedback.disabled = true;

    starRating.forEach(function(val){ 
        if (val.checked) {
            val.checked = false
        }
    })
}

function getStarRating() {
    let starRating = document.getElementsByName('rate');
    let userRate = "";

    starRating.forEach(function(val){ 
        if (val.checked) {
            userRate = val.value;
        }
    })


    return userRate;
}