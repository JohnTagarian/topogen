import json
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


@app.template_filter("thousands")
def thousands_filter(value):
    return "{:,}".format(int(value))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    from llm import parse_requirements, design_topology
    from bom import generate_bom

    user_input = request.form.get("user_input", "").strip()
    if not user_input:
        return render_template("index.html", error="กรุณากรอก requirement ก่อนครับ")

    try:
        parsed_params = parse_requirements(user_input)
        topology = design_topology(parsed_params)
        bom = generate_bom(topology)
    except Exception as e:
        return render_template("result.html", error=str(e))

    return render_template(
        "result.html",
        topology=topology,
        topology_json=json.dumps(topology, ensure_ascii=False),
        bom=bom,
        parsed_params=parsed_params,
        user_input=user_input,
    )


@app.route("/health")
def health():
    from flask import jsonify
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
