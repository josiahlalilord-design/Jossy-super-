from flask import Flask, render_template_string, request, jsonify, send_from_directory
import datetime, json, os, uuid, random
from werkzeug.utils import secure_filename

app = Flask(__name__)

MEMORY_FILE = '/home/Lalilord/mysite/memory.json'
CHATS_FILE = '/home/Lalilord/mysite/chats.json'
UPLOAD_FOLDER = '/home/Lalilord/mysite/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_json(file, default={}):
    try:
        if os.path.exists(file):
            with open(file, 'r') as f: return json.load(f)
    except: pass
    return default

def save_json(file, data):
    try:
        with open(file, 'w') as f: json.dump(data, f)
    except: pass

MEMORY = load_json(MEMORY_FILE, {})
CHATS = load_json(CHATS_FILE, {})

PERSONALITIES = {
    'hype': {'prefix': ['YO LET\'S GOOO', 'BIG ENERGY'], 'suffix': ['Then we rule 🚀', 'Zuckerberg who? 😎']},
    'teacher': {'prefix': ['Good question', 'Let me break this down'], 'suffix': ['Try it and tell me', 'You got this']},
    'funny': {'prefix': ['LMAO wait', 'Broooo'], 'suffix': ['I weak 😂', 'Jossy don win']},
    'coder': {'prefix': ['Deploy it', 'Code first'], 'suffix': ['Push to GitHub', 'What we building next?']}
}

GUI = """<!DOCTYPE html>
<html><head><title>Jossy v2.5</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;font-family:system-ui;background:#000;color:#fff;overflow:hidden}
.tabs{position:fixed;bottom:0;width:100%;display:flex;background:#111;z-index:10}
.tabs button{flex:1;padding:14px 5px;background:#111;border:none;color:#666;font-size:12px;font-weight:bold}
.tabs button.active{color:#fff;border-top:2px solid #fe2c55}
.view{height:100vh;padding-top:55px;padding-bottom:65px;display:none}.view.active{display:block}
.personality-bar{position:fixed;top:0;width:100%;height:55px;padding:8px;background:#111;display:flex;gap:6px;border-bottom:1px solid #222;z-index:9}
.personality-bar button{flex:1;padding:8px 3px;background:#222;border:1px solid #333;color:#fff;border-radius:10px;font-size:10px}
.personality-bar button.active{background:#fe2c55;border-color:#fe2c55}
#ailog,#chatlog{height:calc(100vh - 120px);overflow-y:auto;padding:10px}
.msg{margin:8px;padding:10px;border-radius:12px;max-width:75%;word-wrap:break-word;font-size:14px}
.me{background:#fe2c55;margin-left:auto}.them{background:#333}.jossy{background:#1a3a1a;border-left:3px solid #81c784}
.inputbar{position:fixed;bottom:55px;width:100%;height:65px;padding:8px;background:#000;display:flex;gap:8px;border-top:1px solid #222;z-index:9}
input{flex:1;padding:14px;background:#222;border:1px solid #333;color:#fff;border-radius:22px;font-size:15px}
button.send{padding:14px 16px;background:#fe2c55;border:none;border-radius:22px;color:#fff;font-weight:bold;font-size:15px}
</style></head><body>

<div id="ai" class="view active">
  <div class="personality-bar">
    <button onclick="setMode('hype')" id="m_hype" class="active">🔥 Hype</button>
    <button onclick="setMode('teacher')" id="m_teacher">📚 Teacher</button>
    <button onclick="setMode('funny')" id="m_funny">😂 Funny</button>
    <button onclick="setMode('coder')" id="m_coder">💻 Coder</button>
  </div>
  <div id="ailog"></div>
  <div class="inputbar"><input id="aimsg" placeholder="Ask Jossy AI..."><button class="send" onclick="askAI()">Ask</button></div>
</div>

<div id="chat" class="view">
  <div id="chatlog"></div>
  <div class="inputbar">
    <input id="m" placeholder="Message room...">
    <input type="file" id="img" accept="image/*" style="display:none" onchange="sendImg()">
    <button class="send" onclick="document.getElementById('img').click()">📷</button>
    <button class="send" onclick="sendMsg()">Send</button>
  </div>
</div>

<!-- VIRAL LOOP BUTTON - Share Jossy -->
<button onclick="navigator.clipboard.writeText('https://lalilord.pythonanywhere.com'); alert('🔥 Link copied! Send to 5 friends')"
style="position:fixed;top:60px;right:10px;z-index:20;padding:8px 14px;background:#fe2c55;border:none;border-radius:25px;color:#fff;font-weight:bold;font-size:12px;box-shadow:0 4px 12px #fe2c55">
📤 Share Jossy</button>

<div class="tabs">
  <button onclick="tab('ai')" id="tai" class="active">Jossy AI</button>
  <button onclick="tab('chat')" id="tchat">Chats</button>
  <button onclick="tab('feed')" id="tfeed">For You</button>
</div>

<script>
let uid = localStorage.getItem('jossy_uid') || Math.floor(Math.random()*1e9); localStorage.setItem('jossy_uid', uid);
let room = 'global'; localStorage.setItem('jossy_room', room);
let mode = localStorage.getItem('jossy_mode') || 'hype';

function tab(v){ document.querySelectorAll('.view').forEach(e=>e.classList.remove('active')); document.getElementById(v).classList.add('active');
  document.querySelectorAll('.tabs button').forEach(e=>e.classList.remove('active')); document.getElementById('t'+v).classList.add('active'); if(v=='chat') loadChat(); }

function setMode(m){ mode = m; localStorage.setItem('jossy_mode', m); document.querySelectorAll('.personality-bar button').forEach(b=>b.classList.remove('active')); document.getElementById('m_'+m).classList.add('active'); addAI('jossy', 'Switched to ' + m.toUpperCase()); }

async function askAI(){
  let m = document.getElementById('aimsg').value; if(!m) return;
  addAI('me', m); document.getElementById('aimsg').value = '';
  try{
    let r = await fetch('/ai',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({msg:m,uid:uid,mode:mode})});
    let j = await r.json();
    if(j.reply) addAI('jossy', j.reply);
    else addAI('jossy', 'ERROR: No reply from server');
  }catch(e){
    addAI('jossy', 'ERROR: Connection failed. Check terminal.');
  }
}

function addAI(role, text){ let c = role=='me'?'me':'jossy'; document.getElementById('ailog').innerHTML += `<div class="msg ${c}"><b>${role=='me'?'You':'Jossy'}:</b> ${text}</div>`; document.getElementById('ailog').scrollTop = 1e9; }

addAI('jossy','v2.5 loaded. I will ALWAYS reply now. Test me!');

async function sendMsg(){ let m = document.getElementById('m').value; if(!m) return; await fetch('/msg',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({room:room,msg:m,uid:uid})}); document.getElementById('m').value=''; loadChat(); }
async function sendImg(){ let file = document.getElementById('img').files[0]; if(!file) return; let form = new FormData(); form.append('image', file); form.append('room', room); form.append('uid', uid); await fetch('/upload', {method:'POST', body:form}); document.getElementById('img').value=''; loadChat(); }
async function loadChat(){ let r = await fetch('/msg?room='+room); let j = await r.json(); document.getElementById('chatlog').innerHTML = j.map(x=>{ let img = x.img? `<br><img class="chat-img" src="/uploads/${x.img}">` : ''; return `<div class="msg ${x.uid==uid?'me':'them'}">${x.msg}${img}</div>`; }).join(''); document.getElementById('chatlog').scrollTop = 1e9; }
setInterval(()=>{ if(document.getElementById('chat').classList.contains('active')) loadChat(); }, 2000);
</script></body></html>"""

