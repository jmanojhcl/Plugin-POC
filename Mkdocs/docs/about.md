
# Welcome to {{prodname}} documentation

{%
   include-markdown "topic1.md"
   start="<!--topic2overviewstart-->"
   end="<!--topic2overviewend-->"
%}


To log into {{prodname}} Foundry Engagement Services, follow these steps:

{% if os == "windows" %}
1.  On your Windows computer, specify this environment variable.
{% else %}
1.  On your Linux computer, pass this shell command.
{% endif %}
2.  Open an Internet browser.
3.  Enter the Volt MX Foundry Engagement Services URL in the **Address** field in the browser, Volt MX Foundry Engagement Services console URL is http://<servername>:<serverport>/vpns
    
    Example: http://localhost:8080/vpns
    
4.  Press the **Enter** key. The Volt MX Foundry Engagement Services Login screen appears.
    
 <!--  ![](Resources/Images/Overview/loginscreen.PNG) -->
    
5.  Enter the user name in the **Username** field.
6.  Enter the password in the **Password** field.
7.  Click the **Sign in** button. The **Dashboard** page appears as the landing page in the console.

{% include-markdown "topic1.md" %}