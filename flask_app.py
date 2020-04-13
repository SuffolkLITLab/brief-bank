from flask import Flask
from flask import request,redirect,url_for
from flask import make_response, Response, jsonify
import re
import MySQLdb
import hashlib
import uuid
import docx2txt
from math import ceil


#SETTINGS
db_host = "suffolkbriefbank.mysql.pythonanywhere-services.com"
db_user = "suffolkbriefbank"
db_passwd = "JXbasAaXPrJ94ELek"
db_db ="suffolkbriefbank$default"

# Number of rows per page.
NUM_OF_DOCS_PER_PAGE = 25

"""
How many downloads before you need to upload.
e.g. if DWLD_UPLD_RATIO = 3 then for every 3 downloads you must upload once.
Before you can download again.
"""
DWLD_UPLD_RATIO = 3

# users with these emails become their own organization.
common_emails = ["gmail.com", "yahoo.com", "live.com", "aol.com", "outlook.com"]

"""
home path /
*remember to change the prefix for the functions.js file too*
"""
PREFIX = "/immigration-brief-bank"


def ValidEmail(email):
    if re.match("^.+@[a-zA-Z0-9-.]+\.([a-zA-Z]{2,})$", email) != None:
        return True
    else:
        return False

tos_html = """<h2>Terms of Service<br><font class="subtitle" style="font-weight:normal;">Last updated: XXX</font></h2>
    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam eu convallis eros. Quisque lectus quam, mollis nec
    nisi id, tempus lacinia odio. Nam congue semper lorem nec volutpat. Morbi vestibulum efficitur velit sit amet dictum.
    Cras odio turpis, bibendum eget luctus ac, venenatis non purus. Sed facilisis hendrerit tellus, sit amet suscipit turpis
    vestibulum a. Aliquam tempus mi et pretium facilisis. Suspendisse quis magna id dolor egestas pretium sit amet non diam.</p>
"""

def head(title,description):

    html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<HTML xmlns="http://www.w3.org/1999/xhtml"
      xmlns:og="http://ogp.me/ns#"
      xmlns:fb="http://www.facebook.com/2008/fbml">
<HEAD>
	<title>%s</title>
	<meta http-equiv="Content-type" content="text/html;charset=UTF-8"/>
	<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=0" />
	<meta name="apple-mobile-web-app-capable" content="no" />
    <link rel="apple-touch-icon" href=""/>
	<meta property="og:type" content="website"/>
	<meta property="og:title" content="%s"/>
	<meta property="og:description" content="%s"/>
	<meta property="og:image" content=""/>

	<meta name="twitter:card" content="summary_large_image">
	<meta name="twitter:site" content="@SuffolkLITLab">
	<meta name="twitter:creator" content="@SuffolkLITLab">
	<meta name="twitter:title" content="%s">
	<meta name="twitter:description" content="%s">
	<meta name="twitter:image" content=""/>

	<link rel="shortcut icon" type="image/x-icon" href="/images/favicon.ico">
	<link rel="stylesheet" href="https://code.jquery.com/ui/1.11.1/themes/smoothness/jquery-ui.css">
	<link rel="stylesheet" type="text/css" href="/css/style.css?">
	<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">
	<script src="https://code.jquery.com/jquery-1.11.1.min.js"></script>
  	<script src="https://code.jquery.com/jquery-1.10.2.js"></script>
  	<script src="https://code.jquery.com/ui/1.11.1/jquery-ui.js"></script>
  	<script src="/static/js_bin/jquery.cookie.js"></script>
  	<script src="/static/js_bin/functions.js"></script>
  	"""%(title,title,description,title,description)

    html = html + """<script>
		function createCookie(name,value,days) {
			if (days) {
				var date = new Date();
				date.setTime(date.getTime()+(days*24*60*60*1000));
				var expires = "; expires="+date.toGMTString();
			}
			else var expires = "";
			document.cookie = name+"="+value+expires+"; path=/";
		}
	</script>
</HEAD>
"""

    return html

def header(usr_id=None,title=None):

    if (title == "New Account"):
        bodyload = "onLoad=\"document.getElementById('username').focus();\""
    elif (title == "User Login"):
        bodyload = "onLoad=\"document.getElementById('email').focus();\""
    else:
        bodyload = ""

    html="""<BODY BGCOLOR="#ffffff" BACKGROUND="/static/imagesbackground.jpg" MARGINWIDTH="0" MARGINHEIGHT="0" %s>"""%bodyload

    html = html + "<div id='navbar'>"

    if usr_id == None:
        html = html + """<a href="%s/user/login/" class="navlink" onClick="createCookie('session','',-1);">login</a><body>"""%(PREFIX)
        html = html + """<a href="%s/user/new/" class="navnew">Create Account</a><body>"""%(PREFIX)
    else:
        html = html + f"""<a href="%s/user/settings/" class="navnew">Account Settings</a><body>
                         <a href="%s/" class="navlink" onClick="createCookie('session','',-1);">log out</a>"""%(PREFIX, PREFIX)

    html= html + "</div>"

    html = html + """<div class="content" style="background-size: 100px 100px;background-image:url("https://cdn10.bostonmagazine.com/wp-content/uploads/sites/2/2019/11/boston-skyline-now.jpg");">
	<div id="icon" style="background-size: 100px 100px;background-image: url('https://suffolklitlab.org/images/seal.jpg');"><a href="%s/"><img src="https://suffolklitlab.org/images/space.gif" width="100px" height="100px;" border="0"/></a></div>
	<h1 style="text-align:center;">Brief Bank<sup> <font size=+1>Beta</font></sup><center style="margin-top:5px;"><span class="subtitle">@ Suffolk Law School</font></span></center></h1>

	<div class="menu_bar">
		<p style="text-align:center;">
		<a href="https://suffolklitlab.org/" class="menu">&nbsp;LIT Lab&nbsp;</a>&nbsp;
		<font style="color:#888;">|</font>&nbsp;
		<a href="%s/about" class="menu">&nbsp;About&nbsp;</a>"""%(PREFIX, PREFIX)

    permission = permission_check(usr_id)
    if permission >= 2:
        html =html + """
                &nbsp;<font style="color:#888;">|</font>&nbsp;
                <a href="%s/search/" class="menu">&nbsp;Documents&nbsp;</a>
                &nbsp;<font style="color:#888;">|</font>&nbsp;
                <a href="%s/upload/" class="menu">&nbsp;Upload&nbsp;</a>
                """%(PREFIX, PREFIX)
        if permission >= 3:
            html += """
                    &nbsp;<font style="color:#888;">|</font>&nbsp;
                    <a href="%s/admin" class="menu">&nbsp;Admin&nbsp;</a>
                    """%(PREFIX)

    html = html + """
		</p>
		<div id="cookieConsent">
            <div id="closeCookieConsent">x</div>
            By using this website you agree to the <a href="%s">Terms of service</a> and the use of cookies.<a class="cookieConsentOK">That's Fine</a>
        </div>
	</div><div background= "%s/static/images/background.jpg">\n\n"""%(url_for('tos'), PREFIX)

    return html

def footer():

    html = """</div>\n	<div id="footer" class="footer"><a href="https://suffolklitlab.org/"><img src="https://suffolklitlab.org/images/blue_logo.png" width="50px" align="left" border="0"/></a>
     <a href="%s/terms">Terms &amp; Privacy</a> | <a href="https://suffolklitlab.org/credits">Credits</a></font>
	</div>

