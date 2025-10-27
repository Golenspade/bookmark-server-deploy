#!/usr/bin/env python3
#
# Bookmark Server - 支持Heroku部署
# 可以监听配置的端口（通过PORT环境变量）

import os
import http.server
import requests
from urllib.parse import unquote, parse_qs

memory = {}

form = '''<!DOCTYPE html>
<title>Bookmark Server</title>
<form method="POST">
    <label>Long URI:
        <input name="longuri">
    </label>
    <br>
    <label>Short name:
        <input name="shortname">
    </label>
    <br>
    <button type="submit">Save it!</button>
</form>
<p>URIs I know about:
<pre>
{}
</pre>
'''


def CheckURI(uri, timeout=5):
    '''Check whether this URI is reachable, i.e. does it return a 200 OK?'''
    try:
        if requests.get(uri, timeout=timeout).status_code == 200:
            return True
        else:
            return False
    except requests.RequestException:
        return False


class Shortener(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        name = unquote(self.path[1:])

        if name:
            if name in memory:
                self.send_response(303)
                self.send_header('Location', memory[name])
                self.end_headers()
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write("I don't know '{}'.".format(name).encode())
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            known = "\n".join("{} : {}".format(key, memory[key])
                              for key in sorted(memory.keys()))
            self.wfile.write(form.format(known).encode())

    def do_POST(self):
        length = int(self.headers.get('Content-length', 0))
        body = self.rfile.read(length).decode()
        params = parse_qs(body)

        if "longuri" not in params or "shortname" not in params:
            self.send_response(400)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("Missing form fields!".encode())
            return

        longuri = params["longuri"][0]
        shortname = params["shortname"][0]

        if CheckURI(longuri):
            memory[shortname] = longuri
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write("Couldn't fetch URI '{}'. Sorry!".format(longuri).encode())
            return

if __name__ == '__main__':
    # 支持PORT环境变量（Heroku需要）
    # 如果没有PORT，默认使用8000（本地开发）
    port = int(os.environ.get('PORT', 8000))
    
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, Shortener)
    
    print("=" * 50)
    print("📡 书签服务器启动!")
    print("=" * 50)
    print(f"🌐 监听端口: {port}")
    print(f"📝 访问: http://localhost:{port}")
    print(f"⏹️  停止: Ctrl+C")
    print("=" * 50)
    
    httpd.serve_forever()
