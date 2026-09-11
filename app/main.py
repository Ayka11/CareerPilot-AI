import sys

# Scheduled runs launch under cmd.exe's default codepage (e.g. cp1251), which
# can't encode the emoji used in collector log output and crashes collectors
# before they return any jobs — starving the job pool down to whichever
# source happens to run first. Force UTF-8 stdout/stderr regardless of the
# console's codepage.
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from agents.core.orchestrator import CareerPilotAgent

def main():
    agent = CareerPilotAgent()
    agent.run_daily(top_n=15)

if __name__ == '__main__':
    main()
