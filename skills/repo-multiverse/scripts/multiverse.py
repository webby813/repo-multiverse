#!/usr/bin/env python3
"""repo-multiverse helper: live sessions, registrations, sacred timeline holder, timeline, scope check, combine lock.

Reads ~/.claude/sessions and git. Writes only ~/.claude/multiverse/<repo-key>/, never inside the repo.
Run with --help for subcommands.
"""
import argparse
import datetime
import fnmatch
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

SESS_DIR = os.path.expanduser('~/.claude/sessions')
STATE_HOME = os.environ.get('MULTIVERSE_HOME') or os.path.expanduser('~/.claude/multiverse')


def git(*args, cwd=None, check=True):
    r = subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f'git {" ".join(args)} failed: {r.stderr.strip()}')
    return r.stdout.rstrip()


def repo_key():
    common = git('rev-parse', '--path-format=absolute', '--git-common-dir')
    root = os.path.dirname(common) if os.path.basename(common) == '.git' else common
    return re.sub(r'[^A-Za-z0-9]', '-', root)


def mv_dir():
    d = os.environ.get('MULTIVERSE_DIR') or os.path.join(STATE_HOME, repo_key())
    os.makedirs(os.path.join(d, 'sessions'), exist_ok=True)
    return d


def load_json(path, default=None):
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def config():
    return load_json(os.path.join(mv_dir(), 'config.json'), {})


def worktrees():
    out, cur = [], {}
    for line in git('worktree', 'list', '--porcelain').splitlines() + ['']:
        if not line:
            if cur:
                out.append(cur)
            cur = {}
            continue
        key, _, val = line.partition(' ')
        if key == 'worktree':
            cur['path'] = val
        elif key == 'branch':
            cur['branch'] = val.removeprefix('refs/heads/')
        elif key in ('detached', 'prunable', 'locked'):
            cur[key] = val or True
        elif key == 'HEAD':
            cur['head'] = val[:7]
    return out


def main_path():
    return worktrees()[0]['path']


def alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False
    except (PermissionError, ValueError, TypeError):
        return True


def live_sessions():
    out = []
    for f in glob.glob(os.path.join(SESS_DIR, '*.json')):
        s = load_json(f)
        if s and alive(s.get('pid')):
            out.append(s)
    return out


def my_session():
    pid = os.environ.get('CLAUDE_PID')
    candidates = [pid] if pid else []
    p = os.getppid()
    for _ in range(8):
        candidates.append(str(p))
        r = subprocess.run(['ps', '-o', 'ppid=', '-p', str(p)], capture_output=True, text=True)
        if not r.stdout.strip():
            break
        p = int(r.stdout.strip())
    for c in candidates:
        s = load_json(os.path.join(SESS_DIR, f'{c}.json'))
        if s:
            return s
    sys.exit('cannot find this session in ~/.claude/sessions (run inside a Claude Code session)')


def registrations():
    regs = {}
    for f in sorted(glob.glob(os.path.join(mv_dir(), 'sessions', '*.json'))):
        r = load_json(f)
        if r:
            regs[r['name']] = r
    return regs


def reg_path(name):
    return os.path.join(mv_dir(), 'sessions', f'{name}.json')


def sacred_path():
    return os.path.join(mv_dir(), 'sacred.json')


def sacred_holder():
    """(record, live) of the session holding the sacred timeline; (None, False) when nobody does."""
    h = load_json(sacred_path())
    if not h:
        return None, False
    return h, h.get('name') in {s.get('name') for s in live_sessions()}


def sacred_text():
    h, live = sacred_holder()
    if not h:
        return 'nobody (/loki-sacred)'
    return h['name'] + ('' if live else ' (gone; /loki-sacred takes over)')


def integration():
    b = config().get('integration_branch')
    if not b:
        sys.exit('no integration_branch: run /repo-multiverse init first')
    return b


def ahead_behind(base, branch):
    out = git('rev-list', '--left-right', '--count', f'{base}...{branch}', check=False)
    try:
        behind, ahead = (int(x) for x in out.split())
        return ahead, behind
    except ValueError:
        return None, None


