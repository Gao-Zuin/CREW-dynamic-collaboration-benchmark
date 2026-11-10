"""Export the source changes from the CREW workspace into this small Git repo."""
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent / 'CREW'
OVERLAY = HERE / 'overlays'
ROOT_COPY = HERE / 'workspace'
TEXT_SUFFIXES = {'.md', '.py', '.json', '.jsonl'}


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args]).decode().strip()


def changed_paths(repo):
    modified = git(repo, 'diff', '--name-only', '--diff-filter=ACMRT').splitlines()
    untracked = git(repo, 'ls-files', '--others', '--exclude-standard').splitlines()
    return sorted(set(modified + untracked))


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main():
    for path in (OVERLAY, ROOT_COPY):
        if path.exists():
            shutil.rmtree(path)
    copied = []
    upstream = {}
    for name in ('ORCH', 'WILDFIRE-ORCH', 'CREW-Wildfire', 'CREW-base'):
        repo = WORKSPACE / name
        upstream[name] = {'base_commit': git(repo, 'rev-parse', 'HEAD'),
                          'origin': git(repo, 'remote', 'get-url', 'origin')}
        if name not in ('ORCH', 'WILDFIRE-ORCH'):
            continue
        for relative in changed_paths(repo):
            source = repo / relative
            if not source.is_file() or '__pycache__' in source.parts or source.suffix == '.pyc':
                continue
            target = OVERLAY / name / relative
            copy(source, target)
            copied.append(target)
    for name in ('ARCHITECTURE_NOTES.zh-CN.md', 'HYPERGRAPH_ADAPTATION.md',
                 'HYPERGRAPH_RESULTS.md', 'README.zh-CN.md',
                 'RESEARCH_MATURITY_REVIEW.md', 'SMOKE_TEST_REPORT.md', 'VERSIONS.txt'):
        source = WORKSPACE / name
        if source.exists():
            target = ROOT_COPY / name
            copy(source, target)
            copied.append(target)
    for folder, allowed in (('scripts', {'.py', '.sh', '.c'}),
                            ('tests', {'.py'}),
                            ('research', TEXT_SUFFIXES)):
        for source in (WORKSPACE / folder).rglob('*'):
            if (not source.is_file() or source.suffix not in allowed
                    or '__pycache__' in source.parts or source.stat().st_size > 2_000_000
                    or 'papers' in source.parts or 'orch_paper' in source.parts):
                continue
            target = ROOT_COPY / source.relative_to(WORKSPACE)
            copy(source, target)
            copied.append(target)
    evidence = (
        'benchmark_runs/composite_manager_audit_20261106/summary.json',
        'benchmark_runs/composite_spawn_audit_20261106/travel_summary.json',
        'benchmark_runs/composite_matrix_physical_gate_20261106/summary.json',
        'benchmark_runs/structure_matrix_physical_gate_20261106/summary.json',
        'benchmark_runs/unity_travel_probe_20261106/summary.json',
        'benchmark_runs/unity_travel_probe_20261106/seed42/travel.json',
        'benchmark_runs/unity_travel_probe_20261106/seed503/travel.json',
        'benchmark_runs/commitment_event_deepseek_v4_flash_corrected_seed42_20261110/events.jsonl.gz',
        'benchmark_runs/commitment_event_deepseek_v4_flash_corrected_seed42_20261110/commitment_event_analysis.json',
    )
    for name in evidence:
        source = WORKSPACE / name
        if source.exists():
            target = ROOT_COPY / name
            copy(source, target)
            copied.append(target)
    license_path = HERE / 'LICENSE.upstream-ORCH'
    copy(WORKSPACE / 'ORCH/LICENSE', license_path)
    copied.append(license_path)
    manifest = {'upstream': upstream,
                'files': {str(path.relative_to(HERE)): sha256(path.read_bytes()).hexdigest()
                          for path in sorted(copied)}}
    (HERE / 'SOURCE_MANIFEST.json').write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(f'Exported {len(copied)} files; {sum(p.stat().st_size for p in copied) / 1e6:.2f} MB')


if __name__ == '__main__':
    main()