@app.route('/')
def home(): return render_template_string(GUI)

@app.route('/ai', methods=['POST'])
def ai():
    try:
        data = request.json; msg = data.get('msg','').lower(); uid = str(data.get('uid','0')); mode = data.get('mode', 'hype')
        if uid not in MEMORY: MEMORY[uid] = {'name': 'friend'}

        p = PERSONALITIES.get(mode, PERSONALITIES['hype'])
        prefix = random.choice(p['prefix']); suffix = random.choice(p['suffix'])

        if "my name is" in msg:
            name = msg.split("my name is")[1].strip().split()[0].capitalize()
            MEMORY[uid]['name'] = name; save_json(MEMORY_FILE, MEMORY)
            reply = f"{prefix} {name}! I remember you. {suffix}"
        elif "what is my name" in msg:
            reply = f"{prefix} Your name is {MEMORY[uid]['name']}! {suffix}"
        else:
            reply = f"{prefix} {MEMORY[uid]['name']}, you said: '{data.get('msg','')}'. {suffix}"

        return jsonify(reply=reply)
    except Exception as e:
        return jsonify(reply=f"ERROR: {str(e)}"), 200

@app.route('/msg', methods=['GET','POST'])
def msg():
    global CHATS
    try:
        if request.method == 'POST':
            d = request.json; room = d.get('room','global')
            if room not in CHATS: CHATS[room] = []
            CHATS[room].append({'msg': d.get('msg',''), 'uid': d.get('uid',''), 'time': datetime.datetime.now().isoformat()})
            CHATS[room] = CHATS[room][-50:]; save_json(CHATS_FILE, CHATS)
            return jsonify(ok=True)
        else:
            room = request.args.get('room','global')
            return jsonify(CHATS.get(room, []))
    except Exception as e:
        return jsonify([])

@app.route('/upload', methods=['POST'])
def upload():
    global CHATS
    try:
        file = request.files['image']; room = request.form.get('room','global'); uid = request.form.get('uid','0')
        filename = str(uuid.uuid4()) + secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        if room not in CHATS: CHATS[room] = []
        CHATS[room].append({'msg': '', 'img': filename, 'uid': uid, 'time': datetime.datetime.now().isoformat()})
        save_json(CHATS_FILE, CHATS)
        return jsonify(ok=True)
    except Exception as e:
        return jsonify(ok=False, error=str(e))

@app.route('/uploads/<filename>')
def uploaded_file(filename): return send_from_directory(UPLOAD_FOLDER, filename)

# ANALYTICS DASHBOARD - Track your growth
@app.route('/stats')
def stats():
    global CHATS, MEMORY
    total_msgs = sum(len(CHATS.get(r,[])) for r in CHATS)
    total_users = len(MEMORY)
    return f"""
    <html><body style="background:#000;color:#fff;font-family:system-ui;padding:40px;text-align:center">
    <h1>Jossy Super Stats 🔥</h1>
    <h2>Total Messages: {total_msgs}</h2>
    <h2>Total Users: {total_users}</h2>
    <p>Rooms: {list(CHATS.keys())}</p>
    <br><a href="/" style="color:#fe2c55;font-size:20px">Back to Jossy</a>
    </body></html>
    """

if __name__ == '__main__': app.run(debug=False, host='0.0.0.0', port=5000)