def branch_exists(b):
    return subprocess.run(['git', 'show-ref', '--verify', '--quiet', f'refs/heads/{b}']).returncode == 0


def ago(ms):
    if not ms:
        return '-'
    s = time.time() - ms / 1000
    for unit, n in (('d', 86400), ('h', 3600), ('m', 60)):
        if s >= n:
            return f'{int(s // n)}{unit}'
    return 'now'


def in_repo(path, wt_paths):
    return any(path == w or path.startswith(w + os.sep) for w in wt_paths)


def ordered_branches():
    regs = registrations()
    gks = sorted(n for n, r in regs.items() if r.get('role') == 'gatekeeper')
    rows, n = [], 0
    for gk in gks:
        items = [(gk, b) for b in regs[gk].get('branches', [])]
        for wn, wr in sorted(regs.items()):
            if wr.get('role') == 'worker' and wr.get('gatekeeper') == gk:
                items += [(wn, b) for b in wr.get('branches', [])]
        for owner, b in items:
            n += 1
            rows.append((n, gk, owner, b))
    return rows


def cmd_where(a):
    d = mv_dir()
    print(f"state {d}\nconfig {os.path.join(d, 'config.json')} "
          f"({'present' if os.path.exists(os.path.join(d, 'config.json')) else 'missing'})")


def cmd_whoami(a):
    s = my_session()
    reg = registrations().get(s.get('name'))
    h, _ = sacred_holder()
    print(f"{s.get('name')}  pid {s.get('pid')}  session {s.get('sessionId', '')[:8]}  "
          f"role {reg.get('role') if reg else '(not joined)'}  "
          f"sacred {'yes' if h and h.get('name') == s.get('name') else 'no'}")


def cmd_sessions(a):
    wts = [w['path'] for w in worktrees()]
    me = my_session().get('name')
    regs = registrations()
    live = [s for s in live_sessions() if a.all or in_repo(s.get('cwd', ''), wts)]
    live_names = {s.get('name') for s in live_sessions()}
    cfg = config()
    tip = git('rev-parse', '--short', cfg['integration_branch'], check=False) if cfg.get('integration_branch') else ''
    print(f"repo {os.path.basename(main_path())}  integration {cfg.get('integration_branch', '(not set)')} {tip}")
    print(f"sacred timeline held by {sacred_text()}")
    print(f"{'NAME':28} {'KIND':5} {'STATUS':6} {'IDLE':5} {'ROLE':10} {'GATEKEEPER':20} STORY / BRANCHES")
    for s in sorted(live, key=lambda s: s.get('name', '')):
        n = s.get('name', '?')
        r = regs.get(n, {})
        brs = ','.join(b['name'].split('/')[-1] for b in r.get('branches', []))
        print(f"{(n + (' *' if n == me else ''))[:28]:28} {s.get('kind', '')[:5]:5} {s.get('status', '')[:6]:6} "
              f"{ago(s.get('statusUpdatedAt')):5} {r.get('role', '-'):10} {(r.get('gatekeeper') or '-')[:20]:20} "
              f"{r.get('story', '(not joined)')}{' / ' + brs if brs else ''}")
    stale = [n for n in regs if n not in live_names]
    if stale:
        print('stale registrations (session gone): ' + ', '.join(stale))


def cmd_join(a):
    s = my_session()
    name = s['name']
    cfg = config()
    if a.sim and a.sim in cfg.get('protected_devices', []):
        sys.exit(f'{a.sim} is a protected device (the user\'s); pick your own simulator')
    if a.role == 'worker' and not a.gatekeeper:
        sys.exit('a worker needs --gatekeeper <session name>')
    path = reg_path(name)
    r = load_json(path, {}) or {}
    r.update({k: v for k, v in {
        'name': name, 'pid': s.get('pid'), 'session': s.get('sessionId'),
        'role': a.role, 'story': a.story, 'gatekeeper': a.gatekeeper,
        'sim': a.sim, 'owns': a.owns or None}.items() if v is not None})
    r.setdefault('branches', [])
    r['updated'] = datetime.datetime.now().isoformat(timespec='seconds')
    save_json(path, r)
    print(json.dumps(r, ensure_ascii=False, indent=2))


