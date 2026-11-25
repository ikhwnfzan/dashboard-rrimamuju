from pathlib import Path
import os
import subprocess
import sys

from rjsmin import jsmin


ROOT = Path(__file__).resolve().parent
SOURCES = (
    ROOT / "static" / "js" / "landing.js",
    ROOT / "static" / "js" / "dashboard.js",
)


def build_js():
    for source_path in SOURCES:
        output_path = source_path.with_name(f"{source_path.stem}.min{source_path.suffix}")
        source = source_path.read_text(encoding="utf-8")
        output_path.write_text(jsmin(source) + "\n", encoding="utf-8", newline="\n")


def build_css():
    input_css = ROOT / "static" / "css" / "input.css"
    output_css = ROOT / "static" / "css" / "app.css"
    config_js = ROOT / "tailwind.config.js"
    if not input_css.exists() or not config_js.exists():
        return
    env = os.environ.copy()
    env.setdefault("TAILWINDCSS_VERSION", "v3.4.17")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pytailwindcss",
            "-c",
            str(config_js),
            "-i",
            str(input_css),
            "-o",
            str(output_css),
            "--minify",
        ],
        cwd=str(ROOT),
        env=env,
        check=True,
    )


def main():
    build_js()
    build_css()


if __name__ == "__main__":
    main()