</BODY>
</HTML>"""%(PREFIX)

    return html

def login_check(cookie=None,email=None,password=None):
    usr_id = None
    db=MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
    c=db.cursor()
    if cookie:
        db_query = "select `usr_id` from `users` where crumb = %s"
        c.execute(db_query, (cookie,))
        results = c.fetchone()
        if results:
            usr_id = results[0]
        else:
            usr_id = None
    elif email:
        db_query = "select `salt`,`pass`,`crumb`,`usr_id` from `users` where email = %s"
        c.execute(db_query, (email,))
        results = c.fetchone()
        if results:
            salt = results[0]
            pass_the_salt = password + salt
            pass_the_salt = pass_the_salt.encode('utf-8')
            hash = hashlib.sha512(pass_the_salt).hexdigest()
            if (results[1] == hash):
                cookie = results[2]
                usr_id = results[3]

    db.close()
    return cookie, usr_id

#checks what type of permission a user has.
def permission_check(usr_id):
    if usr_id != None:
        db=MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
        cursor = db.cursor()
        if not cursor.execute('select role from users where usr_id = %s', (usr_id, )):
            return None
        role = cursor.fetchone()
        db.close()
        return role[0]

    return 0

# Downloads file from database as a docx or as plain text.
def download_filed(doc_id, user, text=False):
    try:
        int(doc_id)
    except:
        return "That document does not exist."
    try:
        db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=False)
        cursor =db.cursor()

        # get the (down/up)load of the users org and calculate if upload is 33% of download
        cursor.execute("select org_id from users where usr_id = %s", (user, ))
        org = cursor.fetchone()[0]
        cursor.execute("select upload, download from orgs where org_id = %s", (org, ))

        upload, dload = cursor.fetchone()

        cursor.execute("select doc_id from org_doc_log where doc_id = %s and org_id = %s", (doc_id, org, ))

        if not DWLD_UPLD_RATIO * upload >= dload and cursor.fetchone() == None:
            return "Need to upload"

        cursor.execute("update orgs set download = %s where org_id= %s", (dload + 1, org, ))
        cursor.execute("insert into org_doc_log values(%s, %s)", (doc_id, org, ))
        if text:
            cursor.execute("select plain_text from docs where doc_id = %s", (doc_id, ))
            text = cursor.fetchone()
            if text == None:
                return "That document does not exist."
            return text[0]
        else:
            cursor.execute("select content, file_name from docs where doc_id = %s", (doc_id, ))
        query = cursor.fetchone()
        db.commit()
        db.close()
        return Response(query[0], mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.docx"%(query[1])})
    except Exception as e:
        return str(e)

# casts a vote on citations
def vote(cite_id, ballot, user_id):
    try:
        db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=False)
        cursor =db.cursor()

        cursor.execute("select * from cite_vote_log where cite_id = %s and usr_id= %s", (cite_id, user_id, ))

        if cursor.fetchone() != None:
            return None

        cursor.execute("select valid from citations where cite_id = %s", (cite_id, ))

        if ballot > 0:
            cursor.execute("update citations set valid = %s where cite_id = %s", (cursor.fetchone()[0] + 1, cite_id, ))
        elif ballot < 0:
            cursor.execute("update citations set valid = %s where cite_id = %s", (cursor.fetchone()[0] - 1, cite_id, ))

        cursor.execute("insert into cite_vote_log values(%s, %s)", (user_id, cite_id, ))

        db.commit()
        db.close()
        return True
    except:
        return False

# checks to see if the object can be turned into an int.
def int_check(num):
    try:
        int(num)
        return num
    except:
        return ''
def str_check(item):
    try:
        return item.isalnum()
    except:
        return False
#===================================================================================================================================
#===================================================================================================================================
#===================================================================================================================================

app = Flask(__name__)


@app.route(PREFIX +'/')
def home():
    cookie, usr_id = login_check(request.cookies.get('session'))
    title = "LIT Project"
    description = " "
    body = "<div class=\"content\">"
    body = body + """<h2><a name="what" href="#title" class="anchor"></a>Title</h2>

                    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam eu convallis eros. Quisque lectus quam, mollis nec nisi id, tempus lacinia odio. Nam congue semper lorem nec volutpat. Morbi vestibulum efficitur velit sit amet dictum. Cras odio turpis, bibendum eget luctus ac, venenatis non purus. Sed facilisis hendrerit tellus, sit amet suscipit turpis vestibulum a. Aliquam tempus mi et pretium facilisis. Suspendisse quis magna id dolor egestas pretium sit amet non diam.</p>

                    <p>Vestibulum ante tortor, facilisis a mi vel, viverra scelerisque ex. Fusce vitae tellus justo. Donec tempus, risus a efficitur ultricies, ex orci lacinia est, vitae iaculis mauris lectus eget lacus. Etiam a ipsum urna. Aenean vel tellus fermentum, interdum nisl id, egestas tellus. Phasellus sed laoreet turpis. Quisque sed velit a ligula pharetra tincidunt. Pellentesque nec neque mattis, efficitur diam et, dignissim purus. Aliquam eget sollicitudin odio, eget porta ligula.</p>
                    """
    body = body + "</div>"
    usr_login()

    html = "<html>"+head(title,description)+header(usr_id)+body+footer()+"\n</html>"
    return html

@app.route(PREFIX + '/user/new/', methods=['GET','POST'])
def usr_new():
    cookie, usr_id = login_check(request.cookies.get('session'))

    title = "New Account"
    description = "Spot is an NSMIv2 entity/issue spotter built by Suffolk University's Legal Innovation and Technology (LIT) Lab. Spot builds upon data from the Learned Hands online game, a partnership between the LIT Lab and Stanford's Legal Design Lab. Learned Hands aims to crowdsource the labeling of laypeople's legal questions for the training of machine learning (ML) classifiers/issue spotters. "

    if request.form.get("username"):
        username = request.form.get("username")
    else:
        username = ""
    if request.form.get("email"):
        email = request.form.get("email")
    else:
        email = ""
    if request.form.get("newpass"):
        newpass = request.form.get("newpass")
    else:
        newpass = ""
    if request.form.get("newpassconf"):
        newpassconf= request.form.get("newpassconf")
    else:
        newpassconf = ""
    if request.form.get("tos"):
        tos= request.form.get("tos")
    else:
        tos = 0

    db=MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
    c=db.cursor()
    c.execute("""select count(*) from users where email = '%s'"""%email)
    test = c.fetchone()[0]

    body = "<div class=\"content\"><div class=\"forminput\"><h2> Create An Account</h2>"

    if (username != "") & (email != "") & (ValidEmail(email)) & (len(newpass) >= 8) & (newpass == newpassconf) & (tos == "1") & (test == 0):

        salt = uuid.uuid4().hex
        pass_the_salt = newpass + salt
        pass_the_salt = pass_the_salt.encode('utf-8')
        hash = hashlib.sha512(pass_the_salt).hexdigest()

        db_query = "INSERT INTO users (`name`, `email`, `crumb`, `salt`, `pass`, `created_on`, `org_id`) VALUES (%s, %s, conv(floor(rand() * 99999999999999), 20, 36), %s, %s, NOW(), %s);"
        domain = email.split("@")[-1].lower()
        if domain in common_emails:
            c.execute(db_query, (username, email, salt, hash, 1))
        else:
            c.execute("select org_id from orgs where name = %s", (domain, ))
            row = c.fetchone()
            if row == None:
                c.execute("insert into orgs(name) values(%s)", (domain, ))
                c.execute(db_query, (username, email, salt, hash, c.lastrowid))
            else:
                c.execute(db_query, (username, email, salt, hash, row[0]))

        db_query = "select `crumb` from `users` where email = %s"
        c.execute(db_query, (email,))
        cookie = c.fetchone()[0]
        response = make_response(redirect(url_for('usr_settings'), code=302))
        response.set_cookie('session', cookie)
        return response

    else:
        emailstyle = ""
        namestyle = ""
        npassstyle = ""
        tosstyle = ""

        if (username != "") or (email != "") or (newpass != "") or (newpassconf != ""):
            body = body + """<p style="background:yellow;text-align:center;padding:15px;">There was a problem creating your account.</p>"""

            if test > 0:
                body = body + """<p style="background:yellow;text-align:center;padding:15px;">This email is already used.</p>"""
                emailstyle = "background:yellow;"

            if (username ==""):
                body = body + """<p style="background:yellow;text-align:center;padding:15px;">You must fill in the name field.</p>"""
                namestyle = "background:yellow;"

            if (email ==""):
                body = body + """<p style="background:yellow;text-align:center;padding:15px;">You must fill in the email field.</p>"""
                emailstyle = "background:yellow;"
            elif (ValidEmail(email)==False):
                body = body + """<p style="background:yellow;text-align:center;padding:15px;">There was a problem with your email's formating.</p>"""
                emailstyle = "background:yellow;"

            if (len(newpass) < 8):
                body = body + """<p style="background:yellow;text-align:center;padding:15px;">Password must be 8 or more characters.</p>"""
                npassstyle = "background:yellow;"

            if (newpass != newpassconf):
                body = body + """<p style="background:yellow;text-align:center;padding:15px;">Passwords do not match.</p>"""
                npassstyle = "background:yellow;"

            if (tos != "1"):
                body = body + """<p style="background:yellow;text-align:center;padding:15px;">You must read and agree to the terms of service to create and account.</p>"""
                tosstyle = "style=\"background:yellow;\""

        body = body + """
                <form action="." method="POST">
                <p>Account Name:<br><input type="text" id="username" name="username" maxlength="100" value="%s" style="width:100%%; %s" />
                </p>
                <p>
                Email address:<br><input type="text" maxlength="100" name="email" value="%s" style="width:100%%; %s" />
                </p>
                <p>
                Password:<br><input type="password" maxlength="100" name="newpass" style="width:100%%; %s" />
                </p>
                <p>
                Confirm Password:<br><input type="password" maxlength="100" name="newpassconf" style="width:100%%; %s" />
                </p>
                <p %s >
                <input id="tos" name="tos" type="checkbox" value="1"><label for="tos"> I have read, understand, and accept the API's terms of service.</label>
                </p>
                <p>
                <button type="submit">Submit</button>
                </p>
                </form>
                </div>"""%(username,namestyle,email,emailstyle,npassstyle,npassstyle,tosstyle)

        body = body + """<div class="tosfloat">%s</div>"""%tos_html

    body = body + "</div>"

    html = "<html>"+head(title,description)+header(usr_id,title)+body+footer()+"\n</html>"
    return html

