from flask import Flask
from flask import request,redirect,url_for
from flask import make_response, Response, jsonify
import re
import MySQLdb
import hashlib
import uuid
from io import StringIO
import re
import docx2txt
from math import ceil

db_host = "suffolkbriefbank.mysql.pythonanywhere-services.com"
db_user = "suffolkbriefbank"
db_passwd = "JXbasAaXPrJ94ELek"
db_db ="suffolkbriefbank$default"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx', 'csv'}
NUM_OF_DOCS_PER_PAGE = 1

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
        html = html + """<a href="/user/login/" class="navlink" onClick="createCookie('session','',-1);">login</a><body>"""
        html = html + """<a href="/user/new/" class="navnew">Create Account</a><body>"""
    else:
        html = html + f"""<a href="/user/settings/" class="navnew">Account Settings</a><body>
                         <a href="/" class="navlink" onClick="createCookie('session','',-1);">log out</a>"""

    html= html + "</div>"

    html = html + """<div class="content">
	<div id="icon" style="background-size: 100px 100px;background-image: url('https://suffolklitlab.org/images/seal.jpg');"><a href="/"><img src="https://suffolklitlab.org/images/space.gif" width="100px" height="100px;" border="0"/></a></div>
	<h1 style="text-align:center;">Brief Bank<sup> <font size=+1>Beta</font></sup><center style="margin-top:5px;"><span class="subtitle">@ Suffolk Law School</font></span></center></h1>

	<div class="menu_bar">
		<p style="text-align:center;">
		<a href="https://suffolklitlab.org/" class="menu">&nbsp;LIT Lab&nbsp;</a>&nbsp;
		<font style="color:#888;">|</font>&nbsp;
		<a href="/" class="menu">&nbsp;About&nbsp;</a>"""

    permission = permission_check(usr_id)
    if permission != 0:
        html =html + """
                &nbsp;<font style="color:#888;">|</font>&nbsp;
                <a href="/search/" class="menu">&nbsp;Documents&nbsp;</a>
                &nbsp;<font style="color:#888;">|</font>&nbsp;
                <a href="/upload/" class="menu">&nbsp;Upload&nbsp;</a>
                """
        if permission >= 2:
            html += """
                    &nbsp;<font style="color:#888;">|</font>&nbsp;
                    <a href="/admin" class="menu">&nbsp;Admin&nbsp;</a>
                    """

    html = html + """
		</p>
	</div><div background= "/static/images/background.jpg">\n\n"""

    return html

