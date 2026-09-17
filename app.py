from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "super_secret_key_for_sessions"

USERS_DATABASE = {
    "admin": {
        "password": "123",
        "role": "admin",
        "name": "მთავარი ადმინი",
        "university": "all",
        "group": "all"
    },
    "student1": {
        "password": "1234",
        "role": "student",
        "first_name": "გიორგი",
        "last_name": "ბერიძე",
        "university": "iliauni",
        "group": "ilieu_cs_1",
        "group_number": "CS-101"
    },
    "student2": {
        "password": "pass2",
        "role": "student",
        "first_name": "ნიმფა",
        "last_name": "კაპანაძე",
        "university": "gepi",
        "group": "gtu_math_101",
        "group_number": "MATH-101"
    }
}

TASKS_DATABASE = {
    "ილიაუნი - დავალება_1": [
        {"id": 1, "question": "რა არის მონეტის აგდებისას 'გერბის' მოსვლის ალბათობა?", "points": 0.5, "options": ["1/4", "1/2", "1/3", "1"], "answer": "1/2"},
        {"id": 2, "question": "კამათლის ერთხელ გაგორებისას, რა არის 6-იანის მოსვლის ალბათობა?", "points": 1.5, "options": ["1/6", "1/2", "5/6", "1/12"], "answer": "1/6"}
    ],
    "გეპი - დავალება_1": [
        {"id": 1, "question": "იპოვეთ ფუნქციის წარმოებული: f(x) = x²", "points": 1.0, "options": ["x", "2x", "x^3", "2"], "answer": "2x"}
    ]
}

for i in range(2, 11):
    TASKS_DATABASE[f"ილიაუნი - დავალება_{i}"] = []
    TASKS_DATABASE[f"გეპი - დავალება_{i}"] = []

DEADLINES_DATABASE = {}
COMPLETED_TESTS = {}