@app.route(PREFIX + '/user/login/', methods=['GET','POST'])
def usr_login():
    if request.form.get("email"):
        email = request.form.get("email")
    else:
        email = ""
    if request.form.get("password"):
        password = request.form.get("password")
    else:
        password = ""

    cookie, usr_id = login_check(request.cookies.get('session'),email,password)
    title = "User Login"
    description = "Spot is an NSMIv2 entity/issue spotter built by Suffolk University's Legal Innovation and Technology (LIT) Lab. Spot builds upon data from the Learned Hands online game, a partnership between the LIT Lab and Stanford's Legal Design Lab. Learned Hands aims to crowdsource the labeling of laypeople's legal questions for the training of machine learning (ML) classifiers/issue spotters. "

    body = "<div class=\"content\"><div class=\"forminput\"><h2>Login</h2>"

    if (usr_id and cookie):
        response = make_response(redirect(url_for('usr_settings'), code=302))
        response.set_cookie('session', cookie)
        return response

    else:
        body = body + """<form action="." method="post">"""

        if (email !=""):
            body = body + "<p style=\"background:yellow;text-align:center;padding:5px;\">Your email-password pair cannot be found. Please try again.</p>"

        body = body + """
            <p>
            Email:<br><input type="text" id="email" name="email" style="width:100%%" maxlength="100" value="%s">
            </p>
            <p>
            Password:<br><input type="password" style="width:100%%" maxlength="150" name="password">
            </p>
            <p>
            <input type="submit" value="Submit">
            </p>
            <p><a href="%s/user/new/">Create a New Account</a></p>
            </form></div>"""%(email, PREFIX)

        body = body + """<div class="tosfloat">%s</div>"""%tos_html
        body = body + "</div>"

        response = make_response("<html>"+head(title,description)+header(usr_id,title)+body+footer()+"\n</html>")
        #if cookie:
        #    response.set_cookie('session', cookie)
        return response


