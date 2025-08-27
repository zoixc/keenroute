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
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f0f3f7;
            height: 100vh;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: #fff;
            padding: 30px 40px;
            border-radius: 12px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.12);
            width: 720px;
            max-width: 95%;
            opacity: 0;
            animation: fadeIn 0.5s ease forwards;
        }
        @keyframes fadeIn { to { opacity: 1; } }
        h2 { text-align: center; margin-bottom: 20px; color: #333; }
        textarea, input, select {
            width: 100%;
            padding: 10px 12px;
            margin: 6px 0;
            border-radius: 6px;
            border: 1px solid #ccc;
            font-size: 14px;
            font-family: inherit;
            box-sizing: border-box;
        }
        textarea { resize: none; height: 120px; }
        .row { display: flex; gap: 12px; align-items: center; justify-content: space-between; }
        .row > * { flex: 1; }
        .checkbox-row {
            display: flex;
            align-items: center;
            margin-top: 12px;
        }
        .checkbox-row label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 500;
            color: #555;
            cursor: pointer;
        }
        .checkbox-row input[type="checkbox"] {
            width: auto;
            height: auto;
            margin: 0;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            background: #007bff;
            color: white;
            font-size: 14px;
            transition: 0.3s ease, transform 0.2s ease;
        }
        button:hover { background: #0056b3; transform: translateY(-2px); }
        .copy-btn { margin-top: 8px; background: #28a745; }
        .copy-btn:hover { background: #1e7e34; transform: translateY(-2px); }
        pre {
            background: #f4f4f4;
            padding: 12px;
            border-radius: 6px;
            text-align: left;
            white-space: pre-wrap;
            word-wrap: break-word;
            opacity: 0;
            transform: translateY(10px);
            transition: opacity 0.5s ease, transform 0.5s ease;
            max-height: none;
            overflow: hidden;
        }
        pre.show { opacity: 1; transform: translateY(0); }
        label { display: block; text-align: left; margin-top: 12px; font-weight: 500; color: #555; }
        .buttons { display: flex; justify-content: center; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
        .ip4 { color: #007bff; font-weight: bold; }
        .ip6 { color: #28a745; font-weight: bold; }
        h3 { margin: 15px 0 5px; color: #444; display: flex; align-items: center; gap: 6px; }
        .icon { font-size: 16px; }
        .stats { margin: 10px 0; font-size: 13px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Keenroute</h2>
        <form method="post" onsubmit="saveForm()">
            <label>Домены (по одному в строке):</label>
            <textarea name="domains" id="domains">{{ domains }}</textarea>

            <label>Тип маршрута:</label>
            <select name="route_type">
                <option value="host" {% if route_type=="host" %}selected{% endif %}>Host (узел)</option>
                <option value="network" {% if route_type=="network" %}selected{% endif %}>Network (сеть)</option>
                <option value="default" {% if route_type=="default" %}selected{% endif %}>Default (по умолчанию)</option>
            </select>

            <div class="row">
                <div>
                    <label>Шлюз (gateway):</label>
                    <input type="text" name="gateway" id="gateway" value="{{ gateway }}">
                </div>
                <div>
                    <label>Маска сети (авто / по умолчанию):</label>
                    <input type="text" name="mask" id="mask" value="{{ mask }}">
                </div>
            </div>

            <div class="checkbox-row">
                <label>Включить IPv6 <input type="checkbox" id="ipv6" name="ipv6" {% if ipv6 %}checked{% endif %}></label>
            </div>

            <div class="buttons">
                <button type="submit" name="action" value="generate">Сгенерировать</button>
                {% if result_v4 or result_v6 %}
                    <button type="submit" name="action" value="download">Скачать .bat</button>
                {% endif %}
            </div>
        </form>

        {% if result_v4 %}
            <h3><span class="icon">🌐</span> IPv4 маршруты:</h3>
            <div class="stats">Маршрутов: {{ count_v4 }}, IP: {{ ips_v4|length }}, Уникальные домены: {{ domains_count }}</div>
            <pre id="result_v4">{{ result_v4|safe }}</pre>
            <button class="copy-btn" onclick="copyToClipboard('result_v4')">Скопировать IPv4</button>
        {% endif %}
        {% if result_v6 %}
            <h3><span class="icon">🛰️</span> IPv6 маршруты:</h3>
            <div class="stats">Маршрутов: {{ count_v6 }}, IP: {{ ips_v6|length }}, Уникальные домены: {{ domains_count }}</div>
            <pre id="result_v6">{{ result_v6|safe }}</pre>
            <button class="copy-btn" onclick="copyToClipboard('result_v6')">Скопировать IPv6</button>
        {% endif %}
    </div>

<script>
function copyToClipboard(id) {
    const text = document.getElementById(id).innerText.trim();
    navigator.clipboard.writeText(text).then(() => { alert("Скопировано!"); });
}

function saveForm() {
    localStorage.setItem("domains", document.getElementById("domains").value);
    localStorage.setItem("gateway", document.getElementById("gateway").value);
    localStorage.setItem("mask", document.getElementById("mask").value);
    localStorage.setItem("ipv6", document.querySelector("input[name='ipv6']").checked);
    localStorage.setItem("route_type", document.querySelector("select[name='route_type']").value);
}

window.onload = function() {
    if (!performance || !performance.getEntriesByType) return;
    let perf = performance.getEntriesByType("navigation")[0];
    if (perf && perf.type === "reload") {
        document.getElementById("domains").value = "";
        localStorage.removeItem("domains");
    } else {
        if (localStorage.getItem("domains")) document.getElementById("domains").value = localStorage.getItem("domains");
    }
    if (localStorage.getItem("gateway")) document.getElementById("gateway").value = localStorage.getItem("gateway");
    if (localStorage.getItem("mask")) document.getElementById("mask").value = localStorage.getItem("mask");
    if (localStorage.getItem("ipv6") === "true") document.querySelector("input[name='ipv6']").checked = true;

    const preBlocks = document.querySelectorAll("pre");
    preBlocks.forEach(pre => {
        if(pre.innerText.trim().length > 0){
            setTimeout(() => pre.classList.add("show"), 100);
        }
    });
};
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

def generate_routes(domains, gateway, mask, ipv6=False, route_type="host"):
    lines = []
    ips_collected = set()
    for domain in domains.splitlines():
        domain = domain.strip()
        if not domain:
            continue
        if route_type == "default":
            ip4 = "0.0.0.0"
            ip6 = "::/0"
            if not ipv6:
                lines.append(f"<span class='ip4'>route add {ip4}</span> mask 0.0.0.0 {gateway} :: rem default")
                ips_collected.add(ip4)
            else:
                lines.append(f"<span class='ip6'>route add {ip6}</span> mask 0.0.0.0 {gateway} :: rem default IPv6")
                ips_collected.add(ip6)
            continue
        ips = resolve_domain(domain, ipv6=ipv6)
        for ip in ips:
            cls = "ip6" if ipv6 else "ip4"
            line_mask = mask
            if route_type == "host":
                line_mask = "255.255.255.255"
            elif route_type == "network" and not mask:
                line_mask = "255.255.255.0"
            lines.append(f"<span class='{cls}'>route add {ip}</span> mask {line_mask} {gateway} :: rem {domain}")
            ips_collected.add(ip)
    return "\n".join(lines), ips_collected

@app.route("/", methods=["GET", "POST"])
def index():
    result_v4, result_v6 = "", ""
    ips_v4, ips_v6 = set(), set()
    domains = ""
    gateway = "0.0.0.0"
    mask = ""
    ipv6 = False
    route_type = "host"

    if request.method == "POST":
        domains = request.form.get("domains", "")
        gateway = request.form.get("gateway", "0.0.0.0")
        mask = request.form.get("mask", "")
        ipv6 = "ipv6" in request.form
        route_type = request.form.get("route_type", "host")
        action = request.form.get("action")

        result_v4, ips_v4 = generate_routes(domains, gateway, mask, ipv6=False, route_type=route_type)
        if ipv6:
            result_v6, ips_v6 = generate_routes(domains, gateway, mask, ipv6=True, route_type=route_type)

        if action == "download" and (result_v4 or result_v6):
            plain_v4 = result_v4.replace("<span class='ip4'>","").replace("</span>","")
            plain_v6 = result_v6.replace("<span class='ip6'>","").replace("</span>","")
            all_routes = (plain_v4 + "\n" + plain_v6).strip()
            return Response(
                all_routes,
                mimetype="text/plain",
                headers={"Content-Disposition": "attachment;filename=routes.bat"}
            )

    domains_count = len({d.strip() for d in domains.splitlines() if d.strip()})
    return render_template_string(HTML, 
        result_v4=result_v4, result_v6=result_v6,
        ips_v4=ips_v4, ips_v6=ips_v6,
        count_v4=len(result_v4.splitlines()) if result_v4 else 0,
        count_v6=len(result_v6.splitlines()) if result_v6 else 0,
        domains_count=domains_count,
        domains=domains, gateway=gateway, mask=mask, ipv6=ipv6,
        route_type=route_type
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
