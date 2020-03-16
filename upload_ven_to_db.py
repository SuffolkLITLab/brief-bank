import MySQLdb
import csv

db_host = "suffolkbriefbank.mysql.pythonanywhere-services.com"
db_user = "suffolkbriefbank"
db_passwd = "JXbasAaXPrJ94ELek"
db_db ="suffolkbriefbank$default"

db = MySQLdb.connect(host=db_host,user=db_user,passwd=db_passwd,db=db_db, autocommit=True)
cursor =db.cursor()

with open('Code Sheet.txt', "r") as csvfile:
    reader = csv.reader(csvfile, delimiter = "\t")

    for row in reader:
        cursor.execute("insert into venues(body_id, name) values(%s, %s)"%(row[2], "\""+ row[1].strip() +"\""  ))
    db.close()