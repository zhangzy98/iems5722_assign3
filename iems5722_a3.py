from flask import Flask
from flask import jsonify
from flask import request
from datetime import datetime
import math
import pymysql
import requests

app = Flask(__name__)
conn = pymysql.connect(
    host="localhost",
    user="dbuser",
    password="password",
    db="iems5722",
)


@app.route('/')
def hello_world():
    return "Hello IEMS5722"


@app.route("/api/a3/get_chatrooms")
def get_chatrooms():
    chatroom_result = {}  # To store the result
    conn.ping(reconnect=True)
    cur = conn.cursor(pymysql.cursors.DictCursor)  # To store the data collected into the dictionary format
    cur.execute("SELECT * FROM chatrooms")
    conn.commit()  # Update data
    chatroom_result["status"] = "OK"
    chatroom_result["data"] = cur.fetchall()
    return jsonify(chatroom_result)


@app.route("/api/a3/get_messages", methods=['GET'])
def get_messages():
    message_result = {}
    chatroom_id = int(request.args.get('chatroom_id'))
    page = int(request.args.get('page'))
    conn.ping(reconnect=True)
    cur = conn.cursor(pymysql.cursors.DictCursor)
    count_messages = "SELECT COUNT(`message`) FROM `messages` WHERE `chatroom_id` = %s"
    cur.execute(count_messages, (chatroom_id,))  # insert the query GET chatroom_id to the query SQL
    message_number = cur.fetchall()[0]["COUNT(`message`)"]  # convert the dictionary to int
    if page <= 0 or math.ceil(message_number / 5) < page:
        message_result["message"] = "<error message>"
        message_result["status"] = "ERROR"
    else:
        message_result["status"] = "OK"
        message_result["data"] = {}
        message_result["data"]["current_page"] = page
        message_result["data"]["messages"] = []

        # 1. retrieve the Table 'messages';
        # 2. order by time;
        # 3. every page has maximum of 5 messages from 0-4 5-9 10-14... Num_message = (PAGE-1) * 5
        message_query = "SELECT `id`, `chatroom_id`, `user_id`, `name`, `message`, `message_time` FROM `messages` " \
                        "WHERE `chatroom_id` = %s ORDER BY `message_time` DESC LIMIT %s, 5"
        cur.execute(message_query, (chatroom_id, (page - 1) * 5))
        conn.commit()

        # Insert the message into the dictionary
        for i in cur.fetchall():
            message_result["data"]["messages"].append(i)

        # Insert the total_pages to the dictionary
        message_result["data"]["total_pages"] = math.ceil(message_number / 5)

    return jsonify(message_result)


@app.route("/api/a3/send_message", methods=['POST'])
def post_messages():
    result = {}

    chatroom_id = int(request.form.get("chatroom_id"))
    user_id = int(request.form.get("user_id"))
    name = request.form.get("name")
    message = request.form.get("message")
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    firstIsOne = int(str(user_id)[0])  # Decide whether the student ID start with 1

    if chatroom_id < 1 or firstIsOne != 1 or name == "" or message == "":
        result["message"] = "<error message>"
        result["status"] = "ERROR"
    else:
        result["status"] = "OK"
        conn.ping(reconnect=True)
        cur = conn.cursor(pymysql.cursors.DictCursor)
        insert_message = "INSERT INTO `messages` (`chatroom_id`, `user_id`, `name`, `message`, `message_time`)" \
                         "VALUES (%s, %s, %s, %s, %s)"
        cur.execute(insert_message, (chatroom_id, user_id, name, message, timestamp))
        conn.commit()

    reqMsg = {'chatroom_id': chatroom_id, 'name': name, 'message': message, 'timestamp': timestamp}
    reqToBroad = requests.post(url="http://localhost:8001/api/a4/broadcast_room", data=reqMsg)
    reqTxt = reqToBroad.text
    print(reqTxt, flush=True)

    return jsonify(result)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
