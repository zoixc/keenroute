from flask import Flask, request, render_template, Response
import socket
import ipaddress  # <- добавлено

app = Flask(__name__)

def resolve_domain(domain, ipv6=False):
    try:
        family = socket.AF_INET6 if ipv6 else socket.AF_INET
        return list({res[4][0] for res in socket.getaddrinfo(domain, None, family)})
    except socket.gaierror:
        return []

def generate_routes(domains, gateway, mask, ipv6=False, route_type="host"):
    """
    Возвращает ПЛОСКИЙ текст (без HTML), построчно.
    """
    lines = []
    ips_collected = set()
    for domain in domains.splitlines():
        domain = domain.strip()
        if not domain:
            continue

        if route_type == "default":
            if not ipv6:
                lines.append(f"route add 0.0.0.0 mask 0.0.0.0 {gateway} :: rem default")
                ips_collected.add("0.0.0.0")
            else:
                lines.append(f"route add ::/0 mask 0.0.0.0 {gateway} :: rem default IPv6")
                ips_collected.add("::/0")
            continue

        ips = resolve_domain(domain, ipv6=ipv6)
        for ip in ips:
            if route_type == "host":
                line_mask = "255.255.255.255"
                route_ip = ip
            elif route_type == "network":
                # Если маска не указана, ставим /24 по умолчанию
                line_mask = mask if mask else "255.255.255.0"
                net = ipaddress.ip_network(f"{ip}/{line_mask}", strict=False)
                route_ip = str(net.network_address)
                line_mask = str(net.netmask)
            lines.append(f"route add {route_ip} mask {line_mask} {gateway} :: rem {domain}")
            ips_collected.add(route_ip)

    return "\n".join(lines), ips_collected

@app.route("/", methods=["GET", "POST"])
def index():
    result_v4, result_v6 = "", ""
    ips_v4, ips_v6 = set(), set()
    domains = ""
    gateway = "0.0.0.0"
    mask = ""
    ipv4 = True
    ipv6 = False
    route_type = "host"

    if request.method == "POST":
        domains = request.form.get("domains", "")
        gateway = request.form.get("gateway", "0.0.0.0")
        mask = request.form.get("mask", "")
        ipv4 = "ipv4" in request.form
        ipv6 = "ipv6" in request.form
        route_type = request.form.get("route_type", "host")
        action = request.form.get("action")

        if ipv4:
            result_v4, ips_v4 = generate_routes(domains, gateway, mask, ipv6=False, route_type=route_type)
        if ipv6:
            result_v6, ips_v6 = generate_routes(domains, gateway, mask, ipv6=True, route_type=route_type)

        if action == "download" and (result_v4 or result_v6):
            all_routes = (result_v4 + ("\n" if result_v4 and result_v6 else "") + result_v6).strip()
            return Response(
                all_routes,
                mimetype="text/plain",
                headers={"Content-Disposition": "attachment;filename=routes.bat"}
            )

    domains_count = len({d.strip() for d in domains.splitlines() if d.strip()})
    return render_template(
        "index.html",
        result_v4=result_v4,
        result_v6=result_v6,
        ips_v4=ips_v4,
        ips_v6=ips_v6,
        count_v4=len(result_v4.splitlines()) if result_v4 else 0,
        count_v6=len(result_v6.splitlines()) if result_v6 else 0,
        domains_count=domains_count,
        domains=domains,
        gateway=gateway,
        mask=mask,
        ipv4=ipv4,
        ipv6=ipv6,
        route_type=route_type
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