def cmd_branch(a):
    name = my_session()['name']
    path = reg_path(name)
    r = load_json(path)
    if not r:
        sys.exit('join first (/loki-join)')
    brs = r.setdefault('branches', [])
    cur = next((b for b in brs if b['name'] == a.branch), None)
    if a.action == 'add':
        if not branch_exists(a.branch):
            sys.exit(f'no local branch {a.branch}')
        if cur is None:
            cur = {'name': a.branch}
            brs.append(cur)
        wt = next((w['path'] for w in worktrees() if w.get('branch') == a.branch), None)
        cur.update({'worktree': a.worktree or wt, 'status': a.status or cur.get('status', 'working')})
        if a.note:
            cur['note'] = a.note
    elif a.action == 'status':
        if cur is None:
            sys.exit(f'{a.branch} is not registered by {name}')
        cur['status'] = a.status
        if a.note:
            cur['note'] = a.note
    elif a.action == 'remove':
        r['branches'] = [b for b in brs if b['name'] != a.branch]
    r['updated'] = datetime.datetime.now().isoformat(timespec='seconds')
    save_json(path, r)
    print(f"{name}: {a.action} {a.branch}")


def cmd_leave(a):
    name = my_session()['name']
    path = reg_path(name)
    if os.path.exists(path):
        os.remove(path)
    print('left')
    h, _ = sacred_holder()
    if h and h.get('name') == name:
        print('still holding the sacred timeline: `sacred release` to step down')


def cmd_sacred(a):
    integ = integration()
    h, live = sacred_holder()
    if a.action == 'status':
        print(f'sacred timeline {integ} held by {sacred_text()}' + (f"  since {h['since']}" if h else ''))
        return
    me = my_session()
    name = me['name']
    mine = bool(h) and h.get('name') == name
    combining = load_json(os.path.join(lock_path(), 'owner.json'))
    if a.action == 'release':
        if not mine:
            sys.exit(f'{name} does not hold the sacred timeline (held by {sacred_text()})')
        if combining and combining.get('name') == name:
            sys.exit('a combine of yours holds the lock: finish it and `lock release` first')
        os.remove(sacred_path())
        print(f'{name} released the sacred timeline {integ}; nobody holds it now')
        return
    tip = git('rev-parse', '--verify', '--quiet', '--short', integ, check=False)
    if not tip:
        sys.exit(f'no local branch {integ}: check integration_branch in config.json')
    if mine:
        print(f"{name} already holds the sacred timeline {integ} @ {tip} (since {h['since']})")
        return
    if h and live and not a.takeover:
        print(f"HELD: {h['name']} holds the sacred timeline since {h['since']} and is live. "
              "Take over only with the user's approval: --takeover")
        sys.exit(5)
    if combining and alive(combining.get('pid')) and combining.get('name') != name:
        print(f"BUSY: {combining['name']} is combining since {combining['time']}; claim after it finishes")
        sys.exit(5)
    save_json(sacred_path(), {
        'name': name, 'pid': me.get('pid'), 'session': me.get('sessionId'),
        'since': datetime.datetime.now().isoformat(timespec='seconds'),
        'previous': h.get('name') if h else None})
    prev = f"; took over from {h['name']}{'' if live else ' (gone)'}" if h else ''
    print(f'{name} now holds the sacred timeline {integ} @ {tip}{prev}')


