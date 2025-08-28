from flask import Flask, request, render_template, Response, flash
import socket
import ipaddress

app = Flask(__name__)
app.secret_key = "keenroute-secret"

def resolve_domain(domain, ipv6=False):
    try:
        family = socket.AF_INET6 if ipv6 else socket.AF_INET
        return list({res[4][0] for res in socket.getaddrinfo(domain, None, family)})
    except socket.gaierror:
        return []

def generate_routes(domains, gateway, mask_ipv4="", prefix_ipv6=64, ipv6=False, route_type="host"):
    """
    Возвращает строки маршрутов и набор IP/сетей.
    Для IPv4 используется mask_ipv4, для IPv6 — prefix_ipv6.
    """
    lines = []
    ips_collected = set()
    invalid_mask = False

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
        networks = set()

        for ip in ips:
            try:
                if not ipv6:
                    # IPv4
                    if route_type == "host":
                        networks.add((ip, "255.255.255.255"))
                    elif route_type == "network":
                        m = mask_ipv4 if mask_ipv4 else "255.255.255.0"
                        try:
                            net = ipaddress.ip_network(f"{ip}/{m}", strict=False)
                            networks.add((str(net.network_address), str(net.netmask)))
                        except ValueError:
                            invalid_mask = True
                            net = ipaddress.ip_network(f"{ip}/24", strict=False)
                            networks.add((str(net.network_address), str(net.netmask)))
                else:
                    # IPv6
                    if route_type == "host":
                        networks.add((ip, "128"))
                    elif route_type == "network":
                        try:
                            net = ipaddress.ip_network(f"{ip}/{prefix_ipv6}", strict=False)
                            networks.add((str(net.network_address), str(net.prefixlen)))
                        except ValueError:
                            invalid_mask = True
                            net = ipaddress.ip_network(f"{ip}/64", strict=False)
                            networks.add((str(net.network_address), str(net.prefixlen)))
            except Exception as e:
                print(f"Ошибка при обработке {domain}: {e}")

        for net_ip, net_mask in networks:
            lines.append(f"route add {net_ip} mask {net_mask} {gateway} :: rem {domain}")
            ips_collected.add(net_ip)

    return "\n".join(lines), ips_collected, invalid_mask

@app.route("/", methods=["GET", "POST"])
def index():
    result_v4, result_v6 = "", ""
    ips_v4, ips_v6 = set(), set()
    domains = ""
    gateway = "0.0.0.0"
    mask_ipv4 = ""
    prefix_ipv6 = 64
    ipv4 = True
    ipv6 = False
    route_type = "host"
    mask_warning = False

    if request.method == "POST":
        domains = request.form.get("domains", "")
        gateway = request.form.get("gateway", "0.0.0.0")
        mask_ipv4 = request.form.get("mask_ipv4", "")
        prefix_ipv6_str = request.form.get("prefix_ipv6", "64")
        try:
            prefix_ipv6 = int(prefix_ipv6_str)
            if not (0 <= prefix_ipv6 <= 128):
                prefix_ipv6 = 64
                mask_warning = True
        except ValueError:
            prefix_ipv6 = 64
            mask_warning = True

        ipv4 = "ipv4" in request.form
        ipv6 = "ipv6" in request.form
        route_type = request.form.get("route_type", "host")
        action = request.form.get("action")

        if ipv4:
            result_v4, ips_v4, invalid_v4 = generate_routes(domains, gateway, mask_ipv4, prefix_ipv6, ipv6=False, route_type=route_type)
            if invalid_v4:
                mask_warning = True
        if ipv6:
            result_v6, ips_v6, invalid_v6 = generate_routes(domains, gateway, mask_ipv4, prefix_ipv6, ipv6=True, route_type=route_type)
            if invalid_v6:
                mask_warning = True

        if mask_warning:
            flash("Некорректная маска/префикс. Используются значения по умолчанию: IPv4 /24, IPv6 /64.", "warning")

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
        mask_ipv4=mask_ipv4,
        prefix_ipv6=prefix_ipv6,
        ipv4=ipv4,
        ipv6=ipv6,
        route_type=route_type
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