@app.route(PREFIX + '/user/settings/', methods=['GET','POST'])
def usr_settings():
    cookie, usr_id = login_check(request.cookies.get('session'))


    if (usr_id==None):
        response = make_response(redirect(url_for('usr_login'), code=302))
        new_header = header(None)
        return response
    else:
        new_header = header(usr_id)
        if 'user' in request.args:
            cand_id = request.args.get("user")
            cur_usr_check = permission_check(usr_id)
            other_usr_check = permission_check(cand_id)

            if cur_usr_check >= 3 and other_usr_check < cur_usr_check:
                usr_id = int(cand_id)
            else:
                return "This account does not have access to this link.", 405

        if request.form.get("sentform"):
            sentform = request.form.get("sentform")
        else:
            sentform = "0"

        if request.form.get("username"):
            username = request.form.get("username")
        else:
            username = ""
        if request.form.get("email"):
            email = request.form.get("email")
        else:
            email = ""
        if request.form.get("newpass"):
            newpass = request.form.get("newpass")
        else:
            newpass = ""
        if request.form.get("newpassconf"):
            newpassconf= request.form.get("newpassconf")
        else:
            newpassconf = ""

        title = "Settings"
        description = "Spot is an NSMIv2 entity/issue spotter built by Suffolk University's Legal Innovation and Technology (LIT) Lab. Spot builds upon data from the Learned Hands online game, a partnership between the LIT Lab and Stanford's Legal Design Lab. Learned Hands aims to crowdsource the labeling of laypeople's legal questions for the training of machine learning (ML) classifiers/issue spotters. "

        body = "<div class=\"content\"><div class=\"forminput\"><h2> Settings </h2>"
        userstyle = ""
        emailstyle = ""
        npassstyle = ""

        db=MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
        c=db.cursor()


        if ((len(newpass) == 0) | (len(newpass) >= 8)) & (newpass == newpassconf) & (username != "") & (email != "") & (ValidEmail(email)):

            db_query = "select `usr_id` from `users` where email = %s"
            c.execute(db_query, (email,))
            match_id = c.fetchone()

            if (match_id):
                if (match_id[0]==usr_id):
                    db_query = "UPDATE users SET `name` = %s,`email` = %s WHERE `usr_id` = %s"
                    c.execute(db_query, (username,email,usr_id,))
                    #c.execute("UPDATE users SET `name` = '%s',`email` = '%s' WHERE `usr_id` = '%s'"%(username,email,usr_id))
                    #db.commit()
                else:
                    body = body + """<p style="background:yellow;padding:15px;">Email already in use by another account.</p>"""
                    emailstyle = "style=\"background:yellow;\""
            else:
               db_query = "UPDATE users SET `name` = %s,`email` = %s WHERE `usr_id` = %s"
               c.execute(db_query, (username,email,usr_id,))

            if (newpass == newpassconf) & (newpass != "") & (newpassconf !=""):
                salt = uuid.uuid4().hex
                pass_the_salt = newpass + salt
                pass_the_salt = pass_the_salt.encode('utf-8')
                hash = hashlib.sha512(pass_the_salt).hexdigest()

                db_query = "UPDATE users SET `pass` = %s, `salt`= %s WHERE `usr_id` = %s"
                c.execute(db_query, (hash,salt,usr_id,))

        else:
            if ((username =="") & (sentform == "1")):
                body = body + """<p style="background:yellow;padding:15px;">Email cannot be blank.</p>"""
                userstyle = "background:yellow;"

            if ((email == "") & (sentform == "1")):
                body = body + """<p style="background:yellow;padding:15px;">Email cannot be blank.</p>"""
                emailstyle = "background:yellow;"
            elif ((sentform == "1") & (ValidEmail(email)==False)):
                body = body + """<p style="background:yellow;text-align:center;padding:15px;">There was a problem with your email's formating.</p>"""
                emailstyle = "background:yellow;"

            if (len(newpass) < 8) & (newpass != ""):
                body = body + """<p style="background:yellow;padding:15px;">Password must be at least 8 characters long.</p>"""
                npassstyle = "background:yellow;"

            if (newpass != newpassconf):
                body = body + """<p style="background:yellow;padding:15px;">Passwords do not match.</p>"""
                npassstyle = "background:yellow;"

        db_query = "select `name`, `email` from `users` where usr_id = %s"
        c.execute(db_query, (usr_id,))
        db_res = c.fetchone()

        username = db_res[0]
        email = db_res[1]

        db.close()

        body = body + """<p>
                <form action="%s" method="post">
                <p>
                Account Name: <br><input name="username" maxlength="100" value="%s" style="width:100%%; %s" />
                </p>
                <p>
                    Email address: <br><input name="email" maxlength="100" value="%s" style="width:100%%; %s" />
                </p>
                <p>
                    Change Password To: <br><input name="newpass" maxlength="100" type="password" style="width:100%%; %s" />
                </p>
                <p>
                    Confirm Password: <br><input name="newpassconf" maxlength="100" type="password" style="width:100%%; %s" />
                </p>
                <input type="hidden" name="sentform" value="1"/>
                </p>"""%(url_for('usr_settings', user=usr_id), username,userstyle,email,emailstyle,npassstyle,npassstyle)


        body = body + """<p>
                <button type="submit" value={usr_id}>Save</button>
                </p></form></div>"""

        body = body + """<div class="tosfloat">%s</div>"""%tos_html
        body = body + "</div>"

        html = "<html>"+head(title,description)+new_header+body+footer()+"\n</html>"
        return html

@app.route(PREFIX + '/terms/')
def tos():
    cookie, usr_id = login_check(request.cookies.get('session'))
    title = "Terms of Use"
    description = " "
    html = "<html>"+head(title,description)+header(usr_id)+"<div class=\"content\">"+tos_html+"</div>"+footer()+"\n</html>"
    return html

