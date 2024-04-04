from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from solveSchedule import mainSched

groupList = []
profList = []
profList_ID = []
groupList_ID = []

app = Flask(__name__)


# Connect to DB
def connect_db():
    return sqlite3.connect("db/lite")


# ///////////////////////////////////// Home //////////////////////////////////////////////


@app.route("/")
def index():
    # Render DataFrames using Jinja2
    tablesGroup = [df.to_html(classes="data") for df in groupList]
    titlesGroup = [group for group in groupList_ID]
    zip_group = zip(
        tablesGroup, titlesGroup
    )  

    tablesProf = [df.to_html(classes="data") for df in profList]
    titlesProf = [professor for professor in profList_ID]
    zip_prof = zip(
        tablesProf, titlesProf
    ) 

    return render_template("index.html", zip_group=zip_group, zip_prof=zip_prof)


@app.route("/run_main_sched", methods=["POST"])
def run_main_sched():
    global groupList, profList, groupList_ID, profList_ID
    groupList, profList, groupList_ID, profList_ID = mainSched()
    return (
        "",
        204,
    )  


# ///////////////////////////////////// Groups //////////////////////////////////////////////
@app.route("/groups")
def groups():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groups ORDER BY group_id")
    groups = cursor.fetchall()
    conn.close()
    return render_template("groups.html", groups=groups)


# Add new group
@app.route("/add_group", methods=["POST"])
def add():
    conn = connect_db()
    cursor = conn.cursor()
    group_id = request.form["group_id"]
    group_name = request.form["group_name"]
    group_size = request.form["group_size"]
    cursor.execute(
        "INSERT INTO groups (group_id, group_name, group_size) VALUES (?, ?, ?)",
        (group_id, group_name, group_size),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("groups"))


