from flask import Flask, render_template, request, session, redirect, send_file, flash
import math, os
from os import path
from werkzeug.utils import secure_filename
import pymysql
from board import Board
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'This is secret key'

@app.route('/')
def viewchart():
    return redirect('/bbs/page/1')

@app.route('/bbs/login')
def login():
    return render_template('bbs/bbs_login.html')

@app.route('/bbs/regist')
def regist():
    return render_template('bbs/bbs_regist.html')

@app.route('/bbs/regist1', methods=['post'])
def regist1():
    data = request.form
    conn = pymysql.connect(host='db4free.net', user='cloudheat', password='rlaehgus',
                           db='cloudheat', charset='utf8')
    curs = conn.cursor(pymysql.cursors.DictCursor)
    sql1 = "SELECT * FROM member WHERE id=%s"
    curs.execute(sql1, data['uid'])
    fetch_num = len(curs.fetchall())
    if fetch_num == 0:
        sql2 = "INSERT INTO member ('id', 'pw') VALUES %s, %s"
        curs.execute(sql2, (data['uid'], data['upwd']))
        flash('회원가입 성공')
        return redirect('/bbs/login')
    else:
        flash('이미 동일한 아이디가 가입되어 있습니다')
        return redirect('/bbs/regist')

@app.route('/bbs/login1', methods=['post'])
def login1():
    data = request.form
    conn = pymysql.connect(host='db4free.net', user='cloudheat', password='rlaehgus',
                           db='cloudheat', charset='utf8')
    curs = conn.cursor(pymysql.cursors.DictCursor)
    sql = "SELECT * FROM member WHERE ID=%s AND PW=%s"
    curs.execute(sql, (data['uid'], data['upwd']))
    fetch_num = len(curs.fetchall())
    if fetch_num == 1:
        session['uid'] = data['uid']
        flash('로그인 성공')
        return redirect('/bbs/page/1')
    else:
        flash('로그인 실패')
        return redirect('/bbs/login')

@app.route('/bbs/logout', methods=['post', 'get'])
def logout():
    session['uid'] = ''
    return redirect('/bbs/page/1')

@app.route('/bbs/page/<int:page>')
def page(page):
    try:
        conn = pymysql.connect(host='db4free.net', user='cloudheat', password='rlaehgus',
                               db='cloudheat', charset='utf8')
        curs = conn.cursor(pymysql.cursors.DictCursor)
        curs.execute("SELECT * FROM bbs")
        fetch_num = len(curs.fetchall())
        if fetch_num % 15 == 0:
            num = int(fetch_num / 15)
        else:
            num = int(fetch_num / 15)+1
        curs.execute('SET @RN:=0')
        # sql = "SELECT * FROM (SELECT @RN:=@RN+1 RN, b.* FROM bbs b WHERE (@RN:=0)=0)t1 WHERE RN BETWEEN %s AND %s"
        sql = "SELECT * FROM (SELECT FLOOR((RN-1)/15+1) page, t1.* FROM (SELECT @RN:=@RN+1 RN, b.* FROM bbs b WHERE (@RN:=0)=0)t1)t2 WHERE page=%s"
        curs.execute(sql, page)
        lists = curs.fetchall()
        sql1 = "SELECT a.fname, a.fsize FROM bbs b LEFT OUTER JOIN attach a ON b.num=a.num"
        curs.execute(sql1)
        flists = curs.fetchall()
        session['page_num'] = page
        if session.get('uid'):
            uid = session.get('uid')
        elif not session.get('uid'):
            uid = ''
        return render_template('bbs/bbs_list.html', lists=lists, uid=uid, flists=flists, num=num, message='')
    except Exception as e:
        print(e)
    finally:
        conn.close()

@app.route('/bbs/download/<int:fid>')  # 서버의 폴더구조와 다른 URL을 사용하여 요청한다
def download_attach(fid):
    print('다운로드 요청 :', fid)
    conn = pymysql.connect(host='db4free.net', user='cloudheat', password='rlaehgus',
                           db='cloudheat', charset='utf8')
    curs = conn.cursor(pymysql.cursors.DictCursor)
    curs.execute("SELECT * FROM attach WHERE fid=%s", fid)
    name = curs.fetchone()
    file_name = f"static/uploads/{secure_filename(name['fname'])}"   # 실제의 폴더 구조
    return send_file(file_name, mimetype=None, attachment_filename=name['or_fname'], as_attachment=True)

@app.route('/bbs/read/<int:num>')
def numcontent(num):
    try:
        conn = pymysql.connect(host='db4free.net', user='cloudheat', password='rlaehgus',
                               db='cloudheat', charset='utf8')
        curs = conn.cursor(pymysql.cursors.DictCursor)
        sql = 'UPDATE bbs SET hitcnt = hitcnt + 1 WHERE num = %s'
        curs.execute(sql, num)
        sql1 = 'SELECT b. *, a. * FROM bbs b LEFT OUTER JOIN attach a on b.num = a.num WHERE b.num = %s'
        curs.execute(sql1, num)
        content = curs.fetchone()
        content_list = content['content'].split('\n')
        names = get_file(curs, num)
        conn.commit()
        page_num = session.get('page_num')
        if session.get('uid'):
            uid = session.get('uid')
        elif not session.get('uid'):
            uid = ''
        return render_template('bbs/bbs_content.html', content=content, uid=uid, content_list=content_list,
                               names=names, page_num=page_num)
    except Exception as e:
        print(e)
    finally:
        conn.close()

def get_file(curs, num):
    curs.execute('SELECT * FROM attach WHERE num=%s', num)
    names = curs.fetchall()
    if names:
        return names
    else:
        return ''