@app.route(PREFIX + '/docs/', methods=['POST', 'GET'])
def docs():
    cookie, usr_id = login_check(request.cookies.get('session'))
    if usr_id == None:
        response = make_response(redirect(url_for('usr_login'), code=302))
        return response

    permission = permission_check(usr_id)
    if permission < 1:
        response = "<html>" + head("Error","Access Denied") + header(usr_id)+" <h2>Pending Status</h2> <div class=\"content\">"\
        "<h4>Your account status is pending, access is denied.<br>Your account must first be aproved by the administrator.</h4>"\
        +"</div>"+ footer() +"\n</html>"
        return response

    db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
    cursor =db.cursor()

    doc_id = request.form.get('download')
    if doc_id:
        return download_filed(doc_id, usr_id)

    if request.args:
        try:
            query_list = list()
            sql = ""
            flag = False

            doc_type = int_check(request.args.get('doc_type'))
            if doc_type != '':
                flag = True
                sql_from = """from (select docs.* from docs, rel_docs_types where type_id = %s and docs.doc_id = rel_docs_types.doc_id)
                as all_docs"""%(doc_type)
            else:
                sql_from = "from docs as all_docs"

            body = int_check(request.args.get('body'))
            if body != '':
                query_list.append("body = %s"%(body))

            venue = int_check(request.args.get('venue'))
            if venue != '':
                query_list.append("venue_id = %s"%(venue))

            outcome = int_check(request.args.get('outcome'))
            if outcome != '':
                query_list.append("all_docs.outcome = %s"%(outcome))

            pattern = request.args.get('pattern')
            pat_list= list()
            for pat in [pattern[i:i+9] for i in range(0, len(pattern), 9)]:
                if len(pat) % 9 == 0:
                    pat_list.append("rel_fact_doc.pattern = \"%s\""%(pat))

            if pat_list:
                sql_from += ", rel_fact_doc"
                if len(query_list) >= 1:
                    sql_where = " where all_docs.doc_id = rel_fact_doc.doc_id and (" + " and ".join(query_list) + ") and ( " + " or ".join(pat_list) + ")"
                else:
                    sql_where = " where all_docs.doc_id = rel_fact_doc.doc_id and (" + " or ".join(pat_list) + ")"
            else:
                if len(query_list) >= 1:
                    sql_where = " where (" + " and ".join(query_list) + ")"
                else:
                    sql_where = None

            search_flag = None
            search_query = request.args.get('search_query')
            if search_query and str_check(search_query):
                search_str = "%" +search_query+ "%"
                search_flag = (search_str, search_str, search_str, )
                if sql_where != None:
                    sql_where += " and (all_docs.plain_text LIKE %s or all_docs.description LIKE %s or all_docs.file_name LIKE %s )"
                    sql += sql_from + sql_where
                    #return sql
                    #cursor.execute(sql, (search_str, search_str, search_str, ))
                else:
                    sql += sql_from + " where (all_docs.plain_text LIKE %s or all_docs.description LIKE %s or all_docs.file_name LIKE %s )"
                    #return sql
                    #cursor.execute(sql, (search_str, search_str, search_str, ))
            else:
                #sql_where += ")"
                if sql_where != None:
                    sql += sql_from + sql_where
                else:
                    if not flag:
                        return search(highlights="<p style='display:inline;text-align:center;\
                        background-color:red;color:white;'>You have to choose options.<p>")
                    else:
                        sql += sql_from

        except:
            return search("<p style='display:inline;text-align:center;\
                background-color:red;color:white;'>There was a problem fetching the documents.<p>")

    # pagination setup
    if search_flag:
        cursor.execute("SELECT COUNT(all_docs.doc_id) " + sql, search_flag)
    else:
        cursor.execute("SELECT COUNT(all_docs.doc_id) " + sql)

    total_pages = ceil(int(cursor.fetchone()[0])/NUM_OF_DOCS_PER_PAGE)-1

    if 'page' in request.args:
        try:
            if int(request.args['page']) >= 1:
                page = int(request.args['page'])-1
                if page > total_pages:
                    page = total_pages
            else:
                return search("The page you are looking for does not exist")
        except:
            return search("The page you are looking for does not exist")

    else:
        page = 0
    limit = " LIMIT %d, %d"%(page * NUM_OF_DOCS_PER_PAGE, NUM_OF_DOCS_PER_PAGE)
    sql = "SELECT all_docs.file_name, all_docs.doc_id " + sql +limit
    #return str((sql, search_flag))
    try:
        if search_flag:
            cursor.execute(sql, search_flag)
        else:
            cursor.execute(sql)
    except:
        return str(sql) + '\n\n' + str(search_flag)

    docs_list= cursor.fetchall()


    all_docs = """<center><form method="post"><table class="w3-table-all w3-hoverable"><tr>
                    <th>Brief Title</th>
                    <th>Type</th>
                    <th>File</th>
                    <th>Author(s)</th>
                    </tr>
                """

    #num_pages = ceil(cursor.execute("SELECT COUNT(*) FROM docs")/30)
    try:
        for doc, doc_id in docs_list:
            cursor.execute("select name from authorship inner join users on users.usr_id= authorship.usr_id where doc_id = %s",(doc_id, ))
            authors = cursor.fetchall()
            authors = ", ".join(author[0] for author in authors)
            cursor.execute("select b.name from rel_docs_types a, doc_types b where a.doc_id = %s and b.type_id = a.type_id", (doc_id, ))
            types_fetched = cursor.fetchall()
            if types_fetched:
                types = ", ".join([item[0] for item in types_fetched])
            else:
                types = "N/A"
            all_docs += """<tr><td><a href="%s">%s</a></td>
                           <td>%s</td><td><button value="%s" name= "download"> Download</button>
                           </td><td>%s</td></tr>"""%(url_for('doc', docID= doc_id), doc, types, doc_id, authors)
        all_docs += '</form></table></center>'
    except Exception as e:
        print("Error: could not fetch data.")
        all_docs = "<center>There was a problem fetching the documents.</center>" + str(e)
    db.close()
    page_nav = ""
    first_page = url_for('docs', doc_type=doc_type, body=body, venue=venue, outcome=outcome, pattern=pattern, search_query=search_query, page=1)
    last_page = url_for('docs', doc_type=doc_type, body=body, venue=venue, outcome=outcome, pattern=pattern, search_query=search_query, page=total_pages+1)
    for page_num in [numb for numb in range(page-3, page+3) if numb >= 0 and numb <= total_pages]:
        if page_num == page:
            page_nav += "<a class=\"active\" href=\"#\">%s</a>"%(page_num+1)
        else:
            page_nav += "<a href=\"%s\">%s</a>"%(url_for('docs', doc_type=doc_type, body=body, venue=venue, outcome=outcome, pattern=pattern, search_query=search_query, page=page_num+1), page_num+1)
    if total_pages > 3:
        page_nav= "<div class=\"pagination\"><a href=\"%s\">First</a>%s<a href=\"%s\">Last</a></div>"%(first_page, page_nav, last_page)
    else:
        page_nav= "<div class=\"pagination\">" + page_nav + "</div>"

    all_docs += "</div>" + page_nav
    title = 'Documents'
    description= 'Documents'


    html = "<html>"+head(title,description) + header(usr_id)+" <h2>Documents</h2> <div class=\"content\">"+ all_docs + footer() +"\n</html>"
    return html


@app.route(PREFIX + '/search/', methods=['POST', 'GET'])
def search(highlights=''):
    cookie, usr_id = login_check(request.cookies.get('session'))

    if usr_id == None:
        response = make_response(redirect(url_for('usr_login'), code=302))
        return response

    permission = permission_check(usr_id)
    if permission < 2:
        return make_response(redirect(url_for('home'), code=302))

    db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
    cursor =db.cursor()

    if request.method == 'POST':
        try:
            doc_type = int_check(request.form.get('doc_type'))
            body= int_check(request.form.get("body"))
            venue= int_check(request.form.get("venue"))
            outcome= int_check(request.form.get("outcome"))
            search_query= request.form.get("search").strip()
            patterns =list()

            for pattern, on in request.form.to_dict().items():
                if on == "on":
                    if len(pattern)%9 == 0:
                        patterns.append(pattern)

            for element in patterns:
                cur_elem = element[0:3]+"000000"
                if cur_elem in patterns and element != cur_elem:
                    patterns.remove(cur_elem)
            patterns = "".join(list(patterns))
            if int_check(patterns) and len(patterns) != 0:
                return str(request.form)
                patterns = ''
                highlights +="<p style='background-color: #FF522D;text-align:center;color:white;'>\
                There was something wrong with your fact pattern.</p>"
            if not re.match('^[a-zA-Z0-9_ ]+$',search_query):
                search_query = ''
                highlights +="<p style='background-color: #FF522D;text-align:center;color:white;'>\
                The text enterned is not alphanumeric, please check it and try again.</p>"
            if body == '' and doc_type == '' and venue == '' and outcome == '' and search_query == '' and patterns == '':
                highlights +="<p style='background-color: #FF522D;text-align:center;color:white;'>\
                You must fill in the form before submitting.</p>"
            else:
                search_query = search_query.strip()
                return make_response(redirect(url_for('docs', doc_type=doc_type, body=body, venue=venue, outcome=outcome, pattern=patterns, search_query=search_query)))

        except Exception as e:
            return str(e)
            highlights += "Error fetching data from form."

    cursor.execute("select * from fact_patterns")
    all_pats = list(cursor.fetchall())
    org_pats = []
    for pattern in all_pats:
        if '000000' in pattern[0]:
            print(pattern)
            pat_copy = pattern[0][:3]
            org_pats.append([pattern])
            for pat in all_pats:
                if pat[0][:3] == pat_copy and pat != pattern:
                    org_pats[-1].append(pat)
        fact_pattern_html = "<h2>Fact Pattern</h2><p>Check all the boxes that apply to this document.</p>"
    for pattern in org_pats:
        fact_pattern_html += """<label class="container">
                                <input type="checkbox" class= 'main' name="%s" onload="change_onload()" onclick="on_change()">
                                <span class="checkmark"></span>
                                <span class="on-top">%s</span>
                                </label>
                              """%(pattern[0][0], pattern[0][1])
        if len(pattern) > 1:
            fact_pattern_html += """<div style='display: none;' class= "%s"> """%(pattern[0][0])
            for pat in pattern[1:]:
                fact_pattern_html += """<label>
                                      <input type="checkbox" name="%s"> %s
                                      </label><br>"""%(pat[0], pat[1])
            fact_pattern_html += "</div>"
    fact_pattern_html += "</div></div>"
    """~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"""
    search_field = """
        <p style='display:text-align;'>You can search through all the documents using the search bar. By picking fields and fact patterns you can narrow your search.</p>
             <div style='display: flex;align-items:center;justify-content:center;'>
                <input type="text" placeholder="Search.." name="search">
                <button type="submit"><i class="fa fa-search"></i></button>
             </div>
             """

    outcomes = """
                    <br>
                    <label>
                    Outcome:
                    <select name= "outcome">
                    <option value="" selected>All</option>
                    %s
                    </select></label>
                    <br>
                """
    cursor.execute("select * from outcomes")
    outcome_list = ""
    for outcome_id, name in cursor.fetchall():
        outcome_list += """<option value= "%s">%s</option>\n"""%(outcome_id, name)
    outcomes = outcomes%(outcome_list)

    # get bodies to display them in form.
    fields = """
                <h2>Fields</h2>
                <label>Type: <select name= "doc_type">"
                <option value="" selected>All</option>
            """

    # get doc types to display in form
    cursor.execute("select * from doc_types")
    for type_id, name in cursor.fetchall():
        fields += "<option value=\"%d\">%s</option>\n"%(type_id, name)
    fields += """</select></label>
                <br>
                %s
                 <br><label>Body: <select name= "body" onchange= "change_select(false)">
                 <option value="" selected>All</option>"""%(outcomes)

    cursor.execute("select * from bodies")
    for body_id, name in cursor.fetchall():
        fields += "<option value=\"%d\">%s</option>\n"%(body_id, name)
    fields += """
                </select></label><br>
                <br>
                <label style= 'display: none;' name= "venue">Venue: <select name= "venue"></select></label><br>
              """
    fields = "<div class='content'>" + fields + "</div>"
    fact_pattern_html = "<div class='content'>" + fact_pattern_html + "</div>"

    result = "<form action=\".\" method=\"POST\" enctype = \"multipart/form-data\" class=\"search\">"+search_field + "<div class='space-around'>" + fields + fact_pattern_html + "</div></form>"
    highlights = "<p style='display:inline;text-align:center;\
                background:red;color:white;'>" + highlights + "</p>"
    html = "<html>"+head("results", "Search results") + header(usr_id) + highlights+result +"</div>"+ footer() +"\n</html>"
    return html