@app.route('/')
def home():
    if "user" in session:
        return redirect(url_for('view_task', task_name="ანალიტიკა"))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = USERS_DATABASE.get(username)

    if user and user['password'] == password:
        if user['role'] == 'admin':
            session['user'] = username
            session['role'] = user['role']
            session['name'] = user.get('name', username)
            session['university'] = user.get('university', 'all')
            return redirect(url_for('view_task', task_name="ადმინისტრირება"))
        
        if user['role'] == 'student':
            session['user'] = username
            session['role'] = user['role']
            session['name'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or username
            session['university'] = user.get('university')
            session['group'] = user.get('group')
            return redirect(url_for('view_task', task_name="ანალიტიკა"))

    return render_template('login.html', error="არასწორი მომხმარებელი (მეილი) ან პაროლი!")

@app.route('/register', methods=['POST'])
def register():
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password')
    university = request.form.get('university')

    if university == 'iliauni' and not email.endswith('@iliauni.edu.ge'):
        return render_template('login.html', error="ილიაუნის სტუდენტის მეილი აუცილებლად უნდა მთავრდებოდეს @iliauni.edu.ge-ით!")
    
    if university == 'gepi' and not email.endswith('@gtu.ge'):
        return render_template('login.html', error="გეპის სტუდენტის მეილი აუცილებლად უნდა მთავრდებოდეს @gtu.ge-ით!")

    if email in USERS_DATABASE:
        return render_template('login.html', error="მომხმარებელი ამ მეილით უკვე არსებობს სისტემაში!")

    default_group = "ilieu_cs_1" if university == "iliauni" else "gtu_math_101"
    default_group_num = "CS-101" if university == "iliauni" else "MATH-101"

    USERS_DATABASE[email] = {
        "password": password,
        "role": "student",
        "first_name": first_name,
        "last_name": last_name,
        "university": university,
        "group": default_group,
        "group_number": default_group_num
    }

    session['user'] = email
    session['role'] = 'student'
    session['name'] = f"{first_name} {last_name}".strip()
    session['university'] = university
    session['group'] = default_group

    return redirect(url_for('view_task', task_name="ანალიტიკა"))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/task/<path:task_name>')
def view_task(task_name):
    if "user" not in session:
        return redirect(url_for('home'))

    current_user = session['user']
    user_role = session['role']
    user_university = session.get('university', 'iliauni')

    questions = TASKS_DATABASE.get(task_name, [])
    deadline_str = DEADLINES_DATABASE.get(task_name)
    is_expired = False
    remaining_seconds = None

    if deadline_str:
        try:
            deadline_dt = datetime.strptime(deadline_str, "%Y-%m-%dT%H:%M")
            now = datetime.now()
            if now > deadline_dt:
                is_expired = True
                remaining_seconds = 0
            else:
                remaining_seconds = int((deadline_dt - now).total_seconds())
        except ValueError:
            pass

    user_result = COMPLETED_TESTS.get((current_user, task_name))
    is_submitted = user_result is not None

    iliauni_tasks = [t for t in TASKS_DATABASE.keys() if t.startswith("ილიაუნი - ")]
    gepi_tasks = [t for t in TASKS_DATABASE.keys() if t.startswith("გეპი - ")]

    iliauni_students = []
    gepi_students = []

    if task_name in ["ანალიტიკა", "ადმინისტრირება"]:
        all_students = []
        for u_name, u_info in USERS_DATABASE.items():
            if u_info.get("role") == "student":
                student_row = {
                    "username": u_name,
                    "university": u_info.get("university", ""),
                    "first_name": u_info.get("first_name", u_name),
                    "last_name": u_info.get("last_name", ""),
                    "group_number": u_info.get("group_number", "N/A"),
                    "scores": {}
                }
                for t_k in TASKS_DATABASE.keys():
                    res = COMPLETED_TESTS.get((u_name, t_k))
                    student_row["scores"][t_k] = res['score'] if res else None
                
                all_students.append(student_row)

        all_students.sort(key=lambda s: s["last_name"].lower())

        iliauni_students = [s for s in all_students if s["university"] == "iliauni"]
        gepi_students = [s for s in all_students if s["university"] == "gepi"]

    return render_template(
        'quiz.html',
        questions=questions,
        current_task=task_name,
        user_role=user_role,
        user_name=session.get('name'),
        user_university=user_university,
        iliauni_tasks=iliauni_tasks,
        gepi_tasks=gepi_tasks,
        iliauni_students=iliauni_students,
        gepi_students=gepi_students,
        score=user_result['score'] if is_submitted else None,
        total=user_result['total'] if is_submitted else None,
        user_answers=user_result['answers'] if is_submitted else {},
        is_expired=is_expired,
        is_submitted=is_submitted,
        remaining_seconds=remaining_seconds,
        completed_tests=COMPLETED_TESTS,
        tasks_database=TASKS_DATABASE
    )

@app.route('/admin/create_task', methods=['POST'])
def create_task():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    category = request.form.get('category')
    task_number = request.form.get('task_number')

    if category and task_number:
        new_task_name = f"{category} - დავალება_{task_number}"
        if new_task_name not in TASKS_DATABASE:
            TASKS_DATABASE[new_task_name] = []
        return redirect(url_for('view_task', task_name=new_task_name))

    return redirect(url_for('view_task', task_name="ადმინისტრირება"))

@app.route('/admin/delete_task/<path:task_name>')
def delete_task(task_name):
    if session.get('role') == 'admin':
        if task_name in TASKS_DATABASE:
            del TASKS_DATABASE[task_name]
        if task_name in DEADLINES_DATABASE:
            del DEADLINES_DATABASE[task_name]
        
        keys_to_del = [k for k in COMPLETED_TESTS.keys() if k[1] == task_name]
        for k in keys_to_del:
            del COMPLETED_TESTS[k]

        return redirect(url_for('view_task', task_name="ადმინისტრირება"))
    return redirect(url_for('home'))

@app.route('/admin/add_student', methods=['POST'])
def add_student():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    username = request.form.get('username')
    password = request.form.get('password')
    first_name = request.form.get('first_name', '')
    last_name = request.form.get('last_name', '')
    university = request.form.get('university', 'iliauni')
    group = request.form.get('group', 'ilieu_cs_1')
    group_number = request.form.get('group_number', '101')

    if username and password:
        USERS_DATABASE[username] = {
            "password": password,
            "role": "student",
            "first_name": first_name,
            "last_name": last_name,
            "university": university,
            "group": group,
            "group_number": group_number
        }

    return redirect(url_for('view_task', task_name="ადმინისტრირება"))

# --- წაშლის ახალი მექანიზმები (სახელი, გვარი, ნუმერაცია და სრული) ---
@app.route('/admin/delete_student_individual', methods=['POST'])
def delete_student_individual():
    if session.get('role') == 'admin':
        university = request.form.get('university')
        first_name_query = request.form.get('first_name', '').strip().lower()
        last_name_query = request.form.get('last_name', '').strip().lower()
        index_query = request.form.get('student_index', '').strip()
        
        matching_students = []
        for u_name, u_info in USERS_DATABASE.items():
            if u_info.get('role') == 'student' and u_info.get('university') == university:
                f_name = u_info.get('first_name', '').strip().lower()
                l_name = u_info.get('last_name', '').strip().lower()
                
                if f_name == first_name_query and l_name == last_name_query:
                    matching_students.append(u_name)
        
        target_username = None
        if matching_students:
            if index_query.isdigit():
                idx = int(index_query) - 1
                if 0 <= idx < len(matching_students):
                    target_username = matching_students[idx]
            else:
                target_username = matching_students[0] # თუ ნუმერაცია არ მიუთითა, იღებს პირველს
        
        if target_username and target_username in USERS_DATABASE:
            del USERS_DATABASE[target_username]
            keys_to_del = [k for k in COMPLETED_TESTS.keys() if k[0] == target_username]
            for k in keys_to_del:
                del COMPLETED_TESTS[k]
                
        return redirect(url_for('view_task', task_name="ადმინისტრირება"))
    return redirect(url_for('home'))

@app.route('/admin/delete_student/<path:username>')
def delete_student_direct(username):
    if session.get('role') == 'admin':
        if username in USERS_DATABASE and USERS_DATABASE[username].get('role') == 'student':
            del USERS_DATABASE[username]
            keys_to_del = [k for k in COMPLETED_TESTS.keys() if k[0] == username]
            for k in keys_to_del:
                del COMPLETED_TESTS[k]
        return redirect(url_for('view_task', task_name="ანალიტიკა"))
    return redirect(url_for('home'))

@app.route('/admin/delete_students_bulk', methods=['POST'])
def delete_students_bulk():
    if session.get('role') == 'admin':
        university = request.form.get('university')
        
        student_keys = [u for u, info in USERS_DATABASE.items() if info.get('role') == 'student' and info.get('university') == university]
        
        for u in student_keys:
            del USERS_DATABASE[u]
            keys_to_del = [k for k in COMPLETED_TESTS.keys() if k[0] == u]
            for k in keys_to_del:
                del COMPLETED_TESTS[k]
                
        return redirect(url_for('view_task', task_name="ადმინისტრირება"))
    return redirect(url_for('home'))
# ------------------------------------------------------------------

@app.route('/submit', methods=['POST'])
def submit():
    if "user" not in session:
        return redirect(url_for('home'))

    current_user = session['user']
    task_name = request.form.get('task_name')
    questions = TASKS_DATABASE.get(task_name, [])
    score = 0.0
    total = sum([q.get('points', 1.0) for q in questions])
    user_answers = {}

    for q in questions:
        ans = request.form.get(f"q_{q['id']}")
        user_answers[str(q['id'])] = ans
        if ans == q['answer']:
            score += q.get('points', 1.0)

    COMPLETED_TESTS[(current_user, task_name)] = {
        'score': round(score, 2),
        'total': round(total, 2),
        'answers': user_answers
    }

    return redirect(url_for('view_task', task_name=task_name))

@app.route('/set_deadline', methods=['POST'])
def set_deadline():
    if session.get('role') == 'admin':
        task_name = request.form.get('task_name')
        deadline = request.form.get('deadline')
        if task_name and deadline:
            DEADLINES_DATABASE[task_name] = deadline
        return redirect(url_for('view_task', task_name=task_name))
    return redirect(url_for('home'))

@app.route('/save_question', methods=['POST'])
def save_question():
    if session.get('role') != 'admin':
        return redirect(url_for('home'))

    task_name = request.form.get('task_name')
    q_id = request.form.get('question_id')
    question_text = request.form.get('question_text')
    points = float(request.form.get('points', 1.0))
    options = request.form.getlist('options[]')
    correct_idx = int(request.form.get('correct_index', 0))
    correct_answer = options[correct_idx] if options and correct_idx < len(options) else ""

    if task_name not in TASKS_DATABASE:
        TASKS_DATABASE[task_name] = []

    task_questions = TASKS_DATABASE[task_name]

    if q_id:
        q_id = int(q_id)
        for q in task_questions:
            if q['id'] == q_id:
                q['question'] = question_text
                q['points'] = points
                q['options'] = options
                q['answer'] = correct_answer
                break
    else:
        new_id = max([q['id'] for q in task_questions], default=0) + 1
        task_questions.append({
            "id": new_id,
            "question": question_text,
            "points": points,
            "options": options,
            "answer": correct_answer
        })

    return redirect(url_for('view_task', task_name=task_name))

@app.route('/delete_question/<path:task_name>/<int:q_id>')
def delete_question(task_name, q_id):
    if session.get('role') == 'admin' and task_name in TASKS_DATABASE:
        TASKS_DATABASE[task_name] = [q for q in TASKS_DATABASE[task_name] if q['id'] != q_id]
    return redirect(url_for('view_task', task_name=task_name))

if __name__ == '__main__':
    app.run(debug=True)
