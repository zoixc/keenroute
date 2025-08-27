from flask import Flask, render_template, request, jsonify
import ipaddress

app = Flask(__name__)

def generate_routes(data, ipv6=False):
    lines = []
    for line in data.strip().splitlines():
        parts = line.split()
        if not parts:
            continue

        if len(parts) == 4 and parts[0].lower() == "route" and parts[1].lower() == "add":
            network, mask, gateway = parts[2], parts[4], parts[5] if len(parts) > 5 else "0.0.0.0"
        elif len(parts) == 3:
            network, mask, gateway = parts[0], parts[1], parts[2]
        else:
            continue

        try:
            ip_net = ipaddress.ip_network(f"{network}/{mask}", strict=False)
        except ValueError:
            continue

        if ipv6 and isinstance(ip_net, ipaddress.IPv6Network):
            lines.append(f"ip route {ip_net} gateway {gateway}")
        elif not ipv6 and isinstance(ip_net, ipaddress.IPv4Network):
            lines.append(f"ip route {ip_net} gateway {gateway}")

    return lines

@app.route("/", methods=["GET", "POST"])
def index():
    routes = []
    if request.method == "POST":
        input_data = request.form.get("routes", "")
        ipv6_enabled = request.form.get("ipv6", "off") == "on"
        routes = generate_routes(input_data, ipv6=ipv6_enabled)
    return render_template("index.html", routes=routes)

@app.route("/api/convert", methods=["POST"])
def api_convert():
    data = request.json.get("routes", "")
    ipv6_enabled = request.json.get("ipv6", False)
    routes = generate_routes(data, ipv6=ipv6_enabled)
    return jsonify({"routes": routes})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