@app.route(PREFIX + '/upload/', methods=['POST', 'GET'])
def upload():
    cookie, usr_id = login_check(request.cookies.get('session'))

    permission = permission_check(usr_id)
    if permission < 2:
        response = "<html>"+head("Error","Access Denied") + header(usr_id)+" <h2>Pending Status</h2> <div class=\"content\">"\
        "<h4>Your account status is pending, access is denied.<br>Your account must first be aproved by the administrator.</h4>"\
        +"</div>"+ footer() +"\n</html>"
        return response

    title = "upload page"
    description = ""
    upload_form = ""

    if request.method == 'POST':
        file_name = request.form.get("title")
        file = request.files["file"].read()
        file_desc = request.form.get("desc")
        file_type = request.form.get("doc_type")
        file_venue = request.form.get("venue")
        file_body = request.form.get("body")
        file_outcome = request.form.get("outcome")

        if file_name != "" and file != "":
            if len(file) > 4194304:
                upload_form += "<h3 color =\"red\>Upload Failed: The file is too big, the maximum is 4MB</h3>"
            else:
                try:
                    # saving file for extracting data.
                    with open("temp.docx", 'wb') as f:
                        f.write(file)
                    file_as_text = docx2txt.process("temp.docx")

                    db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=False, charset='utf8')
                    cursor =db.cursor()

                    sql = """insert into docs (file_name, content, description, venue_id, body, outcome, plain_text) values (%s, %s, %s, %s, %s, %s, %s)"""
                    # insert document into database

                    cursor.execute(sql, (file_name, file, file_desc, file_venue, file_body, file_outcome, str(file_as_text), ))
                    doc_id = cursor.lastrowid
                    flag = True
                    # insert the fact patterns
                    for pattern, on in request.form.to_dict().items():
                        if on == "on":
                            if flag:
                                flag = False
                            cursor.execute("insert into rel_fact_doc values(%s, %s)"%(pattern, doc_id))

                    if flag:
                        raise Exception('The user did not submit any fact pattern.')

                    # insert the user as the author
                    cursor.execute("insert into authorship values (%d, %d)"%(usr_id, doc_id))

                    # insert type
                    cursor.execute("insert into rel_docs_types values(%s, %s)"%(file_type, doc_id))

                    # extract citations from docx file and save them to db
                    cursor.execute("select auth_id, regex from authorities")
                    citation_sql = """insert into citations (cite, authority) values (%s, %s)"""
                    rel_citation_sql = """insert into rel_citations values (%s, %s)"""

                    for auth_id, regex in cursor.fetchall():
                        #return str(set(re.findall(regex, file_as_text)))
                        for cite in set(re.findall(regex, file_as_text)):
                            cursor.execute("select cite_id from citations where cite = %s", (cite,))
                            cur= cursor.fetchone()[0]
                            if cur == None:
                                cursor.execute(citation_sql, (cite, auth_id))
                                cursor.execute(rel_citation_sql, (doc_id, cursor.lastrowid, ))
                            else:
                                cursor.execute(rel_citation_sql, (doc_id, cur, ))

                    cursor.execute("select org_id from users where usr_id = %s", (usr_id, ))
                    org = cursor.fetchone()[0]

                    cursor.execute("select upload from orgs where org_id = %s", (org, ))
                    upload = cursor.fetchone()[0]
                    cursor.execute("insert into org_doc_log values(%s, %s)", (doc_id, org, ))
                    cursor.execute("update orgs set upload = %s where org_id= %s", (upload + 1, org, ))
                    db.commit()
                    db.close()
                    upload_form += "<h3 style=\"background-color: #77FF73;text-align:center;\">Your file was uploaded successfully.</h3>"

                except:
                    upload_form += "<h3 style=\"background-color: #FF522D;text-align:center;\">Could not upload the document.</h3>"
        else:
            upload_form += "<h3 style=\"color:red\">No document was uploaded.</h3>"

    try:
        db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
        cursor =db.cursor()

        # get outcomes to display in upload
        outcomes = """
                    <br>
                    <label>
                    Outcome:
                    <select name= "outcome" required>
                    <option value="" selected disabled hidden> Select an Option </option>
                    %s
                    </select></label>
                    <br>
                   """
        cursor.execute("select * from outcomes")
        outcome_list = ""
        for outcome_id, name in cursor.fetchall():
            outcome_list += """<option value= "%s">%s</option>\n"""%(outcome_id, name)
        outcomes = outcomes%(outcome_list)

        # get bodies to display them in form.
        fields = """<div class="space-around">
                    <div><h2>Upload Form</h2>
                    Document Title:
                    <input name="title" required><br><br>
                    <label>Type: <select name= "doc_type" required>
                    <option value="" selected disabled hidden> Select an Option </option>
                """

        # get doc types to display in form
        cursor.execute("select * from doc_types")
        for type_id, name in cursor.fetchall():
            fields += "<option value=\"%d\">%s</option>\n"%(type_id, name)
        fields += """</select></label>
                    <br>
                    %s
                     <br><label>Body: <select name= "body" onchange= "change_select()" required>
                     <option value="" selected disabled hidden> Select an Option </option>"""%(outcomes)

        cursor.execute("select * from bodies")
        for body_id, name in cursor.fetchall():
            fields += "<option value=\"%d\">%s</option>\n"%(body_id, name)

        fields += "</select></label><br>\n"

        fields += """
                    <br>
                     <label style= 'display: none;' name= "venue">Venue: <select name= "venue"></select></label><br><br>Description:<br>
                     <textarea name="desc" placeholder= "Enter a brief description about the document." rows="4" cols="50" required></textarea><br><br>
                     <label>Upload Brief:  <input type = "file" name = "file" required>
                     <input type="hidden" name="MAX_FILE_SIZE" value="4194304" /></label>
                     <br></div>"""


        cursor.execute("select * from fact_patterns")
        all_pats = list(cursor.fetchall())
        org_pats = []
        for pattern in all_pats:
            if '000000' in pattern[0]:
                print(pattern)
                pat_copy = pattern[0][:3]
                org_pats.append([pattern])
                for pat in all_pats:
                    if pat[0][:3] == pat_copy and pat != pattern:
                        org_pats[-1].append(pat)

        fact_pattern_html = "<div><h2>Fact Pattern</h2> <p>Check all the boxes that apply to this document.</p>"
        for pattern in org_pats:
            fact_pattern_html += """<label class="container">
                                    <input type="checkbox" class= 'main' name="%s">
                                    <span class="checkmark"></span>
                                    <span class="on-top">%s</span>
                                    </label>
                                  """%(pattern[0][0], pattern[0][1])
            if len(pattern) > 1:
                fact_pattern_html += """<div class= "%s" hidden> """%(pattern[0][0])
                for pat in pattern[1:]:
                    fact_pattern_html += """<label>
                                          <input type="checkbox" name="%s"> %s
                                          </label><br>"""%(pat[0], pat[1])
                fact_pattern_html += "</div>"
        fact_pattern_html += "</div></div><br><center><button type=\"submit\" onclick=\"return check_fact_pattern();\">Submit</button></center></form>"


    except:
        fields = "There was a problem fetching the bodies"
    upload_form += "<form action=\".\" method=\"POST\" enctype = \"multipart/form-data\">"\
                    + fields + fact_pattern_html


    html = "<html>"+head(title,description) + header(usr_id) + upload_form + footer() +"\n</html>"
    return html

