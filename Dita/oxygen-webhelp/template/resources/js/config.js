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
export const LNG_IDX = 5;
export const VER_IDX = 4;
export const LND_IDX = 3;
export const LANGUAGE = "Language";
export const VERSION = "Version";
export const PAGE_IDX_LOC = "index.html";
export const ENABLE_LANG_EN = false; // This should be the same configuration for all the languages within the same version.
export const PDFPRINTICON = false; // Set to true to enable PDF print icon in the TOC page.
export const PDF_URL_PATH = "https://help.hcltechsw.com/bigfix/10.0/platform/pdf/BigFix_Asset_Discovery_Users_Guide.pdf"; //Mention your PDF URL path here
export const CHANGE_LANG = "en"; //Mention the language you want to generate the webhelp build
export const URLPATH_VARY = "";

export const LATEST_VERSION = "11.0.4"; //Mention the latest version name from the VERSION_LIST.

//Keep the latest version always at first, after "0" : "product Name".
export const VERSION_LIST = {
/*"0" : "DevOps Test Hub versions",
"11.0.4" : "11.0.4",
"11.0.3" : "11.0.3",
"11.0.2" : "11.0.2",
"11.0.1" : "11.0.1",
"11.0.0" : "11.0.0",
"10.5.4" : "10.5.4",
"10.5.3" : "10.5.3",
"10.5.2" : "10.5.2",
"10.5.1" : "10.5.1",
"10.5.0" : "10.5.0",
"10.2.3" : "10.2.3",
"10.2.2" : "10.2.2",
"10.2.1" : "10.2.1",
"10.2.0" : "10.2.0",
"10.1.3" : "10.1.3",
"10.1.2" : "10.1.2",
"10.1.1" : "10.1.1",
"10.1" : "10.1.0"*/
}

export const VERSION_LIST_URL = {
    // "v7": "https://help.hcltechsw.com/connections/v7/index.html",
}

//Change the list base on your product languages availability.
export const PROD_LANG_LIST = [];
// export const PROD_LANG_LIST = ["en", "ar", "bg", "ca", "zh_CN", "zh_TW", "hr", "cs", "da", "nl", "fi", "fr", "de", "iw", "it", "hu", "ja", "kk", "ko", "no", "pl", "pt_BR", "pt", "ro", "ru", "sk", "sl", "es", "sv", "th", "tr"];

//List of product landing page URLs

export const PROD_LANDPAGE_URL = {
	
	DevOps_Test_Integration : "https://help.hcltechsw.com/devops/test/hub/index.html"
	
};