def cmd_timeline(a):
    integ = integration()
    tip = git('rev-parse', '--short', integ)
    up = git('rev-parse', '--abbrev-ref', f'{integ}@{{upstream}}', check=False)
    unpushed = ''
    if up:
        ah, _ = ahead_behind(up, integ)
        unpushed = f'  ({ah} unpushed vs {up})' if ah else '  (pushed)'
    live = {s.get('name'): s for s in live_sessions()}
    regs = registrations()
    wt_by_branch = {w.get('branch'): w for w in worktrees() if w.get('branch')}
    print(f'sacred timeline  {integ} @ {tip}{unpushed}  · held by {sacred_text()}')
    rows = ordered_branches()
    claimed = set()
    gks = sorted(n for n, r in regs.items() if r.get('role') == 'gatekeeper')
    for gi, gk in enumerate(gks):
        r = regs[gk]
        st = live.get(gk, {}).get('status', 'gone')
        last_gk = gi == len(gks) - 1
        print(f"{'└─' if last_gk else '├─'} {gk}  [gatekeeper · {r.get('story', '')} · {st}]")
        mine = [x for x in rows if x[1] == gk]
        if not mine:
            print(f"{'   ' if last_gk else '│  '}└─ (no branches)")
        for i, (n, _, owner, b) in enumerate(mine):
            claimed.add(b['name'])
            ah, be = ahead_behind(integ, b['name']) if branch_exists(b['name']) else (None, None)
            state = 'missing' if ah is None else ('merged' if ah == 0 else f'+{ah}/-{be}')
            wt = wt_by_branch.get(b['name'])
            wtx = '' if not wt else ('  wt prunable' if wt.get('prunable') else f"  wt {os.path.basename(wt['path'])}")
            who = '' if owner == gk else f"  worker {owner}({live.get(owner, {}).get('status', 'gone')})"
            print(f"{'   ' if last_gk else '│  '}{'└─' if i == len(mine) - 1 else '├─'} {n} {b['name']}  "
                  f"{state}  {b.get('status', '')}{wtx}{who}")
    loose = [w for w in worktrees()[1:] if w.get('branch') not in claimed]
    cutoff = time.time() - a.days * 86400
    refs = git('for-each-ref', '--sort=-committerdate', '--format=%(refname:short) %(committerdate:unix)', 'refs/heads')
    recent = []
    for line in refs.splitlines():
        b, _, t = line.rpartition(' ')
        if b in claimed or b == integ or int(t) < cutoff or b in {w.get('branch') for w in loose}:
            continue
        ah, _ = ahead_behind(integ, b)
        if ah:
            recent.append((b, ah))
    if loose or recent:
        print('unclaimed (no gatekeeper):')
        for w in loose:
            b = w.get('branch') or f"detached {w.get('head')}"
            ah, be = ahead_behind(integ, w['branch']) if w.get('branch') else (None, None)
            state = '' if ah is None else ('merged' if ah == 0 else f'+{ah}/-{be}')
            print(f"   - {b}  {state}  wt {w['path']}{'  prunable' if w.get('prunable') else ''}")
        for b, ah in recent[:10]:
            print(f'   - {b}  +{ah} (no worktree)')


def resolve(tokens):
    rows = {str(n): b['name'] for n, _, _, b in ordered_branches()}
    return [rows.get(t, t) for t in tokens]


def cmd_resolve(a):
    for t, b in zip(a.items, resolve(a.items)):
        print(f'{t} -> {b}{"" if branch_exists(b) else "  (no such branch)"}')


def changed(integ, b):
    return set(git('diff', '--name-only', f'{integ}...{b}', check=False).splitlines())


