import shutil
import subprocess
from pathlib import Path


class LatexService:
    def __init__(self, compiler: str = "tectonic"):
        self.compiler = compiler

    def compile(self, tex_path: Path) -> Path | None:
        pdf_path = tex_path.with_suffix(".pdf")
        compile_log = tex_path.with_name("compile_log.txt")
        if shutil.which(self.compiler) is None:
            compile_log.write_text(
                f"Compiler not found: {self.compiler}\n", encoding="utf-8"
            )
            return None
        if self.compiler == "latexmk":
            command = ["latexmk", "-pdf", "-interaction=nonstopmode", str(tex_path.name)]
        else:
            command = [self.compiler, str(tex_path.name)]
        result = subprocess.run(
            command,
            cwd=tex_path.parent,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode != 0 or not pdf_path.exists():
            compile_log.write_text(
                result.stdout + "\n" + result.stderr, encoding="utf-8"
            )
            return None
        compile_log.write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
        return pdf_path
