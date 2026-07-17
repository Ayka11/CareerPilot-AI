from rich import print
from agents.core.orchestrator import CareerPilotAgent

def main():
    agent = CareerPilotAgent()
    agent.run_daily(top_n=5)

if __name__ == '__main__':
    main()