def footer():

    html = """</div>\n	<div id="footer" class="footer"><a href="https://suffolklitlab.org/"><img src="https://suffolklitlab.org/images/blue_logo.png" width="50px" align="left" border="0"/></a>
     <a href="/terms">Terms &amp; Privacy</a> | <a href="https://suffolklitlab.org/credits">Credits</a></font>
	</div>

</BODY>
</HTML>"""

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
        cursor.execute(f'select role from users where usr_id = {usr_id}')
        role = cursor.fetchone()
        db.close()
        return role[0]

    return 0

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def download_filed(doc_id):
    try:
        int(doc_id)
    except:
        return "That document does not exist."

    db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
    cursor =db.cursor()

    cursor.execute("select content, file_name from docs where doc_id = %s", (doc_id, ))
    query = cursor.fetchone()
    db.close()
    return Response(query[0], mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.docx"%(query[1])})

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

#===================================================================================================================================
#===================================================================================================================================
#===================================================================================================================================

app = Flask(__name__)

@app.errorhandler(401)
def custom_401(error):
    return Response('<This account does not have the permission to access this link.>', 401, {'WWW-Authenticate':'Basic realm="Login Required"'})


@app.route('/')
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

@app.route('/user/new/', methods=['GET','POST'])
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

        db_query = "INSERT INTO users (`name`, `email`, `crumb`, `salt`, `pass`, `created_on`) VALUES (%s, %s, conv(floor(rand() * 99999999999999), 20, 36), %s, %s, NOW(), %s);"
        c.execute(db_query, (username, email, salt, hash,))

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

@app.route('/user/login/', methods=['GET','POST'])
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
            <p><a href="/user/new/">Create a New Account</a></p>
            </form></div>"""%email

        body = body + """<div class="tosfloat">%s</div>"""%tos_html
        body = body + "</div>"

        response = make_response("<html>"+head(title,description)+header(usr_id,title)+body+footer()+"\n</html>")
        #if cookie:
        #    response.set_cookie('session', cookie)
        return response


@app.route('/user/settings/', methods=['GET','POST'])
def usr_settings(user= None):
    cookie, usr_id = login_check(request.cookies.get('session'))


    if (usr_id==None):
        response = make_response(redirect(url_for('usr_login'), code=302))
        new_header = header(None)
        return response
    else:
        new_header = header(usr_id)
        if 'user' in request.args:
            if permission_check(usr_id) >= 2:
                usr_id = int(request.args['user'])
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

@app.route('/terms/')
def tos():
    cookie, usr_id = login_check(request.cookies.get('session'))
    title = "Terms of Use"
    description = " "
    html = "<html>"+head(title,description)+header(usr_id)+"<div class=\"content\">"+tos_html+"</div>"+footer()+"\n</html>"
    return html

@app.route('/docs/', methods=['POST', 'GET'])
def docs(docs_list=None, search=None):
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

    if request.method == "POST":
        doc_id = request.form.get('download')
        if doc_id:
            return download_filed(doc_id)

    db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
    cursor =db.cursor()



    # pagination setup
    if docs_list == None:
        cursor.execute("SELECT COUNT(doc_id) FROM docs")
        total_pages = ceil(int(cursor.fetchone()[0])/NUM_OF_DOCS_PER_PAGE)-1
    else:
        total_pages= ceil(len(docs_list)/NUM_OF_DOCS_PER_PAGE)-1

    if 'page' in request.args:
        try:
            if int(request.args['page']) >= 1:
                page = int(request.args['page'])-1
                if page > total_pages:
                    page = total_pages
            else:
                return "There is no page number, " + request.args['page']
        except:
            return "There is no page " + request.args['page']
    else:
        page = 0

    if docs_list == None:
        return "worked1"
        sql = "SELECT file_name, doc_id FROM docs LIMIT %d, %d"%(page * NUM_OF_DOCS_PER_PAGE, NUM_OF_DOCS_PER_PAGE)
        cursor.execute(sql)
        docs= cursor.fetchall()
    else:
        start_slice = page * NUM_OF_DOCS_PER_PAGE
        end_slice = start_slice + 30

        docs = list()


        for item in list(docs_list)[start_slice:end_slice]:
            cursor.execute("SELECT file_name, doc_id FROM docs where doc_id =%s ", (item , ))
            docs.extend(cursor.fetchall())

    all_docs = """<center><form method="post"><table class="w3-table-all w3-hoverable"><tr>
                    <th>Brief Title</th>
                    <th>Type</th>
                    <th>File</th>
                    <th>Author(s)</th>
                    </tr>
                """

    #num_pages = ceil(cursor.execute("SELECT COUNT(*) FROM docs")/30)
    try:
        for doc, doc_id in docs:
            cursor.execute(f"select name from authorship inner join users on users.usr_id= authorship.usr_id where doc_id = {str(doc_id)}")
            authors = cursor.fetchall()
            authors = ", ".join(author[0] for author in authors)
            all_docs += """<tr><td><a href="%s">%s</a></td><td>Future field</td><td><button value="%s" name= "download"> Download</button></td><td>%s</td></tr>"""%(url_for('doc', docID= doc_id), doc, doc_id, authors)
        all_docs += '</form></table></center>'
    except:
        print("Error: could not fetch data.")
        all_docs = "<center>There was a problem fetching the documents.</center>"
    db.close()
    page_nav = ""

    for page_num in [numb for numb in range(page-3, page+3) if numb >= 0 and numb <= total_pages]:
        if page_num == page:
            page_nav += f"<a class=\"active\" href=\"#\">{page_num+1}</a>"
        else:
            page_nav += f"<a href=\"{url_for('docs', page=page_num+1)}\">{page_num+1}</a>"
    if total_pages > 3:
        page_nav= "<div class=\"pagination\"><a href=\"/docs/?page=1\">First</a>" + page_nav + "<a href=\"/docs/?page=%d\">Last</a></div>"%(total_pages+1)
    else:
        page_nav= "<div class=\"pagination\">" + page_nav + "</div>"

    all_docs += "</div>" + page_nav
    title = 'Documents'
    description= 'Documents'


    html = "<html>"+head(title,description) + header(usr_id)+" <h2>Documents</h2> <div class=\"content\">"+ all_docs + footer() +"\n</html>"
    return html

@app.route('/search/', methods=['POST', 'GET'])
def search():
    cookie, usr_id = login_check(request.cookies.get('session'))

    if usr_id == None:
        response = make_response(redirect(url_for('usr_login'), code=302))
        return response

    permission = permission_check(usr_id)
    if permission < 2:
        return "Not allowed!"

    db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
    cursor =db.cursor()

    if request.method == "POST":
        if len(request.form) > 0:
            docs_list= set()
            for pattern, on in request.form.to_dict().items():
                if on == "on":
                    cursor.execute("select doc_id from rel_fact_doc where pattern =%s", (pattern, ))
                    for item in cursor.fetchall():
                        docs_list.add(item[0])
            return docs(docs_list)

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
        fact_pattern_html = "<div><h2>Fact Pattern</h2><form method= \"POST\">"
    for pattern in org_pats:
        fact_pattern_html += """<label class="container">
                                <input type="checkbox" class= 'main' name="%s">
                                <span class="checkmark"></span>
                                <span class="on-top">%s</span>
                                </label>
                              """%(pattern[0][0], pattern[0][1])
        if len(pattern) > 1:
            fact_pattern_html += """<div style='display: none;' class= "%s"> """%(pattern[0][0])
            for pat in pattern[1:]:
                fact_pattern_html += """<label>%s
                                      <input type="checkbox" name="%s">
                                      </label><br>"""%(pat[1], pat[0])
            fact_pattern_html += "</div>"
    fact_pattern_html += "</div></div><br><button type=\"submit\">Search</button></center></form>"

    html = "<html>"+head("results", "Search results") + header(usr_id) + fact_pattern_html + footer() +"\n</html>"
    return html

@app.route('/upload/', methods=['POST', 'GET'])
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

        if file_name != "" and file != "":
            if len(file) > 4194304:
                upload_form += "<h3 color =\"red\>Upload Failed: The file is too big, the maximum is 4MB</h3>"
            else:
                try:
                    with open("temp.docx", 'wb') as f:
                        f.write(file)
                except:
                    upload_form +="could not open file in server."
                try:

                    db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=False)
                    cursor =db.cursor()

                    sql = """insert into docs (file_name, content, description, venue_id, body) values (%s, %s, %s, %s, %s)"""
                    #return str( (sql, (file_name, file, file_desc, file_venue, file_body)) )

                    # insert document into database
                    cursor.execute(sql, (file_name, file, file_desc, file_venue, file_body, ))

                    doc_id = cursor.lastrowid

                    # insert the fact patterns
                    for pattern, on in request.form.to_dict().items():
                        if on == "on":
                            cursor.execute("insert into rel_fact_doc values(%s, %s)"%(pattern, doc_id))
                    # insert the user as the author
                    cursor.execute("insert into authorship values (%d, %d)"%(usr_id, doc_id))

                    # insert type
                    cursor.execute("insert into rel_docs_types values(%s, %s)"%(file_type, doc_id))

                    # extract citations from docx file and save them to db
                    cursor.execute("select auth_id, regex from authorities")
                    file_as_text = docx2txt.process("temp.docx")
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

                    db.commit()
                    db.close()
                    upload_form += "<h3 color =\"green\">Your file was uploaded successfully.</h3>"

                except:
                    upload_form += "<h3 color ='red'>Could not upload the document.</h3>"
        else:
            upload_form += "<h3 style=\"color:red\">No document was uploaded.</h3>"

    try:
        db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
        cursor =db.cursor()

        # get bodies to display them in form.
        fields = """<div class="space-around">
                    <div><h2>Upload Form</h2>
                    Document Title:
                    <input name="title" required><br><br>
                    <label>Type: <select name= "doc_type">"
                    <option value="none" selected disabled hidden> Select an Option </option>
                """
        # get doc types to display in form
        cursor.execute("select * from doc_types")
        for type_id, name in cursor.fetchall():
            fields += "<option value=\"%d\">%s</option>\n"%(type_id, name)
        fields += """</select></label><br>
                     <br><label>Body: <select name= "body" onchange= "change_select()">
                     <option value="none" selected disabled hidden> Select an Option </option>"""

        cursor.execute("select * from bodies")
        for body_id, name in cursor.fetchall():
            fields += "<option value=\"%d\">%s</option>\n"%(body_id, name)

        fields += "</select></label><br>\n"

        fields += """</select>
                    <br>
                     <label style= "display:none;" name= "venue">Venue: <select name= "venue"></select></label><br><br>Description:<br>
                     <textarea name="desc" placeholder= "Enter a brief description about the document." rows="4" cols="50" required>
                     </textarea><br>
                     <label>Upload Brief:<input type = "file" name = "file" required>
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

        fact_pattern_html = "<div><h2>Fact Pattern</h2>"
        for pattern in org_pats:
            fact_pattern_html += """<label class="container">
                                    <input type="checkbox" class= 'main' name="%s">
                                    <span class="checkmark"></span>
                                    <span class="on-top">%s</span>
                                    </label>
                                  """%(pattern[0][0], pattern[0][1])
            if len(pattern) > 1:
                fact_pattern_html += """<div style='display: none;' class= "%s"> """%(pattern[0][0])
                for pat in pattern[1:]:
                    fact_pattern_html += """<label>%s
                                          <input type="checkbox" name="%s">
                                          </label><br>"""%(pat[1], pat[0])
                fact_pattern_html += "</div>"
        fact_pattern_html += "</div></div><br><center><button type=\"submit\">Submit</button></center></form>"


    except:
        fields = "There was a problem fetching the bodies"
    upload_form += "<form action=\".\" method=\"POST\" enctype = \"multipart/form-data\">"\
                    + fields + fact_pattern_html


    html = "<html>"+head(title,description) + header(usr_id) + upload_form + footer() +"\n</html>"
    return html

@app.route('/admin/', methods=['GET', 'POST'])
def admin():
    cookie, usr_id = login_check(request.cookies.get('session'))
    permission = permission_check(usr_id)

    title,description = "Admin", "Administer Users"

    if permission >= 3:

        try:
            db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
            cursor =db.cursor()

            highlights = ""
            if request.form:
                try:
                    flag = 0
                    for u_id, role in request.form.items():
                        q= "update users set role = %s where usr_id = %s and role <> %s"% (role, u_id, role)
                        cursor.execute(q)
                        flag += 1
                    if flag != 0:
                        highlights += "The users were updated."
                except:
                    highlights  += "There was a problem updating the users, with the server"

            cursor.execute("SELECT COUNT(usr_id) FROM users")
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
            if permission >=4:
                sql = "SELECT usr_id, name, email, role FROM users WHERE role <> 1 ORDER BY role LIMIT %d, %d"%(page * NUM_OF_DOCS_PER_PAGE, NUM_OF_DOCS_PER_PAGE)
            else:
                cursor.execute('select email from users where usr_id = %s'%usr_id)
                sql = "SELECT usr_id, name, email, role FROM users WHERE role <> 1 and email like LIKE '%{$%s}%' ORDER BY role LIMIT %d, %d"%(page * NUM_OF_DOCS_PER_PAGE, NUM_OF_DOCS_PER_PAGE, cursor.fetchone()[0].split("@")[-1])

            cursor.execute(sql)
            all_users = """<form action="." method="POST"><table class="w3-table-all w3-hoverable">
                            <tr class="w3-light-grey">
                                <th>User ID</th>
                                <th>Name</th>
                                <th>E-mail</th>
                                <th>Permissions</th>
                                <th>Actions</th>
                            </tr>"""

            # create all the users along with their permissions/forms in html
            for u_id, name, email, perm in cursor.fetchall():

                perm_list = [(0,'Pending'), (1, 'Archive'), (2, 'Contributer'), (3, 'Org Admin'), (4, 'Super Admin')]
                cur_perm = perm_list.pop(perm)
                other1= perm_list[0]
                other2= perm_list[1]
                other3= perm_list[2]

                all_users += f"""<tr><td>{u_id}</td>\n<td>{name.capitalize()}</td>\n
                                <td>{email}</td>
                                \n<td><select name="{u_id}">
                                    <option value="{cur_perm[0]}">{cur_perm[1]}</option>
                                    <option value="{other1[0]}">{other1[1]}</option>
                                    <option value="{other2[0]}">{other2[1]}</option>
                                    <option value="{other3[0]}">{other3[1]}</option>
                                  </select></td>\n
                                <td><a href="{url_for('usr_settings', user=int(u_id))}"><button type= "button">Reset</button></a>  <a href="{url_for('admin', delete=int(u_id))}"><button type= "button" style= "background-color: #f44336; color: white;">Delete</button></td></tr>"""

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

            all_users += '</table><br><button type="submit" onclick= "return confirm(\'Are you sure you want to make these changes?\')">Save</button></form>' + page_nav
        except:
            print("Error: could not fetch data.")
            all_users = "<center>There was a problem fetching the document.</center>"
        if permission_check(usr_id) < 2:
            return make_response(redirect(url_for('home'), code=302))

        html = "<html>"+head(title,description) + header(usr_id)+" <h2>All Users</h2> <center><div class=\"content\">"+ highlights + all_users  +"</div></center>"+ footer() +"\n</html>"
        db.close()
        return html
    else:
        return make_response(redirect(url_for('home'), code=302))

@app.route('/doc/', methods=['GET', 'POST'])
def doc():
    cookie, usr_id = login_check(request.cookies.get('session'))
    permission = permission_check(usr_id)

    if permission >= 3:

        # download file
        if request.method == "POST":
            doc_id = request.form.get('download')
            if doc_id:
                return download_filed(doc_id)

            cite_id = request.form.get('voteUp')
            if cite_id:
                if vote(cite_id, 1, usr_id):
                    return make_response(redirect(url_for('/'), code=302))
                else:
                    return make_response(redirect(url_for('/'), code=302))

            cite_id = request.form.get('voteDown')
            if cite_id:
                if vote(cite_id, -1, usr_id):
                    return make_response(redirect(url_for('/'), code=302))
                else:
                    return make_response(redirect(url_for('/'), code=302))



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
                        <form method="post">
                        <button value="%s" name= "download"> Download</button>
                        </form>
                       """%(body, venue, desc, doc_id)
                return "<html>"+head(name,desc) + header(usr_id)+"<h2>" + name + "</h2><div class=\"content\">"+ body +"</div>"+ cites +footer() +"\n</html>"

            except:
                return "<html>"+head("Not found","") + header(usr_id)+" <h2>Document Not found</h2> <center><div class=\"content\">"  +"</div></center>"+ footer() +"\n</html>"
    else:
        return make_response(redirect(url_for('usr_login'), code=302))


@app.route('/getjson/', methods=['GET', 'POST'])
def getjson():
    cookie, usr_id = login_check(request.cookies.get('session'))
    permission = permission_check(usr_id)

    if "venues" in request.args and permission >= 1:
        db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
        cursor =db.cursor()

        cursor.execute(\
        "select name, venue_id from venues where body_id = %s"%(request.args["venues"]))

        return jsonify(cursor.fetchall())
        db.close()
    return 404
