from flask import Flask, request, render_template_string, Response
import socket

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head>
    <title>Keenroute</title>
    <style>
        body {
            font-family: sans-serif;
            background: #f8f9fa;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            width: 650px;
            text-align: center;
        }
        textarea, input {
            width: 100%;
            padding: 10px;
            margin: 8px 0;
            border-radius: 6px;
            border: 1px solid #ccc;
            font-size: 14px;
        }
        button {
            padding: 10px 18px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            background: #007bff;
            color: white;
            font-size: 14px;
        }
        button:hover { background: #0056b3; }
        pre {
            background: #f4f4f4;
            padding: 12px;
            border-radius: 6px;
            text-align: left;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .buttons {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 10px;
        }
        .copy-btn {
            margin-top: 8px;
            background: #28a745;
        }
        .copy-btn:hover { background: #1e7e34; }
        .ip4 { color: #007bff; font-weight: bold; }
        .ip6 { color: #28a745; font-weight: bold; }
        h3 { margin-bottom: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Генератор маршрутов для Keenetic</h2>
        <form method="post" onsubmit="saveForm()">
            <label>Домены (по одному в строке):</label><br>
            <textarea name="domains" id="domains" rows="6">{{ domains }}</textarea><br>
            
            <label>Шлюз (gateway):</label><br>
            <input type="text" name="gateway" id="gateway" value="{{ gateway }}"><br>
            
            <label>Маска сети:</label><br>
            <input type="text" name="mask" id="mask" value="{{ mask }}"><br>
            
            <label>
                <input type="checkbox" name="ipv6" {% if ipv6 %}checked{% endif %}> Включить IPv6
            </label><br><br>
            
            <div class="buttons">
                <button type="submit" name="action" value="generate">Сгенерировать</button>
                {% if result_v4 or result_v6 %}
                    <button type="submit" name="action" value="download">Скачать .bat</button>
                {% endif %}
            </div>
        </form>

        {% if result_v4 or result_v6 %}
            {% if result_v4 %}
                <h3>IPv4 маршруты:</h3>
                <pre id="result_v4">{{ result_v4|safe }}</pre>
                <button class="copy-btn" onclick="copyToClipboard('result_v4')">Скопировать IPv4</button>
            {% endif %}
            {% if result_v6 %}
                <h3>IPv6 маршруты:</h3>
                <pre id="result_v6">{{ result_v6|safe }}</pre>
                <button class="copy-btn" onclick="copyToClipboard('result_v6')">Скопировать IPv6</button>
            {% endif %}
        {% endif %}
    </div>

    <script>
    function copyToClipboard(id) {
        const text = document.getElementById(id).innerText;
        navigator.clipboard.writeText(text).then(() => {
            alert("Скопировано!");
        });
    }

    function saveForm() {
        localStorage.setItem("domains", document.getElementById("domains").value);
        localStorage.setItem("gateway", document.getElementById("gateway").value);
        localStorage.setItem("mask", document.getElementById("mask").value);
        localStorage.setItem("ipv6", document.querySelector("input[name='ipv6']").checked);
    }

    window.onload = function() {
        if (localStorage.getItem("domains")) document.getElementById("domains").value = localStorage.getItem("domains");
        if (localStorage.getItem("gateway")) document.getElementById("gateway").value = localStorage.getItem("gateway");
        if (localStorage.getItem("mask")) document.getElementById("mask").value = localStorage.getItem("mask");
        if (localStorage.getItem("ipv6") === "true") document.querySelector("input[name='ipv6']").checked = true;
    }
    </script>
</body>
</html>
"""

def resolve_domain(domain, ipv6=False):
    try:
        family = socket.AF_INET6 if ipv6 else socket.AF_INET
        return list({res[4][0] for res in socket.getaddrinfo(domain, None, family)})
    except socket.gaierror:
        return []

def generate_routes(domains, gateway, mask, ipv6=False):
    lines = []
    for domain in domains.splitlines():
        domain = domain.strip()
        if not domain:
            continue
        ips = resolve_domain(domain, ipv6=ipv6)
        for ip in ips:
            cls = "ip6" if ipv6 else "ip4"
            lines.append(f"<span class='{cls}'>route add {ip}</span> mask {mask} {gateway} :: rem {domain}")
    return "\n".join(lines)

@app.route("/", methods=["GET", "POST"])
def index():
    result_v4, result_v6 = "", ""
    domains = ""
    gateway = "0.0.0.0"
    mask = "255.255.255.255"
    ipv6 = False

    if request.method == "POST":
        domains = request.form.get("domains", "")
        gateway = request.form.get("gateway", "0.0.0.0")
        mask = request.form.get("mask", "255.255.255.255")
        ipv6 = "ipv6" in request.form
        action = request.form.get("action")

        result_v4 = generate_routes(domains, gateway, mask, ipv6=False)
        if ipv6:
            result_v6 = generate_routes(domains, gateway, mask, ipv6=True)

        if action == "download" and (result_v4 or result_v6):
            plain_v4 = result_v4.replace("<span class='ip4'>","").replace("</span>","")
            plain_v6 = result_v6.replace("<span class='ip6'>","").replace("</span>","")
            all_routes = (plain_v4 + "\n" + plain_v6).strip()
            return Response(
                all_routes,
                mimetype="text/plain",
                headers={"Content-Disposition": "attachment;filename=routes.bat"}
            )

    return render_template_string(HTML, 
        result_v4=result_v4, result_v6=result_v6,
        domains=domains, gateway=gateway, mask=mask, ipv6=ipv6
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
