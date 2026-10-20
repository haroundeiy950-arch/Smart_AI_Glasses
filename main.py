"""Main entry point."""
from __future__ import annotations
import argparse,getpass,json,sys
from config import PROJECT_NAME,ensure_project_folders
from control_system import SystemController
from logger import configure_logging,get_logger
from ui import LoginWindow
log=get_logger(__name__)

def parser():
    p=argparse.ArgumentParser(description=PROJECT_NAME); p.add_argument('--health',action='store_true'); p.add_argument('--full-health',action='store_true'); p.add_argument('--create-user',action='store_true'); return p

def main()->int:
    ensure_project_folders(); configure_logging(); args=parser().parse_args()
    try:
        controller=SystemController()
        if args.health or args.full_health: print(json.dumps(controller.health_check(quick=not args.full_health),ensure_ascii=False,indent=2)); return 0
        if args.create_user:
            uid=controller.security.create_user(input('Username: '),getpass.getpass('Password: '),input('Full name: '),input('Role [user]: ') or 'user'); print('Created user',uid); return 0
        LoginWindow(controller).run(); return 0
    except Exception as exc: log.exception('Startup failed'); print(f"{PROJECT_NAME} could not start: {exc}",file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