# Delete a group
@app.route("/delete_group/<string:group_id>")
def delete(group_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groups WHERE group_id = ?", (group_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("groups"))


# ///////////////////////////////////// UCs //////////////////////////////////////////////
# Show UCs
@app.route("/ucs")
def ucs():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ucs ORDER BY uc_id")
    ucs = cursor.fetchall()
    conn.close()
    return render_template("ucs.html", ucs=ucs)


# Add UC
@app.route("/add_uc", methods=["POST"])
def add_uc():
    conn = connect_db()
    cursor = conn.cursor()
    uc_id = request.form["uc_id"]
    uc_name = request.form["uc_name"]
    cursor.execute("INSERT INTO ucs (uc_id, uc_name) VALUES (?, ?)", (uc_id, uc_name))
    conn.commit()
    conn.close()
    return redirect(url_for("ucs"))


# Delete UC
@app.route("/delete_uc/<string:uc_id>")
def delete_uc(uc_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ucs WHERE uc_id = ?", (uc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("ucs"))


# ///////////////////////////////////// Profs //////////////////////////////////////////////
# Show professors
@app.route("/profs")
def profs():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profs ORDER BY prof_id")
    profs = cursor.fetchall()
    conn.close()
    return render_template("profs.html", profs=profs)


# Add professor
@app.route("/add_prof", methods=["POST"])
def add_prof():
    conn = connect_db()
    cursor = conn.cursor()
    prof_id = request.form["prof_id"]
    prof_name = request.form["prof_name"]
    cursor.execute(
        "INSERT INTO profs (prof_id, prof_name) VALUES (?, ?)", (prof_id, prof_name)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("profs"))


# Delete professor
@app.route("/delete_prof/<string:prof_id>")
def delete_prof(prof_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM profs WHERE prof_id = ?", (prof_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("profs"))


# ///////////////////////////////////// Classrooms //////////////////////////////////////////////
# Show Classrooms
@app.route("/rooms")
def rooms():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rooms ORDER BY room_id")
    rooms = cursor.fetchall()
    conn.close()
    return render_template("rooms.html", rooms=rooms)


# Add new room
@app.route("/add_room", methods=["POST"])
def add_room():
    conn = connect_db()
    cursor = conn.cursor()
    room_id = request.form["room_id"]
    room_name = request.form["room_name"]
    room_size = request.form["room_size"]
    cursor.execute(
        "INSERT INTO rooms (room_id, room_name, room_size) VALUES (?, ?, ?)",
        (room_id, room_name, room_size),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("rooms"))


# Delete a room
@app.route("/delete_room/<string:room_id>")
def delete_room(room_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("rooms"))


# ///////////////////////////////////// Groups and UCs  //////////////////////////////////////////////
# Groups and UCs
@app.route("/groups_ucs")
def groups_ucs():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM groups_ucs ORDER BY group_id")
    groups_ucs = cursor.fetchall()
    conn.close()
    return render_template("groups_ucs.html", groups_ucs=groups_ucs)


# Add UC
@app.route("/add_groups_ucs", methods=["POST"])
def add_groups_ucs():
    conn = connect_db()
    cursor = conn.cursor()
    group_id = request.form["group_id"]
    ucs = request.form["ucs"]
    cursor.execute(
        "INSERT INTO groups_ucs (group_id, ucs) VALUES (?, ?)", (group_id, ucs)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("groups_ucs"))


# Delete UC
@app.route("/delete_groups_ucs/<string:group_id>")
def delete_groups_ucs(group_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groups_ucs WHERE group_id = ?", (group_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("groups_ucs"))


# ///////////////////////////////////// Profs and UCs  //////////////////////////////////////////////
# Profs and UCs
@app.route("/profs_ucs")
def profs_ucs():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profs_ucs ORDER BY prof_id")
    profs_ucs = cursor.fetchall()
    conn.close()
    return render_template("profs_ucs.html", profs_ucs=profs_ucs)


# Add UC
@app.route("/add_profs_ucs", methods=["POST"])
def add_profs_ucs():
    conn = connect_db()
    cursor = conn.cursor()
    prof_id = request.form["prof_id"]
    ucs = request.form["ucs"]
    cursor.execute("INSERT INTO profs_ucs (prof_id, ucs) VALUES (?, ?)", (prof_id, ucs))
    conn.commit()
    conn.close()
    return redirect(url_for("profs_ucs"))


# Delete UC
@app.route("/delete_profs_ucs/<string:prof_id>")
def delete_profs_ucs(prof_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM profs_ucs WHERE prof_id = ?", (prof_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("profs_ucs"))


# ///////////////////////////////////// Rooms and UCs  //////////////////////////////////////////////
# Rooms and UCs
@app.route("/rooms_ucs")
def rooms_ucs():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rooms_ucs ORDER BY uc_id")
    rooms_ucs = cursor.fetchall()
    conn.close()
    return render_template("rooms_ucs.html", rooms_ucs=rooms_ucs)


# Add Room-UCs
@app.route("/add_rooms_ucs", methods=["POST"])
def add_rooms_ucs():
    conn = connect_db()
    cursor = conn.cursor()
    uc_id = request.form["uc_id"]
    ucs = request.form["ucs"]
    cursor.execute("INSERT INTO rooms_ucs (uc_id, rooms) VALUES (?, ?)", (uc_id, rooms))
    conn.commit()
    conn.close()
    return redirect(url_for("rooms_ucs"))


# Delete Room-UCs
@app.route("/delete_rooms_ucs/<string:uc_id>")
def delete_rooms_ucs(uc_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rooms_ucs WHERE uc_id = ?", (uc_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("rooms_ucs"))


# ///////////////////////////////////// Days and Groups  //////////////////////////////////////////////
# Free days for groups
@app.route("/days_groups")
def days_groups():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM days_groups ORDER BY group_id")
    days_groups = cursor.fetchall()
    conn.close()
    return render_template("days_groups.html", days_groups=days_groups)


# Add free days for groups
@app.route("/add_days_groups", methods=["POST"])
def add_days_groups():
    conn = connect_db()
    cursor = conn.cursor()
    group_id = request.form["group_id"]
    days = request.form["days"]
    cursor.execute(
        "INSERT INTO days_groups (group_id, days) VALUES (?, ?)", (group_id, days)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("days_groups"))


# Delete free days for groups
@app.route("/delete_days_groups/<string:group_id>")
def delete_days_groups(group_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM days_groups WHERE group_id = ?", (group_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("days_groups"))


# ///////////////////////////////////// Days and Profs  //////////////////////////////////////////////
# Free days for professors
@app.route("/days_profs")
def days_profs():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM days_profs ORDER BY prof_id")
    days_profs = cursor.fetchall()
    conn.close()
    return render_template("days_profs.html", days_profs=days_profs)


# Add free days for professors
@app.route("/add_days_profs", methods=["POST"])
def add_days_profs():
    conn = connect_db()
    cursor = conn.cursor()
    prof_id = request.form["prof_id"]
    days = request.form["days"]
    cursor.execute(
        "INSERT INTO days_profs (prof_id, days) VALUES (?, ?)", (prof_id, days)
    )
    conn.commit()
    conn.close()
    return redirect(url_for("days_profs"))


# Delete free days for professors
@app.route("/delete_days_profs/<string:prof_id>")
def delete_days_profs(prof_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM days_profs WHERE prof_id = ?", (prof_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("days_profs"))


# ///////////////////////////////////// Constraints //////////////////////////////////////////////
@app.route("/const")
def const():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM const ORDER BY const_id")
    const = cursor.fetchall()
    conn.close()
    return render_template("const.html", const=const)


@app.route("/update_const/<const_id>", methods=["POST"])
def update_const(const_id):
    if request.method == "POST":
        new_value = request.form["const_value"]
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE const SET const_value = ? WHERE const_id = ?",
            (str(new_value), const_id),
        )
        conn.commit()
        conn.close()

    return redirect(url_for("const"))


# ///////////////////////////////////// Main //////////////////////////////////////////////
if __name__ == "__main__":
    app.run(debug=True)