@app.route(PREFIX + '/admin/', methods=['GET', 'POST'])
def admin():
    cookie, usr_id = login_check(request.cookies.get('session'))
    permission = permission_check(usr_id)

    title,description = "Admin", "Administer Users"

    if permission >= 3:

        try:
            highlights = ""
            if "delete" in request.form and request.method == "POST":
                try:
                    db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=False)
                    cursor =db.cursor()

                    del_usr = int(request.form["delete"])
                    cursor.execute("select role from users where usr_id = %s", (del_usr, ))
                    if cursor.fetchone()[0] < permission:
                        cursor.execute("select doc_id from authorship where usr_id = %s", (del_usr, ))
                        all_docs = cursor.fetchall()
                        if all_docs == None:
                            cursor.execute("delete from users where usr_id = %s", (del_usr, ))
                        else:
                            cursor.execute("delete from authorship where usr_id = %s", (del_usr, ))
                            for doc in all_docs:
                                cursor.execute("select * from authorship where doc_id = %s", (doc[0], ))
                                if cursor.fetchone() == None:
                                    cursor.execute("delete from rel_docs_types where doc_id = %s", (doc[0], ))
                                    cursor.execute("delete from rel_fact_doc where doc_id = %s", (doc[0], ))
                                    cursor.execute("delete from rel_citations where doc_id = %s", (doc[0], ))
                                    cursor.execute("delete from docs where doc_id = %s", (doc[0], ))
                            cursor.execute("delete from users where usr_id = %s", (del_usr, ))
                        db.commit()
                        db.close()
                        highlights = "<p style=\"background-color: #77FF73;text-align:center;\">User " + str(del_usr) + " was succesfully deleted.</p>"
                    else:
                        highlights += "<p style=\"background-color: #FF4545;text-align:center;\">You do not have the permission to delete this user.</p>"
                except:
                    highlights  += "<p style=\"background-color: #FF4545;text-align:center;\">There was a problem updating the users, with the server:</p>"

            db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
            cursor =db.cursor()

            if "submit" in request.form:
                try:
                    flag = 0
                    for u_id, role in request.form.items():
                        if u_id not in ['submit', 'delete']:
                            q= "update users set role = %s where usr_id = %s and role <> %s and role < %s"% (role, u_id, role, permission)
                            if cursor.execute(q):
                                flag = 1
                    if flag:
                        highlights += "<p style=\"background-color: #77FF73;text-align:center;\">The users were updated</p>"
                except Exception as e:
                    highlights  += "<center style=\"background=red\">There was a problem updating the users, with the server</center>" + str(e)


            if "archive" in request.args:
                if request.args["archive"] == "1":
                    temp = "role = 1"
                    archive = "0\">Show unarchived"
                else:
                    archive = "1\">Show Archived"
                    temp = "role <> 1"
            else:
                archive = "1\">Show Archived"
                temp = "role <> 1"

            cursor.execute("SELECT COUNT(usr_id) FROM users %s"%("where " + temp))
            total_pages = ceil(int(cursor.fetchone()[0])/NUM_OF_DOCS_PER_PAGE)-1

            if 'page' in request.args:
                try:
                    if int(request.args['page']) >= 1:
                        cursor.execute("SELECT COUNT(doc_id) FROM docs")
                        page = int(request.args['page'])-1
                        if page > total_pages:
                            page = total_pages
                    else:
                        db.close()
                        return "There is no page number, " + request.args['page']
                except:
                    db.close()
                    return "There is no page " + request.args['page']
            else:
                page = 0

            if permission >= 4: # for super admin
                sql = "SELECT usr_id, name, email, role FROM users WHERE %s ORDER BY role LIMIT %d, %d"%(temp, page * NUM_OF_DOCS_PER_PAGE, NUM_OF_DOCS_PER_PAGE)
            else: # for org admin
                if len(temp) > 0:
                    temp += " and"
                cursor.execute('select org_id from users where usr_id = %s'%usr_id)
                sql = "SELECT usr_id, name, email, role FROM users WHERE %s org_id = %s ORDER BY role LIMIT %d, %d"\
                %(temp, cursor.fetchone()[0], page * NUM_OF_DOCS_PER_PAGE, NUM_OF_DOCS_PER_PAGE)



            cursor.execute("select * from roles")
            roles = list(cursor.fetchall()) # list of available roles

            all_users = """<form action="." method="POST"><table class="w3-table-all w3-hoverable">
                            <tr class="w3-light-grey">
                                <th>User ID</th>
                                <th>Name</th>
                                <th>E-mail</th>
                                <th>Permissions</th>
                                <th>Actions</th>
                            </tr>"""
            # create all the users along with their permissions/forms in html
            cursor.execute(sql)
            for u_id, name, email, perm in cursor.fetchall():
                perm_list = roles.copy()
                cur_perm = perm_list.pop(perm)
                all_users +="""<tr><td>%s</td><td>%s</td>
                                <td>%s</td>
                                <td>
                                <select name="%s">
                                <option value="%s">%s</option>
                            """%(u_id, name.capitalize(), email, u_id, cur_perm[0], cur_perm[1])
                for item in perm_list:
                    all_users += "<option value=\"%s\">%s</option>"%(item[0], item[1])


                all_users += """
                                </select></td>
                                <td>
                                <a href="%s">
                                <button type= "button">Modify</button></a>
                                <button name="delete" value= "%s" type= "submit" style= "background-color: #f44336; color: white;" onclick="return confirm('*WARNING*\nDeleting this user will delete all related data ( e.g. documents) cannot be recovered. You can also archive users by selecting archive from the permissions dropdown menu.')">Delete</button>
                                </td></tr>
                            """%(url_for('usr_settings', user=int(u_id)), u_id)

            # define the tags and links for each page
            page_nav = ""
            for page_num in [numb for numb in range(page-3, page+3) if numb >= 0 and numb <= total_pages]:
                if page_num == page:
                    page_nav += f"<a class=\"active\" href=\"#\">{page_num+1}</a>"
                else:
                    page_nav += f"<a href=\"{url_for('admin', page=page_num+1)}\">{page_num+1}</a>"
            if total_pages > 3:
                page_nav= "<div class=\"pagination\"><a href=\"/admin/?page=1\">First</a>" + page_nav + "<a href=\"/docs/?page=%d\">Last</a></div>"%(total_pages+1)
            else:
                page_nav= "<div class=\"pagination\">" + page_nav + "</div>"

            all_users += '</table><br><button name=\'submit\' type="submit" onclick= "return confirm(\'Are you sure you want to make these changes?\')">Save</button></form><br>' + page_nav
        except:
            print("Error: could not fetch data.")
            all_users = "<center>There was a problem fetching the document.</center>"
        if permission_check(usr_id) < 2:
            return make_response(redirect(url_for('home'), code=302))
        html = "<html>"+head(title,description) + header(usr_id)+ highlights + "<h2>All Users</h2> <center><div class=\"content\"><a href = \""+ PREFIX +"/admin/?archive=%s</a>"%(archive) + all_users  +"</div></center>"+ footer() +"\n</html>"
        db.close()
        return html
    else:
        return make_response(redirect(url_for('home'), code=302))