def cmd_nexus(a):
    integ = integration()
    cfg = config()
    cands = resolve(a.branches)
    regs = registrations()
    owner_of = {b['name']: r for r in regs.values() for b in r.get('branches', [])}
    files = {b: changed(integ, b) for b in cands}
    others = {}
    for r in regs.values():
        for b in r.get('branches', []):
            if b['name'] not in cands and branch_exists(b['name']) and ahead_behind(integ, b['name'])[0]:
                others[b['name']] = changed(integ, b['name'])
    dirty = set()
    for line in git('status', '--porcelain', cwd=main_path()).splitlines():
        dirty.add(line[3:].split(' -> ')[-1].strip('"'))
    blockers = 0
    for b in cands:
        fs = files[b]
        r = owner_of.get(b, {})
        owns = r.get('owns') or []
        print(f'== {b}  ({len(fs)} files, owner {r.get("name", "unregistered")})')
        if owns:
            out = sorted(f for f in fs if not any(fnmatch.fnmatch(f, g) for g in owns))
            if out:
                print('  outside owned paths: ' + ', '.join(out[:15]) + (' …' if len(out) > 15 else ''))
        for pat, rule in cfg.get('shared_files', {}).items():
            hit = sorted(f for f in fs if fnmatch.fnmatch(f, pat))
            if hit:
                print(f'  shared file {pat} ({len(hit)}): {rule}')
        for ob, ofs in others.items():
            both = sorted(fs & ofs)
            if both:
                print(f'  overlaps active branch {ob}: ' + ', '.join(both[:10]))
        for ob in cands:
            if ob != b and (fs & files[ob]):
                print(f'  overlaps candidate {ob}: ' + ', '.join(sorted(fs & files[ob])[:10]))
        d = sorted(fs & dirty)
        if d:
            blockers += 1
            print('  BLOCKER uncommitted in main folder: ' + ', '.join(d))
    sys.exit(3 if blockers else 0)


def lock_path():
    return os.path.join(mv_dir(), 'combine.lock')


def cmd_lock(a):
    lp = lock_path()
    owner = load_json(os.path.join(lp, 'owner.json'))
    if a.action == 'status':
        print(f"held by {owner['name']} since {owner['time']}" if owner else 'free')
        return
    me = my_session()
    if a.action == 'acquire':
        h, live = sacred_holder()
        if not h or h.get('name') != me['name']:
            print(f"NOT SACRED: only the sacred timeline holder combines; held by {sacred_text()}")
            sys.exit(6)
        try:
            os.mkdir(lp)
        except FileExistsError:
            if owner and alive(owner.get('pid')) and owner.get('name') != me['name']:
                print(f"BUSY: held by {owner['name']} since {owner['time']}")
                sys.exit(5)
        save_json(os.path.join(lp, 'owner.json'), {
            'name': me['name'], 'pid': me['pid'],
            'time': datetime.datetime.now().isoformat(timespec='seconds')})
        print(f"acquired by {me['name']}")
    elif a.action == 'release':
        if owner and owner.get('name') != me['name'] and not a.force:
            sys.exit(f"held by {owner['name']}, not you")
        shutil.rmtree(lp, ignore_errors=True)
        print('released')


def cmd_preflight(a):
    integ = integration()
    cfg = config()
    mp = main_path()
    holders = [w['path'] for w in worktrees() if w.get('branch') == integ]
    print(f'integration {integ} @ {git("rev-parse", "--short", integ)} checked out in: {holders or "nowhere"}')
    if holders and holders != [mp]:
        print('  WARNING: held by a worktree other than the main folder')
    owner = load_json(os.path.join(lock_path(), 'owner.json'))
    print(f"combine lock: {('held by ' + owner['name']) if owner else 'free'}")
    for rel in cfg.get('extra_locks', []):
        p = os.path.join(mp, rel)
        print(f"extra lock {rel}: {'PRESENT' if os.path.exists(p) else 'free'}")
    dirty = git('status', '--porcelain', cwd=mp).splitlines()
    print(f'main folder uncommitted: {len(dirty)}')
    for line in dirty[:20]:
        print('  ' + line)


