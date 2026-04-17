"""Flask fixture target: deliberately small, *intentionally* vulnerable, used only by tests."""
from __future__ import annotations

from flask import Flask, request, abort


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/echo")
    def echo():
        return {"q": request.args.get("q", "")}

    @app.get("/search")
    def search():
        # DELIBERATELY UNSAFE: unescaped reflection for XSS fixture.
        q = request.args.get("q", "")
        return f"<html><body>You searched for: {q}</body></html>", 200, {"Content-Type": "text/html"}

    @app.post("/login")
    def login():
        user = request.form.get("user", "")
        pwd = request.form.get("pass", "")
        if user == "admin" and pwd == "hunter2":
            return f"<html><body>Welcome, {user}</body></html>"
        abort(401)

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5055, debug=False)
