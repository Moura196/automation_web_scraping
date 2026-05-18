#!/usr/bin/env python3
"""CLI to choose a domain and generate a page-object stub and config."""
import json
import os
from pathlib import Path


def prompt_choice(prompt: str, choices: list[str]) -> str:
    for i, c in enumerate(choices, 1):
        print(f"{i}. {c}")
    sel = input(prompt).strip()
    try:
        idx = int(sel)
        if 1 <= idx <= len(choices):
            return choices[idx - 1]
    except Exception:
        pass
    return sel


def main():
    print("Create page object — choose domain")
    choices = ["amazon.com.br", "google.com", "custom"]
    domain = prompt_choice("Select domain (number or enter custom): ", choices)
    if domain == "custom":
        domain = input("Enter custom domain (e.g. example.com): ").strip()

    sample_urls_raw = input(
        "Enter 1-3 sample URLs (comma-separated), or leave blank to fill later: "
    ).strip()
    sample_urls = [u.strip() for u in sample_urls_raw.split(",") if u.strip()]

    default_item = "valores_produtos.items.Produto"
    item_import = input(f"Output item import [{default_item}]: ").strip() or default_item

    default_outdir = "valores_produtos/pages"
    outdir = input(f"Output directory [{default_outdir}]: ").strip() or default_outdir

    cfg = {
        "domain": domain,
        "sample_urls": sample_urls,
        "item_import": item_import,
        "output_dir": outdir,
    }

    # Write config to repository root `page_object_config.json`
    project_root = Path(__file__).resolve().parents[2]
    cfg_path = project_root / "page_object_config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote config to {cfg_path}")

    # Ensure output dir exists
    # Create output directory relative to project root when a relative path is provided
    out_path = Path(outdir)
    if not out_path.is_absolute():
        out_path = project_root / out_path
    out_path.mkdir(parents=True, exist_ok=True)

    # Create a stub page object file
    safe_name = domain.replace(".", "_").replace("/", "_")
    file_path = out_path / f"{safe_name}_page.py"
    if file_path.exists():
        print(f"Page object stub already exists: {file_path}")
        return

    class_name = ''.join(part.capitalize() for part in safe_name.split("_")) + "Page"

    sample_list = "".join(f"    - {u}\n" for u in sample_urls)

    content = f'''from web_poet import WebPage
from {item_import.rsplit('.', 1)[0]} import {item_import.rsplit('.', 1)[1]}


class {class_name}(WebPage):
    """Page object for domain {domain}

    Sample URLs:
{sample_list if sample_list else '    - (none provided)\n'}
    """

    def __init__(self, response):
        self.response = response

    def products(self):
        """Return iterable of `Produto` instances extracted from search results."""
        raise NotImplementedError('Implement extraction logic.')
'''

    file_path.write_text(content, encoding="utf-8")
    print(f"Created page object stub: {file_path}")


if __name__ == '__main__':
    main()
