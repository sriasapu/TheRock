# Copyright Advanced Micro Devices, Inc.
# SPDX-License-Identifier: MIT

import argparse
import logging
import os
import shlex
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO)

DEFAULT_SKIP_BENCHMARKS_FILE = Path(__file__).with_name(
    "hecbench_spirv_skipped_benchmarks.txt"
)


def load_skipped_benchmarks(skip_file: Path) -> set[str]:
    if not skip_file.is_file():
        raise RuntimeError(f"Skip benchmarks file not found: {skip_file}")

    skipped_benchmarks = set()
    with open(skip_file, "r") as f:
        for raw_line in f:
            entry = raw_line.split("#", 1)[0].strip()
            if entry:
                skipped_benchmarks.add(entry)
    return skipped_benchmarks


def run_cmd(
    cmd: list[str], cwd: Path, env: dict[str, str]
) -> subprocess.CompletedProcess:
    logging.info(f"++ Exec [{cwd}]$ {shlex.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )


def patch_makefile(makefile_path: Path, rocm_path: Path, hipcc_cmd: str) -> None:
    with open(makefile_path, "r") as f:
        content = f.read()

    new_lines = []
    for line in content.splitlines():
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]  # preserve tabs/spaces
        # Change-0: Force compiler driver to hipcc.
        if stripped.startswith("CC") and "=" in stripped:
            line = indent + f"CC = {hipcc_cmd}"
            new_lines.append(line)
            continue

        # Change-1: Update CFLAGS line
        if stripped.startswith("CFLAGS :="):
            # Insert HIP flags right after $(EXTRA_CFLAGS), keep rest intact
            if "$(EXTRA_CFLAGS)" in stripped and "-x hip" not in stripped:
                parts = stripped.split("$(EXTRA_CFLAGS)", 1)
                stripped = f"CFLAGS := $(EXTRA_CFLAGS) -x hip --offload-arch=amdgcnspirv{parts[1]}"
            line = indent + stripped

        # Change-2: Update LDFLAGS line
        elif stripped.startswith("LDFLAGS"):
            line = indent + "LDFLAGS := --hip-link --offload-arch=amdgcnspirv " + stripped.split('=',1)[-1]

        # Change-3: Update link rule (remove CFLAGS)
        elif "$(CC) $(CFLAGS) " in stripped and stripped.endswith(" $(LDFLAGS)"):
            line = indent + "$(CC) $(obj) -o $@ $(LDFLAGS)"

        elif "$(CC)" in stripped and "$(CFLAGS)" in stripped and "-c" in stripped:
            tokens = stripped.split()

            # Remove all occurrences of $(CFLAGS)
            tokens = [token for token in tokens if token != "$(CFLAGS)"]

            # Ensure $(CFLAGS) is inserted immediately after $(CC)
            if tokens[0] == "$(CC)":
                tokens.insert(1, "$(CFLAGS)")

            # Rebuild the line
            stripped = " ".join(tokens)
            line = indent + stripped

        new_lines.append(line)

    content = "\n".join(new_lines)

    with open(makefile_path, "w") as f:
        f.write(content)