def cmd_prune_plan(a):
    integ = integration()
    live_ids = {s.get('sessionId') for s in live_sessions()}
    live_names = {s.get('name') for s in live_sessions()}
    owner = {b['name']: n for n, r in registrations().items() for b in r.get('branches', [])}
    print('# nothing is deleted by this command; run the lines you agree with')
    gone = [w['path'] for w in worktrees()[1:] if w.get('prunable')]
    if gone:
        print(f"git worktree prune   # {len(gone)} worktree folders no longer exist: " +
              ', '.join(os.path.basename(p) for p in gone))
    for w in worktrees()[1:]:
        if w.get('prunable'):
            continue
        o = owner.get(w.get('branch'))
        if o in live_names:
            print(f"# keep '{w['path']}'   # {w['branch']} belongs to live session {o}")
        elif w.get('detached'):
            print(f"git worktree remove '{w['path']}'   # detached (temp combine?)")
        elif w.get('branch') and ahead_behind(integ, w['branch'])[0] == 0:
            dirty = git('status', '--porcelain', cwd=w['path'], check=False)
            note = '  # DIRTY, ask the owner first' if dirty else ''
            print(f"git worktree remove '{w['path']}'   # {w['branch']} merged{note}")
    for n in registrations():
        if n not in live_names:
            print(f"rm '{reg_path(n)}'   # registration of gone session {n}")
    if a.scratch:
        uid = os.getuid()
        slug = main_path().replace('/', '-').replace('_', '-')
        for d in sorted(glob.glob(f'/private/tmp/claude-{uid}/{slug}/*/')):
            sid = os.path.basename(d.rstrip('/'))
            if sid not in live_ids:
                size = subprocess.run(['du', '-sh', d], capture_output=True, text=True).stdout.split('\t')[0]
                print(f"rm -rf '{d}'   # scratch of ended session, {size}")


def main():
    p = argparse.ArgumentParser(prog='multiverse.py', description=__doc__)
    sp = p.add_subparsers(dest='cmd', required=True)
    sp.add_parser('where').set_defaults(f=cmd_where)
    sp.add_parser('whoami').set_defaults(f=cmd_whoami)
    s = sp.add_parser('sessions')
    s.add_argument('--all', action='store_true', help='all live sessions on this machine')
    s.set_defaults(f=cmd_sessions)
    s = sp.add_parser('join')
    s.add_argument('--role', choices=['gatekeeper', 'worker'], required=True)
    s.add_argument('--story', required=True)
    s.add_argument('--gatekeeper')
    s.add_argument('--sim')
    s.add_argument('--owns', action='append', help='glob of paths this session owns (repeatable)')
    s.set_defaults(f=cmd_join)
    s = sp.add_parser('branch')
    s.add_argument('action', choices=['add', 'status', 'remove'])
    s.add_argument('branch')
    s.add_argument('--worktree')
    s.add_argument('--status', choices=['working', 'ready', 'blocked', 'merged'])
    s.add_argument('--note')
    s.set_defaults(f=cmd_branch)
    sp.add_parser('leave').set_defaults(f=cmd_leave)
    s = sp.add_parser('sacred', help='the one session that combines into the integration branch')
    s.add_argument('action', nargs='?', default='status', choices=['status', 'claim', 'release'])
    s.add_argument('--takeover', action='store_true', help='claim from a live holder (user approval only)')
    s.set_defaults(f=cmd_sacred)
    s = sp.add_parser('timeline')
    s.add_argument('--days', type=int, default=14, help='unclaimed branches committed within N days')
    s.set_defaults(f=cmd_timeline)
    s = sp.add_parser('resolve')
    s.add_argument('items', nargs='+', help='timeline numbers or branch names')
    s.set_defaults(f=cmd_resolve)
    s = sp.add_parser('nexus')
    s.add_argument('branches', nargs='+', help='timeline numbers or branch names')
    s.set_defaults(f=cmd_nexus)
    s = sp.add_parser('lock')
    s.add_argument('action', choices=['acquire', 'release', 'status'])
    s.add_argument('--force', action='store_true')
    s.set_defaults(f=cmd_lock)
    sp.add_parser('preflight').set_defaults(f=cmd_preflight)
    s = sp.add_parser('prune-plan')
    s.add_argument('--scratch', action='store_true', help='also list scratch dirs of ended sessions')
    s.set_defaults(f=cmd_prune_plan)
    a = p.parse_args()
    a.f(a)


if __name__ == '__main__':
    main()