@app.route('/bbs/edit/<int:num>')
def edit(num):
    try:
        conn = pymysql.connect(host='db4free.net', user='cloudheat', password='rlaehgus',
                               db='cloudheat', charset='utf8')
        curs = conn.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT * FROM bbs WHERE num=%s"
        curs.execute(sql, num)
        content = curs.fetchone()
        content_list = content['content'].split('\n')
        names = get_file(curs, num)
        page_num = session.get('page_num')
        if session.get('uid'):
            uid = session.get('uid')
        elif not session.get('uid'):
            uid = ''
        return render_template('bbs/bbs_edit.html', content=content, uid=uid, content_list=content_list, names=names
                               , page_num=page_num)
    except Exception as e:
        print(e)
    finally:
        conn.close()

@app.route('/bbs/update', methods=['post'])
def update():
    try:
        data = request.form
        conn = pymysql.connect(host='db4free.net', user='cloudheat', password='rlaehgus',
                               db='cloudheat', charset='utf8')
        curs = conn.cursor(pymysql.cursors.DictCursor)
        sql = "UPDATE bbs SET title=%s, content=%s where num=%s"
        res = curs.execute(sql, (data['title'], data['content'], data['num']))
        conn.commit()
        return redirect('/bbs/read/'+data['num'])
    except Exception as e:
        print(e)
    finally:
        conn.close()

@app.route('/bbs/delete/<int:num>', methods=['post', 'get'])
def delete(num):
    try:
        conn = pymysql.connect(host='db4free.net', user='cloudheat', password='rlaehgus',
                               db='cloudheat', charset='utf8')
        curs = conn.cursor(pymysql.cursors.DictCursor)
        sql = "DELETE FROM bbs WHERE num=%s"
        curs.execute(sql, num)
        conn.commit()
        return redirect('/bbs/page/1')
    except Exception as e:
        print(e)
    finally:
        conn.close()

@app.route('/bbs/write')
def write():
    page_num = session.get('page_num')
    if session.get('uid'):
        uid = session.get('uid')
    elif not session.get('uid'):
        uid = ''
    return render_template('bbs/bbs_write.html', uid=uid, page_num=page_num)


@app.route('/bbs/write1', methods=['post', 'get'])
def write1():
    uid = session.get('uid')
    data = request.form
    try:
        conn = pymysql.connect(host='db4free.net', user='cloudheat', password='rlaehgus',
                               db='cloudheat', charset='utf8')
        curs = conn.cursor(pymysql.cursors.DictCursor)
        sql1 = "INSERT INTO bbs(title, author, wdate, content) VALUES(%s, %s, NOW(), %s)"
        curs.execute(sql1, (data['title'], uid, data['content']))
        if not request.files.to_dict():
            conn.commit()
        else:
            saved = file_handler(curs)
            if saved:
                conn.commit()
            else:
                conn.rollback()
        return redirect('/bbs/page/1')
    except Exception as e:
        print(e)
    finally:
        conn.close()

def file_handler(curs):
    fdic = request.files.to_dict()
    upload_cnt = len(fdic)
    oknum = 0
    try:
        for key in fdic:
            or_fname = fdic[key].filename
            while True:
                b = path.exists('static/uploads/'+fdic[key].filename)
                a = fdic[key].filename.split('.')
                name = a[0]
                ext = a[1]
                dt_obj = datetime.now()
                timest = dt_obj.timestamp()
                ts = math.floor(timest*10000000)
                fdic[key].filename = name+str(ts)+'.'+ext
                if not b:
                    break
            fdic[key].save('static/uploads/'+f"{secure_filename(fdic[key].filename)}")
            n = os.path.getsize('D:/PyCharmProjects/PythonWeb/static/uploads/'+secure_filename(fdic[key].filename))
            n = ("{0:.3f}".format(n / 1024))
            sql2 = "SELECT max(num) FROM bbs"
            curs.execute(sql2)
            num = curs.fetchone()
            sql3 = "INSERT INTO attach(num, fname, fsize, or_fname) VALUES(%s, %s, %s, %s)"
            nrow = curs.execute(sql3, (num['max(num)'], fdic[key].filename, str(n)+" KB", or_fname))
            oknum += nrow
        if oknum == upload_cnt:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False

@app.route('/bbs/search')
def search():
    return render_template('bbs/bbs_search.html')

@app.route('/bbs/search1', methods=['post'])
def search1():
    data = request.form
    try:
        conn = pymysql.connect(host='db4free.net', user='cloudheat', password='rlaehgus',
                               db='cloudheat', charset='utf8')
        curs = conn.cursor(pymysql.cursors.DictCursor)
        sql = 'SELECT * FROM bbs WHERE '+data['s_menu']+' LIKE \'%'+data['search']+'%\''
        curs.execute(sql)
        info = curs.fetchall()
        return render_template('bbs/bbs_s_result.html', content=info)
    except Exception as e:
        print(e)
    finally:
        conn.close()

@app.route('/bbs/hitcnt/<int:num>', methods=['post'])
def hitcnt(num):
    try:
        conn = pymysql.connect(host='db4free.net', user='cloudheat', password='rlaehgus',
                               db='cloudheat', charset='utf8')
        curs = conn.cursor(pymysql.cursors.DictCursor)
        sql = "SELECT * FROM bbs WHERE num=%s"
        curs.execute(sql, num)
        data = curs.fetchone()
        sql = "UPDATE bbs SET hitcnt=%s WHERE num=%s"
        curs.execute(sql, (data['hitcnt']+1, num))
        conn.commit()
        return redirect('/bbs/read/'+str(data['num']))
    except Exception as e:
        print(e)
    finally:
        conn.close()

@app.route('/reinforcement')
def reinforcement_home():
    return render_template('reinforcement.html')
