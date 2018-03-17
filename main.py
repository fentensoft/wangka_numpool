"""
Web server implements.

Created by Tony Liu (388848@163.com)
Date: 02/11/2018
"""
from flask import Flask, jsonify, render_template, request
from worker import Worker, getDistrictCode, product_list
from database import getDatabaseConnection
from regex_tags import regexTags


app = Flask(__name__)
w = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/start")
def start():
    global w
    w = Worker(
        request.args.get("product", "腾讯大王卡"),
        request.args.get("province", "上海"),
        request.args.get("provinceCode", "31"),
        request.args.get("city", "上海"),
        request.args.get("cityCode", "310"),
        request.args.get("groupKey", "34236498")
        )
    w.start()
    return jsonify({})

@app.route("/api/stop")
def stop():
    global w
    if w:
        w.stop()
    return jsonify({})

@app.route("/api/status")
def status():
    global w
    conn = getDatabaseConnection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM tbl_numbers;")
    ret = cur.fetchone()[0]
    conn.close()
    if w:
        return jsonify({
            "running": w.is_alive(),
            "count": ret,
            "product": w.product,
            "city": w.city,
            "cityCode": w.cityCode,
            "province": w.province,
            "provinceCode": w.provinceCode,
            "groupKey": w.groupKey,
            "autoTerminate": w.autoTerminate,
            "history": w.history
            })
    return jsonify({"running": False, "count": ret})
    

@app.route("/api/products")
def getProducts():
    return jsonify(list(product_list.keys()))


@app.route("/api/district")
def getDistrict():
    return jsonify(getDistrictCode(product_list[request.args["product"]]))


@app.route("/api/filters")
def getFilters():
    return jsonify(list(map(lambda i: i[1], regexTags)))


@app.route("/api/empty")
def empty():
    global w
    if w:
        if w.is_alive():
            return jsonify({})
    conn = getDatabaseConnection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tbl_numbers;")
    conn.commit()
    conn.close()
    return jsonify({})


@app.route("/api/nums")
def getNums():
    query = []
    if request.args.get("filter"):
        filters = request.args.get("filter").split("|")
        for f in filters:
            query.append("tag LIKE '%,{},%'".format(f))
    if request.args.get("custom"):
        query.append("number REGEXP '{}'".format(request.args.get("custom")))
    conn = getDatabaseConnection()
    cur = conn.cursor()
    if query:
        cur.execute("SELECT number,tag FROM tbl_numbers WHERE {};".format(" OR ".join(query)))
    else:
        cur.execute("SELECT number,tag FROM tbl_numbers;")
    ret = cur.fetchall()
    conn.close()
    ret = list(map(lambda i: {"number": i[0], "tag": i[1].strip(",")}, ret))
    return jsonify(ret)


@app.route("/api/autoTerminate")
def setAutoTerminate():
    global w
    print(request.args)
    w.autoTerminate = True if request.args.get("autoTerminate", "true") == "true" else False
    return jsonify({})


if __name__ == "__main__":
    app.run()