def pick_first_existing_path(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate and candidate.is_file():
            return candidate
    return None


def is_clangxx(path: Path | None) -> bool:
    return bool(path) and "clang++" in path.name


def has_hip_runtime(root: Path) -> bool:
    return (root / "include" / "hip" / "hip_runtime.h").is_file()


def pick_hip_runtime_root(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        if candidate and has_hip_runtime(candidate):
            return candidate
    return None


def select_bench_dirs(
    src_dir: Path, skipped_benchmarks: set[str]
) -> tuple[list[Path], list[str]]:
    bench_dirs = sorted(
        bench
        for bench in src_dir.iterdir()
        if bench.is_dir() and bench.name.endswith("-hip")
    )
    if not bench_dirs:
        raise RuntimeError(f"No *-hip benchmark directories found in {src_dir}")

    selected_bench_dirs = [
        bench for bench in bench_dirs if bench.name not in skipped_benchmarks
    ]
    skipped_present = [
        bench.name for bench in bench_dirs if bench.name in skipped_benchmarks
    ]

    if not selected_bench_dirs:
        raise RuntimeError(
            f"All discovered *-hip benchmark directories are skipped in {src_dir}"
        )

    return selected_bench_dirs, skipped_present


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--rocm-path", type=Path, required=True)
    parser.add_argument("--cxx-compiler", type=Path, default=None)
    parser.add_argument("--hipcc", type=Path, default=None)
    parser.add_argument(
        "--skip-benchmarks-file",
        type=Path,
        default=DEFAULT_SKIP_BENCHMARKS_FILE,
        help="Path to newline-separated benchmark names to skip",
    )
    args = parser.parse_args()

    if not args.source_dir.is_dir():
        logging.error(f"Source directory not found: {args.source_dir}")
        return 1

    skipped_benchmarks = load_skipped_benchmarks(args.skip_benchmarks_file)
    logging.info(
        f"Loaded {len(skipped_benchmarks)} skipped benchmark(s) from: "
        f"{args.skip_benchmarks_file}",
    )

    src_dir = args.source_dir / "src"
    bench_dirs, skipped_bench_dirs = select_bench_dirs(src_dir, skipped_benchmarks)

    if skipped_bench_dirs:
        logging.info(
            f"Skipping {len(skipped_bench_dirs)} benchmark(s): "
            + ", ".join(skipped_bench_dirs),
        )

    env = dict(os.environ)

    hipcc_candidates = [
        args.hipcc,
        args.rocm_path / "bin" / "hipcc",
        args.rocm_path.parent / "dist" / "rocm" / "bin" / "hipcc",
        args.rocm_path.parent / "core" / "clr" / "dist" / "bin" / "hipcc",
    ]
    selected_hipcc = pick_first_existing_path(hipcc_candidates)
    hipcc_cmd = str(selected_hipcc) if selected_hipcc else "hipcc"

    clang_candidates = [
        args.rocm_path / "lib" / "llvm" / "bin" / "clang++",
        args.rocm_path / "llvm" / "bin" / "clang++",
        args.rocm_path.parent
        / "compiler"
        / "amd-llvm"
        / "dist"
        / "lib"
        / "llvm"
        / "bin"
        / "clang++",
    ]
    if is_clangxx(args.cxx_compiler):
        clang_candidates.append(args.cxx_compiler)
    selected_clang = pick_first_existing_path(clang_candidates)
    if selected_clang:
        env["HIP_CLANG_PATH"] = str(selected_clang.parent)

    runtime_root_candidates = [
        args.rocm_path,
        args.rocm_path.parent / "dist" / "rocm",
        args.rocm_path.parent / "core" / "clr" / "stage",
    ]
    runtime_root = pick_hip_runtime_root(runtime_root_candidates)
    if runtime_root:
        env["ROCM_PATH"] = str(runtime_root)
        env["HIP_PATH"] = str(runtime_root)
    else:
        # Fallback to provided rocm-path if no explicit HIP runtime root is found.
        env["ROCM_PATH"] = str(args.rocm_path)

    if selected_hipcc:
        env["PATH"] = (
            f"{selected_hipcc.parent}{os.pathsep}{env.get('PATH', '')}".rstrip(
                os.pathsep
            )
        )
    logging.info(f"Using hipcc at: {hipcc_cmd}")
    if selected_clang:
        logging.info(f"Using clang++ at: {selected_clang}")
    if runtime_root:
        logging.info(f"Using HIP runtime root: {runtime_root}")
    else:
        logging.warning(
            f"Could not find HIP runtime root, falling back to: {args.rocm_path}"
        )

    failed = 0
    for bench_dir in bench_dirs:
        makefile_path = bench_dir / "Makefile"
        if not makefile_path.is_file():
            failed += 1
            logging.warning(f"Missing Makefile for {bench_dir.name}")
            continue

        patch_makefile(makefile_path, Path(env["ROCM_PATH"]), hipcc_cmd)
        proc = run_cmd(["make", "-j2"], bench_dir, env)
        if proc.returncode != 0:
            failed += 1
            logging.error(f"Build failed for {bench_dir.name}")
            if proc.stderr:
                logging.error(proc.stderr)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