@app.route(PREFIX + '/doc/', methods=['GET', 'POST'])
def doc():
    cookie, usr_id = login_check(request.cookies.get('session'))
    permission = permission_check(usr_id)

    if permission >= 2:

        if "download" in request.args:
            doc_id = request.args['download']
            if doc_id:
                return download_filed(doc_id, usr_id)
            else:
                return "Your downloads are too high. Please upload."


        highlights = ""
        # download file
        if request.method == "POST":
            doc_id = request.form.get('download')
            if doc_id:
                return download_filed(doc_id, usr_id)

            cite_id = request.form.get('voteUp')
            if permission >= 3:
                if cite_id:
                     sent = vote(cite_id, 1, usr_id)
                else:
                    cite_id = request.form.get('voteDown')
                    if cite_id:
                        sent = vote(cite_id, -1, usr_id)
                    else:
                        sent = None
            else:
                sent =None
            if sent != None:
                highlights = """<p style="background:yellow;text-align:center;padding:15px;">Vote successful!</p>"""
            else:
                highlights = """<p style="background:cyan;text-align:center;padding:15px;">Vote was unsuccessful.</p>"""

        # get the document details page
        if "docID" in request.args:
            try:
                db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
                cursor =db.cursor()

                doc_id= int(request.args["docID"])

                cursor.execute("select file_name, description, venue_id, body from docs where doc_id = %s"%(doc_id))


                fetched = cursor.fetchone()
                if fetched == None:
                    return "That document does not exists"

                name = fetched[0]
                if fetched[3] != None:
                    cursor.execute("select name from bodies where body_id = %s", (fetched[3], ))
                    body = cursor.fetchone()[0]
                else:
                    body = "Does not have a body"

                if fetched[2] != None:
                    cursor.execute("select name from venues where venue_id = %s", (fetched[2], ))
                    venue = cursor.fetchone()[0]
                else:
                    venue = "Does not have a venue"

                if fetched[1] != None:
                    desc = fetched[1]
                else:
                    desc = "No description."

                #get the citations
                cursor.execute("select cite_id from rel_citations where doc_id = %s", (doc_id, ))
                cites = "<h3>Citations</h3><div class= \"space-around\">"

                for cite in cursor.fetchall():
                    cursor.execute("select * from citations where cite_id = %s", (cite[0], ))
                    temp1 = cursor.fetchall()[0]

                    cursor.execute("select name from authorities where auth_id = %s", (temp1[3] , ))
                    temp2 = cursor.fetchone()[0]

                    if temp1[2] > 0:
                        validity= "border: 2px solid #4CAF50;"
                    elif temp1[2] == 0:
                        validity= "border: 2px solid #c7c7c7;"
                    else:
                        validity= "border: 2px solid #d60000;"

                    if permission >= 3:
                        cites += """
                                 <div class ="card" style ="%s">
                                    Citation: %s <br>
                                    Authority: %s<br>
                                    Validity index: %s <br>
                                    <form method= "POST" style= "text-align: center">
                                    <button name= "voteUp" value= "%s" style="border-radius: 10pt;">
                                    <i class="fa fa-chevron-circle-up" style="font-size:48px;color:green"></i>
                                    </button>

                                    <button name= "voteDown" value= "%s" style="border-radius: 10pt;">
                                    <i class="fa fa-chevron-circle-down" style="font-size:48px;color:red"></i>
                                    </button>
                                    </form>
                                </div>
                                    """%(validity, temp1[1], temp2, temp1[2], temp1[0], temp1[0])
                    else:
                        cites += """
                             <div class ="card" style ="%s">
                                Citation: %s <br>
                                Authority: %s<br>
                                Validity index: %s <br>
                            </div>
                                """%(validity, temp1[1], temp2, temp1[2])


                cites += "</div>"
                body = """
                        <p>
                        Body: %s
                        </p>
                        <p>
                        Venue: %s
                        </p>
                        <p>
                        Description: %s
                        </p>
                        <p style="text-align: center;">
                        *This is a preview of the document and may not represent it's content/format accurately.<br>
                        <iframe type="application/pdf" onload= "iframe_loaded();"></iframe>
                        </p>
                        <form method="post">
                        <button value="%s" name= "download"> Download</button>
                        </form>
                       """%(body, venue, desc, doc_id)
                return "<html>"+head(name,desc) + header(usr_id)+"<h2>" + name +"</h2><div class=\"content\">"+ highlights+ body +"</div>"+ cites +footer() +"\n</html>"

            except:
                return "<html>"+head("Not found","") + header(usr_id)+" <h2>Document Not found</h2> <center><div class=\"content\">"  +"</div></center>"+ footer() +"\n</html>"
    else:
        return make_response(redirect(url_for('usr_login'), code=302))


@app.route(PREFIX + '/getvenues/', methods=['GET', 'POST'])
def getjson():
    cookie, usr_id = login_check(request.cookies.get('session'))
    permission = permission_check(usr_id)

    if permission >= 2:
        if "text" in request.args:
            try: # to make sure the arg is an int.
                doc_id = int(request.args["text"])
            except:
                return "did not work"
            return download_filed(doc_id, usr_id, True)
        db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
        cursor =db.cursor()

        cursor.execute(\
        "select * from venues")

        return jsonify(cursor.fetchall())
        db.close()
    return 404
